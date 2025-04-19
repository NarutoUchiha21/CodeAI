import logging
from typing import Dict, List, Any, Optional
import re
import uuid
from models import Specification, ImplementationStep, ImplementationStrategy
from openai import OpenAI
import os
import json
import networkx as nx

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def generate_strategy(specifications: List[Specification]) -> ImplementationStrategy:
    """
    Generate an implementation strategy based on extracted specifications.
    
    Args:
        specifications: List of extracted Specification objects.
        
    Returns:
        ImplementationStrategy with steps and dependencies.
    """
    logger.info("Generating implementation strategy from specifications")
    
    # Group specifications by type for better organization
    specs_by_type = {}
    for spec in specifications:
        if spec.entity_type not in specs_by_type:
            specs_by_type[spec.entity_type] = []
        specs_by_type[spec.entity_type].append(spec)
    
    # Step 1: Generate architectural steps first (if any)
    steps = []
    dependencies = {}
    
    if 'architecture' in specs_by_type:
        arch_steps = generate_architectural_steps(specs_by_type['architecture'])
        steps.extend(arch_steps)
        
        # Add dependencies between architectural steps
        for i, step in enumerate(arch_steps):
            if i > 0:
                dependencies[step.id] = [arch_steps[i-1].id]
            else:
                dependencies[step.id] = []
    
    # Step 2: Generate steps for each type of entity
    entity_steps_by_type = {}
    
    for entity_type, entity_specs in specs_by_type.items():
        if entity_type != 'architecture' and entity_type != 'pattern':
            type_steps = generate_entity_type_steps(entity_type, entity_specs)
            entity_steps_by_type[entity_type] = type_steps
            steps.extend(type_steps)
    
    # Step 3: Add pattern steps (if any)
    if 'pattern' in specs_by_type:
        pattern_steps = generate_pattern_steps(specs_by_type['pattern'])
        steps.extend(pattern_steps)
    
    # Step 4: Establish dependencies between steps
    dependencies = establish_step_dependencies(steps, entity_steps_by_type, specifications)
    
    # Step 5: Calculate execution order using topological sort
    execution_order = calculate_execution_order(steps, dependencies)
    
    logger.info(f"Generated strategy with {len(steps)} steps")
    
    return ImplementationStrategy(
        steps=steps,
        dependencies=dependencies,
        execution_order=execution_order
    )

def generate_architectural_steps(arch_specs: List[Specification]) -> List[ImplementationStep]:
    """
    Generate implementation steps for architectural specifications.
    
    Args:
        arch_specs: List of architectural Specification objects.
        
    Returns:
        List of ImplementationStep objects.
    """
    steps = []
    
    for spec in arch_specs:
        # Always start with project setup
        setup_step = ImplementationStep(
            id=f"setup_{str(uuid.uuid4())[:8]}",
            description=f"Set up project structure based on {spec.entity_name} architecture",
            dependencies=[],
            expected_output="Project directory structure and essential configuration files",
            validation_criteria=["Directory structure exists", "Configuration files are properly formatted"]
        )
        steps.append(setup_step)
        
        # Add step for implementing architectural components
        components_step = ImplementationStep(
            id=f"arch_components_{str(uuid.uuid4())[:8]}",
            description=f"Implement core architectural components for {spec.entity_name}",
            dependencies=[setup_step.id],
            expected_output="Core framework components implementing the architectural style",
            validation_criteria=["Components match architectural description", "Components are properly connected"]
        )
        steps.append(components_step)
    
    return steps

