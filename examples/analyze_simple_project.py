#!/usr/bin/env python3
"""
Example script demonstrating how to use the Code Analysis and Re-implementation System
to analyze a simple project and generate specifications.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import CodeReimplementationSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Run the code analysis system on a sample project."""
    # Path to the sample project
    sample_project_path = Path(__file__).parent / "sample_project"
    
    # Create output directory
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Initialize the system
    system = CodeReimplementationSystem()
    system.output_dir = str(output_dir)
    
    try:
        # Analyze the codebase
        logger.info(f"Analyzing codebase at {sample_project_path}")
        analysis = await system.analyze_codebase(str(sample_project_path))
        
        # Generate specifications
        logger.info("Generating specifications")
        specifications = await system.generate_specifications(analysis)
        
        # Generate implementation strategy
        logger.info("Generating implementation strategy")
        strategy = await system.generate_implementation_strategy(specifications)
        
        # Implement code
        logger.info("Implementing code")
        implementation_result = await system.implement_code(strategy)
        
        logger.info("Process completed successfully")
        logger.info(f"Results saved to {output_dir}")
        
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 