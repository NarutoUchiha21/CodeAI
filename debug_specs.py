"""
Debug script for specification extraction
"""
import os
import logging
import sys
from models import CodebaseAnalysis, CodeEntity
from spec_extractor import extract_specifications
from code_analyzer import analyze_codebase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """
    Test the specification extraction functionality with a sample codebase
    """
    logger.info("Starting specification extraction debug")
    
    # Set OpenAI API key from environment
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    # Create a test codebase path (assuming there's something in /tmp to analyze)
    test_path = "/tmp"
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
    
    logger.info(f"Analyzing codebase at: {test_path}")
    
    try:
        # Analyze codebase
        analysis_result = analyze_codebase(test_path)
        logger.info(f"Analysis complete. Found {len(analysis_result.entities)} entities")
        
        # Extract specifications
        logger.info("Extracting specifications...")
        specs = extract_specifications(analysis_result)
        
        logger.info(f"Successfully extracted {len(specs)} specifications")
        for i, spec in enumerate(specs):
            logger.info(f"Spec {i+1}: {spec.entity_name} ({spec.entity_type})")
        
        logger.info("Specification extraction test successful")
    except Exception as e:
        logger.error(f"Error during specification extraction: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()