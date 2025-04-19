"""
Test script for Git repository cloning functionality
"""
import os
import tempfile
import shutil
import logging
from git import Repo

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_git_clone():
    """Test Git repository cloning functionality"""
    logger.info("Starting Git clone test")
    
    # Create a test directory
    test_dir = os.path.join(tempfile.gettempdir(), 'test_git_clone')
    
    # Create the directory if it doesn't exist
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    try:
        # Test repository URL (use a small, public repository)
        repo_url = "https://github.com/pallets/flask.git"
        branch = "main"
        
        logger.info(f"Cloning repository: {repo_url}, branch: {branch}")
        
        # Clone the repository
        Repo.clone_from(url=repo_url, to_path=test_dir, branch=branch, depth=1)
        
        # Verify that the repository was cloned successfully
        if os.path.exists(os.path.join(test_dir, '.git')):
            logger.info("Repository cloned successfully")
            
            # Count files in the repository
            file_count = 0
            for root, dirs, files in os.walk(test_dir):
                file_count += len(files)
            
            logger.info(f"Found {file_count} files in the cloned repository")
            
            # Return success
            return True
        else:
            logger.error("Repository clone failed")
            return False
        
    except Exception as e:
        logger.error(f"Error cloning repository: {e}")
        return False
    finally:
        # Clean up the test directory
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            logger.info(f"Removed test directory: {test_dir}")

if __name__ == "__main__":
    success = test_git_clone()
    if success:
        print("Git repository cloning test successful")
    else:
        print("Git repository cloning test failed")