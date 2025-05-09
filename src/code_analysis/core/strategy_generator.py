"""
File: strategy_generator.py
Purpose: Generate implementation strategies with enhanced planning and dependency management
Generated by Code Reverse-Engineering System
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import uuid
import networkx as nx
from models import Specification, ImplementationStep, ImplementationStrategy
from openai import OpenAI
import os
import json

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

class StepType(Enum):
    SETUP = "setup"
    CORE = "core"
    FEATURE = "feature"
    INTEGRATION = "integration"
    TEST = "test"
    OPTIMIZATION = "optimization"

class DependencyType(Enum):
    REQUIRES = "requires"
    ENHANCES = "enhances"
    TESTS = "tests"
    OPTIMIZES = "optimizes"

@dataclass
class StepDependency:
    source: str
    target: str
    type: DependencyType
    strength: float
    context: Dict[str, Any]

class StrategyGenerator:
    def __init__(self):
        self.dependency_graph = nx.DiGraph()
        self.step_cache = {}
        self.strategy_templates = self._load_strategy_templates()

    def _load_strategy_templates(self) -> Dict[str, Any]:
        """Load strategy templates from configuration."""
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'strategy_templates.json')
        try:
            with open(template_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Strategy templates not found, using defaults")
            return {}

    def generate_strategy(self, specifications: List[Specification]) -> ImplementationStrategy:
        """
        Generate implementation strategy with enhanced planning.
        
        Args:
            specifications: List of Specification objects.
            
        Returns:
            ImplementationStrategy with planned steps.
        """
        logger.info("Generating enhanced implementation strategy")
        
        # Build dependency graph
        self._build_dependency_graph(specifications)
        
        # Generate implementation steps
        steps = self._generate_implementation_steps(specifications)
        
        # Optimize step order
        optimized_steps = self._optimize_step_order(steps)
        
        # Create strategy
        strategy = ImplementationStrategy(
            steps=optimized_steps,
            dependencies=self._extract_dependencies(),
            metadata=self._generate_strategy_metadata(specifications)
        )
        
        return strategy

    def _build_dependency_graph(self, specifications: List[Specification]):
        """Build dependency graph from specifications."""
        self.dependency_graph.clear()
        
        # Add nodes for each specification
        for spec in specifications:
            self.dependency_graph.add_node(spec.id, type='specification', data=spec)
        
        # Add dependencies between specifications
        for spec in specifications:
            # Analyze direct dependencies
            for dep in spec.dependencies:
                self.dependency_graph.add_edge(
                    spec.id,
                    dep,
                    type=DependencyType.REQUIRES,
                    strength=1.0
                )
            
            # Analyze implicit dependencies
            implicit_deps = self._analyze_implicit_dependencies(spec, specifications)
            for dep in implicit_deps:
                self.dependency_graph.add_edge(
                    spec.id,
                    dep.target,
                    type=dep.type,
                    strength=dep.strength,
                    context=dep.context
                )

    def _generate_implementation_steps(self, specifications: List[Specification]) -> List[ImplementationStep]:
        """Generate implementation steps based on specifications and dependencies."""
        steps = []
        
        # Generate setup steps
        setup_steps = self._generate_setup_steps(specifications)
        steps.extend(setup_steps)
        
        # Generate core implementation steps
        core_steps = self._generate_core_steps(specifications)
        steps.extend(core_steps)
        
        # Generate feature implementation steps
        feature_steps = self._generate_feature_steps(specifications)
        steps.extend(feature_steps)
        
        # Generate integration steps
        integration_steps = self._generate_integration_steps(specifications)
        steps.extend(integration_steps)
        
        # Generate test steps
        test_steps = self._generate_test_steps(specifications)
        steps.extend(test_steps)
        
        # Generate optimization steps
        optimization_steps = self._generate_optimization_steps(specifications)
        steps.extend(optimization_steps)
        
        return steps

    def _optimize_step_order(self, steps: List[ImplementationStep]) -> List[ImplementationStep]:
        """Optimize the order of implementation steps."""
        # Create step dependency graph
        step_graph = nx.DiGraph()
        
        for step in steps:
            step_graph.add_node(step.id, step=step)
        
        # Add dependencies between steps
        for step in steps:
            for dep in step.dependencies:
                step_graph.add_edge(dep, step.id)
        
        # Check for cycles
        if not nx.is_directed_acyclic_graph(step_graph):
            logger.warning("Step dependency graph contains cycles")
            # Break cycles by removing weakest dependencies
            step_graph = self._break_cycles(step_graph)
        
        # Get topological sort
        try:
            ordered_steps = list(nx.topological_sort(step_graph))
            return [step_graph.nodes[step_id]['step'] for step_id in ordered_steps]
        except nx.NetworkXUnfeasible:
            logger.error("Could not determine step order")
            return steps

    def _generate_setup_steps(self, specifications: List[Specification]) -> List[ImplementationStep]:
        """Generate setup and initialization steps."""
        steps = []
        
        # Project structure setup
        steps.append(ImplementationStep(
            id="setup_project_structure",
            type=StepType.SETUP,
            description="Set up project structure and configuration",
            specifications=[s for s in specifications if s.type == 'project_structure'],
            dependencies=[],
            estimated_time=30,
            priority=1
        ))
        
        # Dependencies setup
        steps.append(ImplementationStep(
            id="setup_dependencies",
            type=StepType.SETUP,
            description="Set up project dependencies and environment",
            specifications=[s for s in specifications if s.type == 'dependencies'],
            dependencies=["setup_project_structure"],
            estimated_time=15,
            priority=1
        ))
        
        return steps

    def _generate_core_steps(self, specifications: List[Specification]) -> List[ImplementationStep]:
        """Generate core implementation steps."""
        steps = []
        
        # Core components
        core_specs = [s for s in specifications if s.type == 'core_component']
        for spec in core_specs:
            steps.append(ImplementationStep(
                id=f"implement_core_{spec.id}",
                type=StepType.CORE,
                description=f"Implement core component: {spec.name}",
                specifications=[spec],
                dependencies=self._get_core_dependencies(spec),
                estimated_time=self._estimate_implementation_time(spec),
                priority=2
            ))
        
        return steps

    def _generate_feature_steps(self, specifications: List[Specification]) -> List[ImplementationStep]:
        """Generate feature implementation steps."""
        steps = []
        
        # Feature components
        feature_specs = [s for s in specifications if s.type == 'feature']
        for spec in feature_specs:
            steps.append(ImplementationStep(
                id=f"implement_feature_{spec.id}",
                type=StepType.FEATURE,
                description=f"Implement feature: {spec.name}",
                specifications=[spec],
                dependencies=self._get_feature_dependencies(spec),
                estimated_time=self._estimate_implementation_time(spec),
                priority=3
            ))
        
        return steps

    def _generate_integration_steps(self, specifications: List[Specification]) -> List[ImplementationStep]:
        """Generate integration steps."""
        steps = []
        
        # Component integration
        integration_specs = [s for s in specifications if s.type == 'integration']
        for spec in integration_specs:
            steps.append(ImplementationStep(
                id=f"integrate_{spec.id}",
                type=StepType.INTEGRATION,
                description=f"Integrate components: {spec.name}",
                specifications=[spec],
                dependencies=self._get_integration_dependencies(spec),
                estimated_time=self._estimate_integration_time(spec),
                priority=4
            ))
        
        return steps

    def _generate_test_steps(self, specifications: List[Specification]) -> List[ImplementationStep]:
        """Generate test implementation steps."""
        steps = []
        
        # Unit tests
        test_specs = [s for s in specifications if s.type == 'test']
        for spec in test_specs:
            steps.append(ImplementationStep(
                id=f"implement_tests_{spec.id}",
                type=StepType.TEST,
                description=f"Implement tests for: {spec.name}",
                specifications=[spec],
                dependencies=self._get_test_dependencies(spec),
                estimated_time=self._estimate_test_time(spec),
                priority=5
            ))
        
        return steps

    def _generate_optimization_steps(self, specifications: List[Specification]) -> List[ImplementationStep]:
        """Generate optimization steps."""
        steps = []
        
        # Performance optimization
        optimization_specs = [s for s in specifications if s.type == 'optimization']
        for spec in optimization_specs:
            steps.append(ImplementationStep(
                id=f"optimize_{spec.id}",
                type=StepType.OPTIMIZATION,
                description=f"Optimize: {spec.name}",
                specifications=[spec],
                dependencies=self._get_optimization_dependencies(spec),
                estimated_time=self._estimate_optimization_time(spec),
                priority=6
            ))
        
        return steps

    def _analyze_implicit_dependencies(self, spec: Specification, all_specs: List[Specification]) -> List[StepDependency]:
        """Analyze and identify implicit dependencies between specifications."""
        implicit_deps = []
        
        # Analyze data flow dependencies
        data_flow_deps = self._analyze_data_flow_dependencies(spec, all_specs)
        implicit_deps.extend(data_flow_deps)
        
        # Analyze functional dependencies
        functional_deps = self._analyze_functional_dependencies(spec, all_specs)
        implicit_deps.extend(functional_deps)
        
        # Analyze resource dependencies
        resource_deps = self._analyze_resource_dependencies(spec, all_specs)
        implicit_deps.extend(resource_deps)
        
        return implicit_deps

    def _break_cycles(self, graph: nx.DiGraph) -> nx.DiGraph:
        """Break cycles in the dependency graph by removing weakest dependencies."""
        while not nx.is_directed_acyclic_graph(graph):
            cycles = list(nx.simple_cycles(graph))
            if not cycles:
                break
            
            # Find the weakest edge in the first cycle
            cycle = cycles[0]
            weakest_edge = min(
                [(u, v) for u, v in zip(cycle, cycle[1:])],
                key=lambda e: graph.edges[e].get('strength', 1.0)
            )
            
            # Remove the weakest edge
            graph.remove_edge(*weakest_edge)
        
        return graph

    def _extract_dependencies(self) -> List[StepDependency]:
        """Extract dependencies from the dependency graph."""
        dependencies = []
        
        for u, v, data in self.dependency_graph.edges(data=True):
            dependencies.append(StepDependency(
                source=u,
                target=v,
                type=data.get('type', DependencyType.REQUIRES),
                strength=data.get('strength', 1.0),
                context=data.get('context', {})
            ))
        
        return dependencies

    def _generate_strategy_metadata(self, specifications: List[Specification]) -> Dict[str, Any]:
        """Generate metadata for the implementation strategy."""
        return {
            'total_specifications': len(specifications),
            'specification_types': {
                spec.type: len([s for s in specifications if s.type == spec.type])
                for spec in specifications
            },
            'estimated_total_time': sum(
                self._estimate_implementation_time(spec)
                for spec in specifications
            ),
            'complexity_score': self._calculate_complexity_score(specifications),
            'risk_assessment': self._assess_implementation_risks(specifications)
        }

    def _get_core_dependencies(self, spec: Specification) -> List[str]:
        """Get dependencies for a core component."""
        # This is a placeholder and should be replaced with actual implementation
        return []

    def _get_feature_dependencies(self, spec: Specification) -> List[str]:
        """Get dependencies for a feature."""
        # This is a placeholder and should be replaced with actual implementation
        return []

    def _get_integration_dependencies(self, spec: Specification) -> List[str]:
        """Get dependencies for integration."""
        # This is a placeholder and should be replaced with actual implementation
        return []

    def _get_test_dependencies(self, spec: Specification) -> List[str]:
        """Get dependencies for tests."""
        # This is a placeholder and should be replaced with actual implementation
        return []

    def _get_optimization_dependencies(self, spec: Specification) -> List[str]:
        """Get dependencies for optimization."""
        # This is a placeholder and should be replaced with actual implementation
        return []

    def _estimate_implementation_time(self, spec: Specification) -> float:
        """Estimate the time required to implement a specification."""
        # This is a placeholder and should be replaced with actual implementation
        return 0.0

    def _estimate_integration_time(self, spec: Specification) -> float:
        """Estimate the time required to integrate components."""
        # This is a placeholder and should be replaced with actual implementation
        return 0.0

    def _estimate_test_time(self, spec: Specification) -> float:
        """Estimate the time required to implement tests."""
        # This is a placeholder and should be replaced with actual implementation
        return 0.0

    def _estimate_optimization_time(self, spec: Specification) -> float:
        """Estimate the time required to optimize a specification."""
        # This is a placeholder and should be replaced with actual implementation
        return 0.0

    def _analyze_data_flow_dependencies(self, spec: Specification, all_specs: List[Specification]) -> List[StepDependency]:
        """Analyze data flow dependencies between specifications."""
        # This is a placeholder and should be replaced with actual implementation
        return []

    def _analyze_functional_dependencies(self, spec: Specification, all_specs: List[Specification]) -> List[StepDependency]:
        """Analyze functional dependencies between specifications."""
        # This is a placeholder and should be replaced with actual implementation
        return []

    def _analyze_resource_dependencies(self, spec: Specification, all_specs: List[Specification]) -> List[StepDependency]:
        """Analyze resource dependencies between specifications."""
        # This is a placeholder and should be replaced with actual implementation
        return []

    def _calculate_complexity_score(self, specifications: List[Specification]) -> float:
        """Calculate complexity score based on the specifications."""
        # This is a placeholder and should be replaced with actual implementation
        return 0.0

    def _assess_implementation_risks(self, specifications: List[Specification]) -> Dict[str, Any]:
        """Assess implementation risks based on the specifications."""
        # This is a placeholder and should be replaced with actual implementation
        return {}

if __name__ == "__main__":
    # Test with sample specifications
    from models import Specification
    
    sample_specs = [
        Specification(
            entity_name="Calculator",
            entity_type="class",
            purpose="A simple calculator class that provides basic arithmetic operations",
            inputs=[
                {"name": "a", "type": "number"},
                {"name": "b", "type": "number"}
            ],
            outputs=[
                {"name": "add", "type": "method"},
                {"name": "subtract", "type": "method"}
            ],
            constraints=["Must validate inputs are numbers"],
            dependencies=[],
            behavior="Implements basic arithmetic operations and maintains calculation history",
            examples=[
                {"type": "code", "content": "calc = Calculator()\nresult = calc.add(5, 3)  # Returns 8"}
            ]
        ),
        Specification(
            entity_name="MathUtils",
            entity_type="module",
            purpose="Utility module with mathematical functions",
            inputs=None,
            outputs=None,
            constraints=["Must handle division by zero"],
            dependencies=[],
            behavior="Provides utility math functions beyond basic arithmetic",
            examples=None
        ),
        Specification(
            entity_name="CalculatorApp",
            entity_type="class",
            purpose="User interface for the calculator",
            inputs=None,
            outputs=None,
            constraints=["Must handle user input validation"],
            dependencies=["Calculator"],
            behavior="Provides a user interface to interact with the Calculator class",
            examples=None
        )
    ]
    
    strategy_generator = StrategyGenerator()
    strategy = strategy_generator.generate_strategy(sample_specs)
    
    print("Generated Implementation Strategy:")
    print(f"Total steps: {len(strategy.steps)}")
    
    print("\nExecution order:")
    for step_id in strategy.execution_order:
        step = next((s for s in strategy.steps if s.id == step_id), None)
        if step:
            print(f"- {step.description}")
            print(f"  Dependencies: {strategy.dependencies[step.id]}")