def generate_entity_type_steps(entity_type: str, entity_specs: List[Specification]) -> List[ImplementationStep]:
    """
    Generate implementation steps for a specific entity type.
    
    Args:
        entity_type: Type of entity ('module', 'class', 'function', etc.)
        entity_specs: List of Specification objects for this entity type.
        
    Returns:
        List of ImplementationStep objects.
    """
    steps = []
    
    # Group related entities
    groups = group_related_entities(entity_specs)
    
    for group_name, group_specs in groups.items():
        # For each group, create implementation steps
        if len(group_specs) > 3:
            # For large groups, create a step for the group
            group_step = ImplementationStep(
                id=f"{entity_type}_{group_name}_{str(uuid.uuid4())[:8]}",
                description=f"Implement {entity_type} group: {group_name}",
                dependencies=[],  # Will be filled later
                expected_output=f"Implementation of {len(group_specs)} {entity_type}s in the {group_name} group",
                validation_criteria=[
                    f"All {entity_type}s in group are implemented",
                    "Implementations match specifications",
                    "Unit tests pass for all implementations"
                ]
            )
            steps.append(group_step)
        else:
            # For smaller groups, create steps for individual entities
            for spec in group_specs:
                entity_step = create_entity_implementation_step(spec)
                steps.append(entity_step)
    
    return steps

def group_related_entities(entity_specs: List[Specification]) -> Dict[str, List[Specification]]:
    """
    Group related entities based on names, dependencies, and purpose.
    
    Args:
        entity_specs: List of Specification objects for entities.
        
    Returns:
        Dictionary mapping group names to lists of Specification objects.
    """
    if not entity_specs:
        return {}
    
    # Start with a common group
    groups = {"common": []}
    
    # Try to identify groups by path or name patterns
    for spec in entity_specs:
        assigned = False
        
        # Check if part of an existing group based on name
        for group_name in list(groups.keys()):
            if group_name != "common" and (
                spec.entity_name.lower().startswith(group_name.lower()) or
                group_name.lower() in spec.entity_name.lower()
            ):
                groups[group_name].append(spec)
                assigned = True
                break
        
        if not assigned:
            # Extract potential group name from entity name
            name_parts = spec.entity_name.split('_')
            if len(name_parts) > 1 and len(name_parts[0]) > 3:
                group_name = name_parts[0].lower()
                if group_name not in groups:
                    groups[group_name] = []
                groups[group_name].append(spec)
                assigned = True
        
        if not assigned:
            # Add to common group
            groups["common"].append(spec)
    
    # If common group is too large, try to split it further using LLM
    if len(groups["common"]) > 5:
        try:
            refined_groups = refine_groups_with_llm(groups["common"])
            
            # Add refined groups
            for group_name, specs in refined_groups.items():
                if group_name != "common":
                    groups[group_name] = specs
            
            # Update common group to only include unassigned specs
            assigned_specs = [spec for group, specs in refined_groups.items() 
                             if group != "common" for spec in specs]
            groups["common"] = [spec for spec in groups["common"] 
                               if spec not in assigned_specs]
        except Exception as e:
            logger.error(f"Error refining groups with LLM: {str(e)}")
    
    # Remove empty groups
    return {group: specs for group, specs in groups.items() if specs}

def refine_groups_with_llm(specs: List[Specification]) -> Dict[str, List[Specification]]:
    """
    Use LLM to refine grouping of entities.
    
    Args:
        specs: List of Specification objects to group.
        
    Returns:
        Dictionary mapping group names to lists of Specification objects.
    """
    # Create a summary of the specifications
    specs_summary = []
    for spec in specs:
        summary = {
            "entity_name": spec.entity_name,
            "entity_type": spec.entity_type,
            "purpose": spec.purpose,
            "dependencies": spec.dependencies if spec.dependencies else []
        }
        specs_summary.append(summary)
    
    prompt = f"""
    You're given a list of code entities that need to be grouped by functionality or domain.
    Each entity has a name, type, purpose, and dependencies.
    
    Entities:
    ```json
    {json.dumps(specs_summary, indent=2)}
    ```
    
    Please identify logical groups for these entities based on their purpose and dependencies.
    Follow these guidelines:
    1. Create 2-6 groups
    2. Name each group based on its shared functionality
    3. Assign each entity to exactly one group
    4. Put entities that don't fit in any group in a "common" group
    
    Respond with a JSON object where:
    - Keys are group names
    - Values are arrays of entity names (strings, not objects) belonging to that group
    """
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            
            # Convert entity names back to specification objects
            grouped_specs = {}
            for group_name, entity_names in result.items():
                grouped_specs[group_name] = [
                    spec for spec in specs 
                    if spec.entity_name in entity_names
                ]
            
            return grouped_specs
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in group refinement response")
            return {"common": specs}
            
    except Exception as e:
        logger.error(f"Error using LLM to refine groups: {str(e)}")
        return {"common": specs}

