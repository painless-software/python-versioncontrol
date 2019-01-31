"""
API access implementation for GitLab.

See: https://docs.gitlab.com/ce/api/
"""
from .base import ServiceAPI, ServiceAPIStrategy


class GitLabStrategy(ServiceAPIStrategy):
    """API bus implementation for accessing GitLab resources"""

    def __init__(self, oauth_token):
        """API access to the GitLab hosted service"""
        super().__init__(base_url='https://gitlab.com/api/v4',
                         oauth_token=oauth_token)

    def create_project(self, name, slug=None, **kwargs):
        """Create a repository project on GitLab"""
        default_settings = {
            'builds_enabled': True,
            'issues_enabled': False,
            'merge_requests_enabled': True,
            'name': name,
            'path': slug,
            'public': False,
            'public_builds': False,
            'snippets_enabled': False,
            'wiki_enabled': False,
        }
        default_settings.update(kwargs)
        return self.post('projects', params=default_settings)

    def update_project(self, key, slug=None, **kwargs):
        """Update a repository project on GitLab"""
        mappings = {
            'path': slug,
        }
        mappings.update(kwargs)
        return self.put('projects', key, params=mappings)

    def delete_project(self, key, slug):
        """Safe-delete a repository project on GitLab"""
        response = self.project_details(key)
        response.raise_for_status()
        project_details = response.json()

        if project_details['path'] == slug:
            return self.delete('projects', key)
        return self.HTTP400_DELETION_REFUSED

    def list_projects(self):
        """Get a list of user's projects on GitLab"""
        return self.get('projects')

    def project_details(self, key):
        """Get details of a single project on GitLab"""
        return self.get('projects', key)

    def add_deploy_key(self, project_id, key_title, ssh_key, read_only=True):
        """Create a new deploy key for a project on GitLab"""
        payload = {
            'id': project_id,
            'title': key_title,
            'key': ssh_key,
            'can_push': not read_only,
        }
        return self.post('projects', project_id, 'deploy_keys', params=payload)


class GitLabAPI(ServiceAPI):
    """GitLab service API"""

    def __init__(self, oauth_token):
        super().__init__(GitLabStrategy(oauth_token))
