"""
Pytest configuration file.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, src_path)

# Set up test environment variables
os.environ["TESTING"] = "true"
os.environ["DEBUG"] = "true"

# Import fixtures
from code_analysis.core.models import (
    CodeEntity,
    Specification,
    ImplementationStep,
    ImplementationStrategy,
    CodebaseAnalysis,
)

@pytest.fixture
def sample_code_entity():
    """Create a sample code entity for testing."""
    return CodeEntity(
        name="Calculator",
        type="class",
        file_path="calculator.py",
        line_number=1,
        content="class Calculator:\n    def add(self, a, b):\n        return a + b",
    )

@pytest.fixture
def sample_specification():
    """Create a sample specification for testing."""
    return Specification(
        name="Calculator Implementation",
        description="A simple calculator class with basic arithmetic operations",
        entities=[
            CodeEntity(
                name="Calculator",
                type="class",
                file_path="calculator.py",
                line_number=1,
                content="class Calculator:\n    def add(self, a, b):\n        return a + b",
            )
        ],
        dependencies=[],
    )

@pytest.fixture
def sample_implementation_step():
    """Create a sample implementation step for testing."""
    return ImplementationStep(
        id="step1",
        description="Create Calculator class",
        code="class Calculator:\n    def __init__(self):\n        self.last_result = 0",
        dependencies=[],
    )

@pytest.fixture
def sample_implementation_strategy():
    """Create a sample implementation strategy for testing."""
    return ImplementationStrategy(
        name="Calculator Implementation",
        description="Step-by-step implementation of the Calculator class",
        steps=[
            ImplementationStep(
                id="step1",
                description="Create Calculator class",
                code="class Calculator:\n    def __init__(self):\n        self.last_result = 0",
                dependencies=[],
            ),
            ImplementationStep(
                id="step2",
                description="Add arithmetic methods",
                code="def add(self, a, b):\n    self.last_result = a + b\n    return self.last_result",
                dependencies=["step1"],
            ),
        ],
    )

@pytest.fixture
def sample_codebase_analysis():
    """Create a sample codebase analysis for testing."""
    return CodebaseAnalysis(
        project_name="Calculator",
        description="A simple calculator implementation",
        entities=[
            CodeEntity(
                name="Calculator",
                type="class",
                file_path="calculator.py",
                line_number=1,
                content="class Calculator:\n    def add(self, a, b):\n        return a + b",
            )
        ],
        relationships=[],
        patterns=[],
    ) 