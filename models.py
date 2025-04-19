from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

# Define data models for the system

@dataclass
class CodeEntity:
    """Represents a code entity (class, function, module, etc.)"""
    name: str
    type: str  # 'class', 'function', 'module', etc.
    path: str
    code: str
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CodebaseAnalysis:
    """Results of codebase analysis"""
    entities: List[CodeEntity]
    languages: Dict[str, int]  # language -> lines of code
    dependencies: Dict[str, List[str]]  # entity -> [dependencies]
    structure: Dict[str, Any]  # file structure
    metrics: Dict[str, Any]  # complexity, size, etc.

@dataclass
class Specification:
    """Extracted specification from code"""
    entity_name: str
    entity_type: str
    purpose: str
    inputs: Optional[List[Dict[str, str]]] = None
    outputs: Optional[List[Dict[str, str]]] = None
    constraints: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    behavior: Optional[str] = None
    examples: Optional[List[Dict[str, Any]]] = None

@dataclass
class ImplementationStep:
    """A single step in the implementation strategy"""
    id: str
    description: str
    dependencies: List[str]  # IDs of steps this depends on
    expected_output: str
    validation_criteria: List[str]

@dataclass
class ImplementationStrategy:
    """Strategy for implementing the specifications"""
    steps: List[ImplementationStep]
    dependencies: Dict[str, List[str]]  # step ID -> [dependent step IDs]
    execution_order: List[str]  # step IDs in order of execution

@dataclass
class GeneratedFile:
    """A generated file in the re-implementation"""
    path: str
    content: str
    purpose: str
    derived_from: List[str]  # specification IDs this was derived from

@dataclass
class GeneratedCode:
    """Complete generated codebase"""
    files: List[GeneratedFile]
    structure: Dict[str, Any]  # file structure
    execution_instructions: str

@dataclass
class ValidationResult:
    """Results of validating the generated code against the original"""
    success: bool
    functional_equivalence: float  # percentage 0-100
    structural_similarity: float  # percentage 0-100
    missing_features: List[str]
    additional_features: List[str]
    error_details: Optional[Dict[str, Any]] = None
