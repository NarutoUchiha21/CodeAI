# Code Analysis System

An AI-powered system for analyzing codebases and generating specifications for re-implementation.

## Features

- Codebase analysis and understanding
- Specification generation
- Implementation strategy planning
- Code generation
- Validation and testing
- Visualization tools
- Web interface
- CLI tools

## Project Structure

```
code-analysis-system/
├── src/
│   └── code_analysis/
│       ├── core/           # Core functionality
│       │   ├── models.py
│       │   ├── knowledge_graph.py
│       │   ├── code_analyzer.py
│       │   ├── code_generator.py
│       │   ├── strategy_generator.py
│       │   └── validator.py
│       ├── agents/         # Agent-based components
│       │   ├── orchestrator.py
│       │   └── spec_extractor.py
│       ├── utils/          # Utility functions
│       │   ├── visualizer.py
│       │   └── git_utils.py
│       ├── web/           # Web interface
│       │   └── app.py
│       ├── templates/     # Web templates
│       ├── static/        # Static assets
│       └── cli.py         # Command-line interface
├── tests/                # Test suite
├── docs/                 # Documentation
├── examples/             # Example projects
├── setup.py             # Package configuration
├── requirements.txt     # Dependencies
└── README.md           # This file
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/code-analysis-system.git
cd code-analysis-system
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package:
```bash
pip install -e .
```

## Usage

### Command Line Interface

The system provides a CLI with three main commands:

1. Analyze a codebase:
```bash
code-analysis analyze /path/to/codebase --output ./analysis_results
```

2. Generate implementation from specifications:
```bash
code-analysis generate /path/to/specs.json --output ./generated_code
```

3. Visualize analysis results:
```bash
code-analysis visualize /path/to/analysis.json --output ./visualizations
```

### Web Interface

To start the web interface:

```bash
python -m code_analysis.web.app
```

Then open your browser at `http://localhost:5000`.

### Python API

```python
from code_analysis.core import CodeAnalyzer, CodeGenerator
from code_analysis.agents import AgentOrchestrator

# Analyze a codebase
analyzer = CodeAnalyzer()
analysis = await analyzer.analyze("/path/to/codebase")

# Generate implementation
generator = CodeGenerator()
implementation = await generator.generate_code(analysis)
```

## Development

1. Install development dependencies:
```bash
pip install -e ".[dev]"
```

2. Run tests:
```bash
pytest
```

3. Generate documentation:
```bash
cd docs
make html
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 