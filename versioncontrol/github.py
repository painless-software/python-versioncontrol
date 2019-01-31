"""
API access implementation for GitHub.

See: https://developer.github.com/v3/
"""
import json

from django.template.defaultfilters import slugify

from .base import ServiceAPI, ServiceAPIStrategy


class GitHubStrategy(ServiceAPIStrategy):
    """API bus implementation for accessing GitHub resources"""

    def __init__(self, oauth_token):
        """API access to the GitHub hosted service"""
        super().__init__(base_url='https://api.github.com',
                         headers={'Accept': 'application/vnd.github.v3+json'},
                         oauth_token=oauth_token)

    @property
    def username(self):
        """Yield the authenticated user by querying the API"""
        user_details = self.get_json_or_raise('user')
        return user_details['login']

    def create_project(self, name, slug=None, **kwargs):
        """Create a repository project on GitHub"""
        default_settings = {
            'has_issues': False,
            'has_wiki': False,
            'name': slug if slug else slugify(name),
            'private': False,
        }
        default_settings.update(kwargs)
        return self.post('user', 'repos', json=default_settings)

    def update_project(self, key, slug=None, **kwargs):
        """Update a repository project on GitHub"""
        mappings = {}
        mappings.update(kwargs)
        return self.put('repos', self.username, key, json=mappings)

    def delete_project(self, key, slug):
        """Safe-delete a repository project on GitHub"""
        response = self.project_details(key)
        response.raise_for_status()
        project_details = response.json()

        if project_details['path'] == slug:
            return self.delete('repos', self.username, key)
        return self.HTTP400_DELETION_REFUSED

    def list_projects(self):
        """Get a list of user's projects on GitHub"""
        return self.get('user', 'repos')

    def project_details(self, key):
        """Get details of a single project on GitHub"""
        return self.get('repos', self.username, key)

    def add_deploy_key(self, project_id, key_title, ssh_key, read_only=True):
        """Create a new deploy key for a project on GitHub"""
        payload = {
            'title': key_title,
            'key': ssh_key,
            'read_only': read_only,
        }
        return self.post('repos', self.username, project_id, 'keys', data=json.dumps(payload))


class GitHubAPI(ServiceAPI):
    """GitHub service API"""

    def __init__(self, oauth_token):
        super().__init__(GitHubStrategy(oauth_token))
