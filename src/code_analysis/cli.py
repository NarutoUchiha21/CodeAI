"""
Command-line interface for the code analysis system.
"""

import argparse
import asyncio
import logging
from pathlib import Path

from .core import CodeAnalyzer, CodeGenerator, StrategyGenerator, Validator
from .agents import AgentOrchestrator
from .utils import Visualizer

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

async def analyze_codebase(args):
    """Analyze a codebase and generate specifications."""
    analyzer = CodeAnalyzer()
    analysis = await analyzer.analyze(args.path)
    
    if args.output:
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)
        analyzer.save_analysis(analysis, output_path / "analysis.json")
    
    return analysis

async def generate_implementation(args):
    """Generate implementation from specifications."""
    strategy_gen = StrategyGenerator()
    code_gen = CodeGenerator()
    validator = Validator()
    
    strategy = await strategy_gen.generate_strategy(args.specs)
    implementation = await code_gen.generate_code(strategy)
    validation = await validator.validate_implementation(implementation)
    
    if args.output:
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)
        code_gen.save_implementation(implementation, output_path)
    
    return implementation, validation

async def visualize_analysis(args):
    """Generate visualizations of the codebase analysis."""
    visualizer = Visualizer()
    await visualizer.visualize_analysis(args.analysis, args.output)

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Code Analysis System CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a codebase")
    analyze_parser.add_argument("path", help="Path to the codebase to analyze")
    analyze_parser.add_argument("--output", help="Output directory for analysis results")
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate implementation")
    generate_parser.add_argument("specs", help="Path to specifications file")
    generate_parser.add_argument("--output", help="Output directory for generated code")
    
    # Visualize command
    visualize_parser = subparsers.add_parser("visualize", help="Generate visualizations")
    visualize_parser.add_argument("analysis", help="Path to analysis file")
    visualize_parser.add_argument("--output", help="Output directory for visualizations")
    
    args = parser.parse_args()
    setup_logging()
    
    if args.command == "analyze":
        asyncio.run(analyze_codebase(args))
    elif args.command == "generate":
        asyncio.run(generate_implementation(args))
    elif args.command == "visualize":
        asyncio.run(visualize_analysis(args))
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 