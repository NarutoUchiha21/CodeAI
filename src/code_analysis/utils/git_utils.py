"""
Git utilities for the code analysis system.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

class GitUtils:
    """Utility class for Git operations."""
    
    @staticmethod
    def clone_repository(url: str, target_dir: Optional[str] = None) -> str:
        """
        Clone a Git repository.
        
        Args:
            url: The URL of the repository to clone
            target_dir: Optional target directory for the clone
            
        Returns:
            The path to the cloned repository
            
        Raises:
            subprocess.CalledProcessError: If the clone operation fails
        """
        if target_dir is None:
            # Extract repository name from URL
            repo_name = url.split('/')[-1].replace('.git', '')
            target_dir = repo_name
        
        target_path = Path(target_dir)
        
        # Create parent directory if it doesn't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Clone the repository
        subprocess.run(
            ["git", "clone", url, str(target_path)],
            check=True,
            capture_output=True,
            text=True
        )
        
        return str(target_path)
    
    @staticmethod
    def get_file_history(file_path: str, repo_path: Optional[str] = None) -> List[Tuple[str, str, str]]:
        """
        Get the commit history for a specific file.
        
        Args:
            file_path: Path to the file
            repo_path: Optional path to the Git repository
            
        Returns:
            List of tuples containing (commit_hash, author, date) for each commit
        """
        if repo_path is None:
            repo_path = os.getcwd()
        
        # Get the relative path from the repository root
        rel_path = os.path.relpath(file_path, repo_path)
        
        # Get the log for the file
        result = subprocess.run(
            ["git", "log", "--pretty=format:%H|%an|%ad", "--date=short", rel_path],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Parse the output
        history = []
        for line in result.stdout.strip().split('\n'):
            if line:
                commit_hash, author, date = line.split('|')
                history.append((commit_hash, author, date))
        
        return history
    
    @staticmethod
    def get_file_content(file_path: str, commit_hash: Optional[str] = None, repo_path: Optional[str] = None) -> str:
        """
        Get the content of a file at a specific commit.
        
        Args:
            file_path: Path to the file
            commit_hash: Optional commit hash to get the file content at
            repo_path: Optional path to the Git repository
            
        Returns:
            The content of the file
        """
        if repo_path is None:
            repo_path = os.getcwd()
        
        # Get the relative path from the repository root
        rel_path = os.path.relpath(file_path, repo_path)
        
        # Build the git show command
        cmd = ["git", "show"]
        if commit_hash:
            cmd.append(f"{commit_hash}:{rel_path}")
        else:
            cmd.append(rel_path)
        
        # Get the file content
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True
        )
        
        return result.stdout
    
    @staticmethod
    def get_repository_info(repo_path: Optional[str] = None) -> dict:
        """
        Get information about a Git repository.
        
        Args:
            repo_path: Optional path to the Git repository
            
        Returns:
            Dictionary containing repository information
        """
        if repo_path is None:
            repo_path = os.getcwd()
        
        info = {}
        
        # Get remote URL
        try:
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            info["remote_url"] = result.stdout.strip()
        except subprocess.CalledProcessError:
            info["remote_url"] = None
        
        # Get current branch
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            info["current_branch"] = result.stdout.strip()
        except subprocess.CalledProcessError:
            info["current_branch"] = None
        
        # Get commit count
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            info["commit_count"] = int(result.stdout.strip())
        except subprocess.CalledProcessError:
            info["commit_count"] = 0
        
        return info 