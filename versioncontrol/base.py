"""
Generic API access implementation for a version control system service.
"""
from abc import ABCMeta, abstractmethod

import json
import requests


def merge_dict(thedict, **kwargs_with_dict_values):
    """
    Update or add dictionary values in a dictionary for specific keys.
    An existing value is _updated_, not replaced (as with ``dict.update()``),
    preserving unaffected parts of the existing dictionary value.  Raises an
    AttributeError if ``thedict[keyword]`` exists but is not a dictionary.
    """
    for key, value in kwargs_with_dict_values.items():
        try:
            thedict[key].update(value)
        except KeyError:
            thedict.update({key: value})
    return thedict


class JSONResponse(requests.Response):
    """A pseudo-response object as alternative to an exception"""

    def __init__(self, reason, status_code=200):
        """A response object that carries a 'reason' text message as JSON"""
        super().__init__()
        self.status_code = status_code
        self.reason = reason
        self._content = bytes(json.dumps({'message': reason}), encoding='UTF-8')


class ServiceRequestsMixin:
    """
    A collection of functions for making HTTP request calls against a REST API
    """

    def __init__(self, base_url, headers, timeout):
        """Just a mixin, initialized in ServiceAPIStrategy constructor"""
        self.base_url = base_url
        self.headers = headers
        self.timeout = timeout

    def url_for_endpoint(self, endpoint, *args):
        """Return the full URL for an API endpoint"""
        # return '/'.join([self.base_url, endpoint, *args])  # Python 3.5 syntax (PEP 448)
        return '/'.join((self.base_url, endpoint) + args)

    def get_json_or_raise(self, endpoint, *args, **kwargs):
        """Make a GET request, ensure it was successful, and return JSON"""
        response = self.get(endpoint, *args, **kwargs)
        response.raise_for_status()
        return response.json()

    def get(self, endpoint, *args, **kwargs):
        """Make a GET request handling authentication and timeout

        Arguments are appended to the endpoint to form the URL path.
        Keyword arguments are passed to the request.
        """
        url = self.url_for_endpoint(endpoint, *args)
        kwargs = merge_dict(kwargs, headers=self.headers)
        return requests.get(url, timeout=self.timeout, **kwargs)

    def post(self, endpoint, *args, **kwargs):
        """Make a POST request handling authentication and timeout

        Arguments are appended to the endpoint to form the URL path.
        Keyword arguments are passed to the request.
        """
        url = self.url_for_endpoint(endpoint, *args)
        kwargs = merge_dict(kwargs, headers=self.headers)
        return requests.post(url, timeout=self.timeout, **kwargs)

    def put(self, endpoint, *args, **kwargs):
        """Make a PUT request handling authentication and timeout

        Arguments are appended to the endpoint to form the URL path.
        Keyword arguments are passed to the request.
        """
        url = self.url_for_endpoint(endpoint, *args)
        kwargs = merge_dict(kwargs, headers=self.headers)
        return requests.put(url, timeout=self.timeout, **kwargs)

    def delete(self, endpoint, *args, **kwargs):
        """Make a DELETE request handling authentication and timeout

        Arguments are appended to the endpoint to form the URL path.
        Keyword arguments are passed to the request.
        """
        url = self.url_for_endpoint(endpoint, *args)
        kwargs = merge_dict(kwargs, headers=self.headers)
        return requests.delete(url, timeout=self.timeout, **kwargs)


class ServiceAPIStrategy(ServiceRequestsMixin, metaclass=ABCMeta):
    """
    Interface for a VCS service API implementation (strategy pattern).
    """
    DEFAULT_TIMEOUT = 30  # seconds
    HTTP400_DELETION_REFUSED = JSONResponse(
        status_code=400, reason="Slug does not match project. Deletion refused.")

    def __init__(self, base_url, oauth_token, headers=None, timeout=DEFAULT_TIMEOUT):
        """
        The behavior of an API of a specific VCS service (strategy pattern).
        """
        if headers is None:
            headers = {}
        headers.update({'Authorization': 'Bearer %s' % oauth_token})
        super().__init__(base_url, headers, timeout)

    @abstractmethod
    def create_project(self, name, slug=None, **kwargs):
        """Create a repository project on the service platform"""

    @abstractmethod
    def update_project(self, key, slug=None, **kwargs):
        """Update a repository project on the service platform"""

    @abstractmethod
    def delete_project(self, key, slug):
        """Safe-delete a repository project on the service platform

        Only when `slug` matches the project with `key` the project is
        deleted, and should return HTTP404_DELETION_REFUSED otherwise.
        """

    @abstractmethod
    def list_projects(self):
        """Get a list of user's projects on the service platform"""

    @abstractmethod
    def project_details(self, key):
        """Get details of a single project on the service platform"""

    @abstractmethod
    def add_deploy_key(self, project_id, key_title, ssh_key, read_only=True):
        """Create a new deploy key for a project on the service platform"""


class ServiceAPI:
    """
    Generic API for a version control system service hosting source code
    repositories.

    Usage example:
        api = ServiceAPI(GitLabStrategy(oauth_token='abcdefg1234567'))
    """

    def __init__(self, strategy):
        """
        An API bus with the behavior of a specific VCS service (strategy
        pattern).
        """
        assert isinstance(strategy, ServiceAPIStrategy), \
            "strategy must be an instance of ServiceAPIStrategy."
        self.strategy = strategy
        self.response = None

    def create_project(self, name, **kwargs):
        """Create a repository project on the service platform"""
        response = self.strategy.create_project(name, **kwargs)
        self.response = response.json()
        response.raise_for_status()

    def update_project(self, key, **kwargs):
        """Update a repository project on the service platform"""
        response = self.strategy.update_project(key, **kwargs)
        self.response = response.json()
        response.raise_for_status()

    def delete_project(self, key, slug):
        """Delete a repository project on the service platform"""
        response = self.strategy.delete_project(key, slug)
        self.response = response.json()
        response.raise_for_status()

    def list_projects(self):
        """Get a list of user's projects on the service platform"""
        response = self.strategy.list_projects()
        self.response = response.json()
        response.raise_for_status()

    def project_details(self, key):
        """Get details of a single project on the service platform"""
        response = self.strategy.project_details(key)
        self.response = response.json()
        response.raise_for_status()

    def add_deploy_key(self, project_id, key_title, ssh_key, read_only=True):
        """Create a new deploy key for a project on the service platform"""
        response = self.strategy.add_deploy_key(project_id, key_title, ssh_key, read_only)
        self.response = response.json()
        response.raise_for_status()
