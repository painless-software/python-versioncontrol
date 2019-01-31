"""
API access implementation for Bitbucket.

See: https://developer.atlassian.com/bitbucket/api/2/reference/
"""
from django.template.defaultfilters import slugify

from .base import ServiceAPI, ServiceAPIStrategy


class BitbucketStrategy(ServiceAPIStrategy):
    """API bus implementation for accessing Bitbucket resources"""

    def __init__(self, oauth_token):
        """API access to the Bitbucket hosted service"""
        super().__init__(base_url='https://api.bitbucket.org/2.0',
                         oauth_token=oauth_token)

    @property
    def username(self):
        """Yield the username of the Bitbucket account by querying the API"""
        user_details = self.get_json_or_raise('user')
        return user_details['username']

    def create_project(self, name, slug=None, **kwargs):
        """Create a repository project on Bitbucket"""
        default_settings = {
            'has_issues': False,
            'has_wiki': False,
            'is_private': True,
            'name': name,
            'scm': 'git',
        }
        default_settings.update(kwargs)
        if not slug:
            slug = slugify(name)
        return self.post('repositories', self.username, slug, json=default_settings)

    def update_project(self, key, slug=None, **kwargs):
        """Update a repository project on Bitbucket"""
        mappings = {}
        mappings.update(kwargs)
        return self.put('repositories', self.username, slug, json=mappings)

    def delete_project(self, key, slug):
        """Safe-delete a repository project on Bitbucket"""
        response = self.project_details(key)
        response.raise_for_status()
        project_details = response.json()

        if project_details['name'] == slug:
            return self.delete('repositories', self.username, slug)
        return self.HTTP400_DELETION_REFUSED

    def list_projects(self):
        """Get a list of user's projects on Bitbucket"""
        return self.get('repositories', self.username)

    def project_details(self, key):
        """Get details of a single project on Bitbucket"""
        return self.get('repositories', self.username, key)

    def add_deploy_key(self, project_id, key_title, ssh_key, read_only=True):
        """Create a new deploy key for a project on Bitbucket"""
        raise NotImplementedError("Not available on Bitbucket, we're sorry!")


class BitbucketAPI(ServiceAPI):
    """Bitbucket service API"""

    def __init__(self, oauth_token):
        super().__init__(BitbucketStrategy(oauth_token))