def create_entity_implementation_step(spec: Specification) -> ImplementationStep:
    """
    Create an implementation step for a single entity.
    
    Args:
        spec: Specification object for the entity.
        
    Returns:
        ImplementationStep object.
    """
    validation_criteria = [
        f"Implementation matches {spec.entity_type} specification",
        "Code is well-structured and commented"
    ]
    
    # Add specific validation criteria based on entity type
    if spec.entity_type == 'class':
        validation_criteria.append("All methods are implemented correctly")
        validation_criteria.append("Class interfaces are consistent with specification")
    elif spec.entity_type == 'function':
        validation_criteria.append("Function handles all specified input cases")
        validation_criteria.append("Function produces correct output")
    elif spec.entity_type == 'module':
        validation_criteria.append("Module exports all required functionality")
        validation_criteria.append("Module dependencies are correctly imported")
    
    return ImplementationStep(
        id=f"{spec.entity_type}_{spec.entity_name}_{str(uuid.uuid4())[:8]}",
        description=f"Implement {spec.entity_type}: {spec.entity_name}",
        dependencies=[],  # Will be filled later
        expected_output=f"Implementation of {spec.entity_name} {spec.entity_type}",
        validation_criteria=validation_criteria
    )

def generate_pattern_steps(pattern_specs: List[Specification]) -> List[ImplementationStep]:
    """
    Generate implementation steps for design patterns.
    
    Args:
        pattern_specs: List of pattern Specification objects.
        
    Returns:
        List of ImplementationStep objects.
    """
    steps = []
    
    for spec in pattern_specs:
        pattern_step = ImplementationStep(
            id=f"pattern_{spec.entity_name}_{str(uuid.uuid4())[:8]}",
            description=f"Implement {spec.entity_name} pattern",
            dependencies=[],  # Will be filled later
            expected_output=f"Implementation of the {spec.entity_name} pattern",
            validation_criteria=[
                "Pattern implementation matches specification",
                "Components interact correctly according to pattern",
                "Pattern implementation follows best practices"
            ]
        )
        steps.append(pattern_step)
    
    return steps

