"""
Test script for code analyzer functionality
"""
import os
import tempfile
import shutil
import logging
from code_analyzer import analyze_codebase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_test_codebase():
    """Create a test codebase with different file types and content"""
    test_dir = os.path.join(tempfile.gettempdir(), 'test_codebase')
    
    # Create the directory if it doesn't exist
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    # Create Python file
    with open(os.path.join(test_dir, 'main.py'), 'w') as f:
        f.write("""
import os

def main():
    print("Hello, world!")
    
class TestClass:
    def __init__(self):
        self.value = 10
        
    def get_value(self):
        return self.value
        
if __name__ == "__main__":
    main()
""")
    
    # Create JavaScript file
    with open(os.path.join(test_dir, 'script.js'), 'w') as f:
        f.write("""
const axios = require('axios');

function fetchData() {
    return axios.get('https://api.example.com/data');
}

class DataProcessor {
    constructor(data) {
        this.data = data;
    }
    
    process() {
        return this.data.map(item => item.value * 2);
    }
}

module.exports = { fetchData, DataProcessor };
""")
    
    # Create HTML file
    with open(os.path.join(test_dir, 'index.html'), 'w') as f:
        f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <h1>Test Page</h1>
    <div class="container">
        <p>This is a test page</p>
    </div>
    <script src="script.js"></script>
</body>
</html>
""")
    
    # Create CSS file
    with open(os.path.join(test_dir, 'styles.css'), 'w') as f:
        f.write("""
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

h1 {
    color: #333;
}
""")
    
    # Create text file
    with open(os.path.join(test_dir, 'README.md'), 'w') as f:
        f.write("""
# Test Project

This is a test project for the code analyzer.

## Files included:
- main.py - Python code
- script.js - JavaScript code
- index.html - HTML page
- styles.css - CSS styles
""")
    
    # Create a small binary file
    with open(os.path.join(test_dir, 'binary.dat'), 'wb') as f:
        f.write(os.urandom(100))
    
    return test_dir

def main():
    """Test the code analyzer with a test codebase"""
    logger.info("Starting code analyzer test")
    
    # Create test codebase
    test_dir = create_test_codebase()
    logger.info(f"Created test codebase at: {test_dir}")
    
    try:
        # Analyze the codebase
        logger.info("Analyzing test codebase...")
        analysis = analyze_codebase(test_dir)
        
        # Print results
        logger.info(f"Analysis complete. Found {len(analysis.entities)} entities in {analysis.metrics['total_files']} files.")
        logger.info(f"Languages: {analysis.languages}")
        logger.info(f"Total lines: {analysis.metrics['total_lines']}")
        
        # Print entities by type
        entity_types = {}
        for entity in analysis.entities:
            if entity.type not in entity_types:
                entity_types[entity.type] = []
            entity_types[entity.type].append(entity.name)
        
        for entity_type, entities in entity_types.items():
            logger.info(f"{entity_type} entities: {', '.join(entities)}")
        
        logger.info("Code analyzer test successful")
    except Exception as e:
        logger.error(f"Error during code analysis: {str(e)}")
    finally:
        # Clean up the test directory
        shutil.rmtree(test_dir)
        logger.info(f"Removed test directory: {test_dir}")

if __name__ == "__main__":
    main()