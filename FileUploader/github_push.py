import os
import subprocess

class GitHubManager:
    def __init__(self, repo_path, token=None, user=None, email=None):
        self.repo_path = repo_path
        self.token = token
        self.user = user
        self.email = email

    def get_repository_status(self):
        """
        Returns a dict with:
            branch: str
            has_changes: bool
            modified_files: list
            untracked_files: list
            staged_files: list
            deleted_files: list
            revert_in_progress: bool
        """
        try:
            branch = subprocess.check_output([
                'git', '-C', self.repo_path, 'rev-parse', '--abbrev-ref', 'HEAD'
            ]).decode().strip()
            status_lines = subprocess.check_output([
                'git', '-C', self.repo_path, 'status', '--porcelain'
            ]).decode().splitlines()
            modified_files = []
            untracked_files = []
            staged_files = []
            deleted_files = []
            for line in status_lines:
                if not line.strip():
                    continue
                code = line[:2]
                file_path = line[3:].strip()
                # Staged changes (first char)
                if code[0] == 'A' or code[0] == 'M':
                    staged_files.append(file_path)
                if code[0] == 'D':
                    deleted_files.append(file_path)
                # Unstaged changes (second char)
                if code[1] == 'M':
                    modified_files.append(file_path)
                if code[1] == 'D':
                    deleted_files.append(file_path)
                # Untracked
                if code == '??':
                    untracked_files.append(file_path)
            has_changes = bool(modified_files or untracked_files or staged_files or deleted_files)
            # Check for ongoing revert/merge
            revert_in_progress = os.path.exists(os.path.join(self.repo_path, '.git', 'REVERT_HEAD'))
            return {
                'branch': branch,
                'has_changes': has_changes,
                'modified_files': modified_files,
                'untracked_files': untracked_files,
                'staged_files': staged_files,
                'deleted_files': deleted_files,
                'revert_in_progress': revert_in_progress
            }
        except Exception as e:
            return {'error': str(e)}

    def full_push_workflow(self, commit_msg, auto_add=True, handle_revert=True):
        try:
            if self.user:
                subprocess.run(['git', '-C', self.repo_path, 'config', 'user.name', self.user], check=True)
            if self.email:
                subprocess.run(['git', '-C', self.repo_path, 'config', 'user.email', self.email], check=True)
            if auto_add:
                subprocess.run(['git', '-C', self.repo_path, 'add', '.'], check=True)
            subprocess.run(['git', '-C', self.repo_path, 'commit', '-m', commit_msg], check=True)
            # Use token if provided (for HTTPS remote)
            push_env = os.environ.copy()
            if self.token:
                push_env['GIT_ASKPASS'] = 'echo'
                push_env['GITHUB_TOKEN'] = self.token
            subprocess.run(['git', '-C', self.repo_path, 'push'], check=True, env=push_env)
            return True, 'Push successful.'
        except subprocess.CalledProcessError as e:
            return False, f'Git error: {e}'
        except Exception as e:
            return False, str(e)