def establish_step_dependencies(
    steps: List[ImplementationStep], 
    entity_steps_by_type: Dict[str, List[ImplementationStep]],
    specifications: List[Specification]
) -> Dict[str, List[str]]:
    """
    Establish dependencies between implementation steps.
    
    Args:
        steps: List of all ImplementationStep objects.
        entity_steps_by_type: Dictionary mapping entity types to their implementation steps.
        specifications: List of all Specification objects.
        
    Returns:
        Dictionary mapping step IDs to lists of dependency step IDs.
    """
    # Create mappings for easy lookup
    spec_by_name = {spec.entity_name: spec for spec in specifications}
    step_by_entity = {}
    
    for step in steps:
        # Extract entity name from step ID if possible
        parts = step.id.split('_')
        if len(parts) >= 3:
            entity_type = parts[0]
            # The entity name might contain underscores, so join appropriate parts
            entity_name = '_'.join(parts[1:-1])
            
            step_by_entity[(entity_type, entity_name)] = step
    
    # Initialize dependencies
    dependencies = {step.id: [] for step in steps}
    
    # Add dependencies based on architectural steps
    arch_steps = [step for step in steps if step.id.startswith(('setup_', 'arch_components_'))]
    if arch_steps:
        # All implementation steps depend on architectural setup
        for step in steps:
            if not step.id.startswith(('setup_', 'arch_components_')):
                for arch_step in arch_steps:
                    dependencies[step.id].append(arch_step.id)
    
    # Add dependencies based on entity dependencies
    for spec in specifications:
        # Find the step for this entity
        entity_step = None
        for key, step in step_by_entity.items():
            if key[0] == spec.entity_type and key[1] == spec.entity_name:
                entity_step = step
                break
        
        if entity_step and spec.dependencies:
            for dep_name in spec.dependencies:
                if dep_name in spec_by_name:
                    dep_spec = spec_by_name[dep_name]
                    
                    # Find the step for the dependency
                    dep_step = None
                    for key, step in step_by_entity.items():
                        if key[0] == dep_spec.entity_type and key[1] == dep_name:
                            dep_step = step
                            break
                    
                    if dep_step and dep_step.id not in dependencies[entity_step.id]:
                        dependencies[entity_step.id].append(dep_step.id)
    
    # Add dependencies for pattern steps
    pattern_steps = [step for step in steps if step.id.startswith('pattern_')]
    for step in pattern_steps:
        # Pattern implementation should generally come after entity implementations
        for entity_type, type_steps in entity_steps_by_type.items():
            for entity_step in type_steps:
                if entity_step.id not in dependencies[step.id]:
                    dependencies[step.id].append(entity_step.id)
    
    return dependencies

def calculate_execution_order(
    steps: List[ImplementationStep], 
    dependencies: Dict[str, List[str]]
) -> List[str]:
    """
    Calculate the execution order of steps using topological sort.
    
    Args:
        steps: List of all ImplementationStep objects.
        dependencies: Dictionary mapping step IDs to lists of dependency step IDs.
        
    Returns:
        List of step IDs in execution order.
    """
    # Create a directed graph
    graph = nx.DiGraph()
    
    # Add nodes
    for step in steps:
        graph.add_node(step.id)
    
    # Add edges (dependencies)
    for step_id, deps in dependencies.items():
        for dep_id in deps:
            graph.add_edge(dep_id, step_id)
    
    try:
        # Perform topological sort
        execution_order = list(nx.topological_sort(graph))
        return execution_order
    except nx.NetworkXUnfeasible:
        # Handle cycles in the dependency graph
        logger.warning("Cyclic dependencies detected in implementation steps")
        
        # Break cycles by finding strongly connected components
        components = list(nx.strongly_connected_components(graph))
        
        # Create a new graph with components as nodes
        component_graph = nx.DiGraph()
        
        # Map original nodes to component indices
        node_to_component = {}
        for i, component in enumerate(components):
            for node in component:
                node_to_component[node] = i
            component_graph.add_node(i)
        
        # Add edges between components
        for u, v in graph.edges():
            u_component = node_to_component[u]
            v_component = node_to_component[v]
            if u_component != v_component:
                component_graph.add_edge(u_component, v_component)
        
        # Perform topological sort on component graph
        component_order = list(nx.topological_sort(component_graph))
        
        # Convert back to node IDs
        execution_order = []
        for component_idx in component_order:
            # Add nodes from this component
            component_nodes = list(components[component_idx])
            
            # Sort nodes within component by ID for consistency
            component_nodes.sort()
            
            execution_order.extend(component_nodes)
        
        return execution_order

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
    
    strategy = generate_strategy(sample_specs)
    
    print("Generated Implementation Strategy:")
    print(f"Total steps: {len(strategy.steps)}")
    
    print("\nExecution order:")
    for step_id in strategy.execution_order:
        step = next((s for s in strategy.steps if s.id == step_id), None)
        if step:
            print(f"- {step.description}")
            print(f"  Dependencies: {strategy.dependencies[step.id]}")
