import logging
from typing import Dict, List, Any, Optional
import re
from models import CodeEntity, CodebaseAnalysis, Specification
from openai import OpenAI
import os
import json

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def extract_specifications(analysis: CodebaseAnalysis) -> List[Specification]:
    """
    Extract specifications from code analysis results.
    
    Args:
        analysis: CodebaseAnalysis object with analysis results.
        
    Returns:
        List of Specification objects.
    """
    logger.info("Extracting specifications from analysis results")
    
    specifications = []
    
    # Group entities by type
    entity_types = {}
    for entity in analysis.entities:
        if entity.type not in entity_types:
            entity_types[entity.type] = []
        entity_types[entity.type].append(entity)
    
    # Process each type of entity
    for entity_type, entities in entity_types.items():
        logger.info(f"Processing {len(entities)} entities of type '{entity_type}'")
        
        # Process each entity
        for entity in entities:
            # Extract specification based on entity type
            if entity_type == 'module':
                spec = extract_module_specification(entity, analysis)
            elif entity_type == 'class':
                spec = extract_class_specification(entity, analysis)
            elif entity_type == 'function':
                spec = extract_function_specification(entity, analysis)
            else:
                spec = extract_generic_specification(entity, analysis)
            
            if spec:
                specifications.append(spec)
    
    # Extract high-level architectural specifications
    arch_specs = extract_architectural_specifications(analysis)
    specifications.extend(arch_specs)
    
    logger.info(f"Extracted {len(specifications)} specifications")
    return specifications

def extract_module_specification(entity: CodeEntity, analysis: CodebaseAnalysis) -> Optional[Specification]:
    """
    Extract specification for a module.
    
    Args:
        entity: CodeEntity representing the module.
        analysis: Complete CodebaseAnalysis object.
        
    Returns:
        Specification object or None if extraction fails.
    """
    try:
        # First try to extract from docstring or comments
        purpose = extract_purpose_from_docstring(entity)
        
        if not purpose:
            # Use LLM to infer purpose from code
            purpose = infer_purpose_from_code(entity)
        
        # Extract dependencies from analysis
        dependencies = analysis.dependencies.get(entity.name, [])
        
        # Create specification
        spec = Specification(
            entity_name=entity.name,
            entity_type='module',
            purpose=purpose,
            inputs=None,  # Modules don't have direct inputs
            outputs=None,  # Modules don't have direct outputs
            constraints=extract_constraints(entity),
            dependencies=dependencies,
            behavior=extract_behavior_description(entity),
            examples=None
        )
        
        return spec
    
    except Exception as e:
        logger.error(f"Error extracting specification for module {entity.name}: {str(e)}")
        return None

def extract_class_specification(entity: CodeEntity, analysis: CodebaseAnalysis) -> Optional[Specification]:
    """
    Extract specification for a class.
    
    Args:
        entity: CodeEntity representing the class.
        analysis: Complete CodebaseAnalysis object.
        
    Returns:
        Specification object or None if extraction fails.
    """
    try:
        # Extract purpose
        purpose = extract_purpose_from_docstring(entity)
        
        if not purpose:
            purpose = infer_purpose_from_code(entity)
        
        # Extract inputs (constructor parameters)
        inputs = extract_constructor_params(entity)
        
        # Extract outputs (public methods and properties)
        outputs = extract_class_outputs(entity)
        
        # Extract dependencies
        dependencies = analysis.dependencies.get(entity.name, [])
        
        # Create specification
        spec = Specification(
            entity_name=entity.name,
            entity_type='class',
            purpose=purpose,
            inputs=inputs,
            outputs=outputs,
            constraints=extract_constraints(entity),
            dependencies=dependencies,
            behavior=extract_behavior_description(entity),
            examples=extract_examples(entity)
        )
        
        return spec
    
    except Exception as e:
        logger.error(f"Error extracting specification for class {entity.name}: {str(e)}")
        return None

def extract_function_specification(entity: CodeEntity, analysis: CodebaseAnalysis) -> Optional[Specification]:
    """
    Extract specification for a function.
    
    Args:
        entity: CodeEntity representing the function.
        analysis: Complete CodebaseAnalysis object.
        
    Returns:
        Specification object or None if extraction fails.
    """
    try:
        # Extract purpose
        purpose = extract_purpose_from_docstring(entity)
        
        if not purpose:
            purpose = infer_purpose_from_code(entity)
        
        # Extract inputs (parameters)
        inputs = []
        if 'args' in entity.metadata:
            for arg in entity.metadata['args']:
                inputs.append({'name': arg, 'type': 'unknown'})
        
        # Extract outputs (return value)
        outputs = []
        if 'returns' in entity.metadata:
            outputs.append({'type': entity.metadata['returns']})
        
        # Extract dependencies
        dependencies = analysis.dependencies.get(entity.name, [])
        
        # Create specification
        spec = Specification(
            entity_name=entity.name,
            entity_type='function',
            purpose=purpose,
            inputs=inputs,
            outputs=outputs,
            constraints=extract_constraints(entity),
            dependencies=dependencies,
            behavior=extract_behavior_description(entity),
            examples=extract_examples(entity)
        )
        
        return spec
    
    except Exception as e:
        logger.error(f"Error extracting specification for function {entity.name}: {str(e)}")
        return None

def extract_generic_specification(entity: CodeEntity, analysis: CodebaseAnalysis) -> Optional[Specification]:
    """
    Extract specification for a generic entity.
    
    Args:
        entity: CodeEntity to extract specification from.
        analysis: Complete CodebaseAnalysis object.
        
    Returns:
        Specification object or None if extraction fails.
    """
    try:
        # Extract purpose
        purpose = extract_purpose_from_docstring(entity)
        
        if not purpose:
            purpose = infer_purpose_from_code(entity)
        
        # Extract dependencies
        dependencies = analysis.dependencies.get(entity.name, [])
        
        # Create specification
        spec = Specification(
            entity_name=entity.name,
            entity_type=entity.type,
            purpose=purpose,
            inputs=None,
            outputs=None,
            constraints=extract_constraints(entity),
            dependencies=dependencies,
            behavior=extract_behavior_description(entity),
            examples=None
        )
        
        return spec
    
    except Exception as e:
        logger.error(f"Error extracting specification for {entity.type} {entity.name}: {str(e)}")
        return None

def extract_architectural_specifications(analysis: CodebaseAnalysis) -> List[Specification]:
    """
    Extract high-level architectural specifications from the codebase.
    
    Args:
        analysis: CodebaseAnalysis object.
        
    Returns:
        List of architectural Specification objects.
    """
    specs = []
    
    try:
        # Use LLM to extract architectural specifications
        modules = [e for e in analysis.entities if e.type == 'module']
        classes = [e for e in analysis.entities if e.type == 'class']
        
        # Only proceed if we have enough entities for architectural analysis
        if len(modules) > 2 or len(classes) > 5:
            # Create a summary of the codebase structure
            structure_summary = {
                'modules': [{'name': m.name, 'path': m.path} for m in modules],
                'classes': [{'name': c.name, 'path': c.path} for c in classes],
                'dependencies': analysis.dependencies,
                'languages': analysis.languages,
            }
            
            # Use LLM to infer architecture
            architecture = infer_architecture(structure_summary)
            
            # Create architectural specification
            arch_spec = Specification(
                entity_name='architecture',
                entity_type='architecture',
                purpose=architecture.get('purpose', 'Overall architecture of the system'),
                inputs=None,
                outputs=None,
                constraints=architecture.get('constraints', []),
                dependencies=None,
                behavior=architecture.get('description', ''),
                examples=None
            )
            
            specs.append(arch_spec)
            
            # Add pattern specifications if any
            for pattern in architecture.get('patterns', []):
                pattern_spec = Specification(
                    entity_name=f"pattern_{pattern['name']}",
                    entity_type='pattern',
                    purpose=pattern.get('purpose', f"Implementation of {pattern['name']} pattern"),
                    inputs=None,
                    outputs=None,
                    constraints=pattern.get('constraints', []),
                    dependencies=pattern.get('components', []),
                    behavior=pattern.get('description', ''),
                    examples=None
                )
                
                specs.append(pattern_spec)
    
    except Exception as e:
        logger.error(f"Error extracting architectural specifications: {str(e)}")
    
    return specs

def extract_purpose_from_docstring(entity: CodeEntity) -> str:
    """
    Extract purpose description from entity docstring.
    
    Args:
        entity: CodeEntity to extract purpose from.
        
    Returns:
        Purpose description or empty string if not found.
    """
    if 'docstring' in entity.metadata and entity.metadata['docstring']:
        # Extract first paragraph of docstring
        docstring = entity.metadata['docstring']
        first_para = docstring.split('\n\n')[0].strip()
        return first_para
    
    # Try to find a comment at the start of the code
    lines = entity.code.split('\n')
    comment_lines = []
    for line in lines:
        line = line.strip()
        if line.startswith('//') or line.startswith('#'):
            comment_lines.append(line[2:].strip())
        elif line.startswith('/*') or line.startswith('"""'):
            break
        elif not line.startswith(('import', 'from', 'package', 'using')) and not line == '':
            break
    
    if comment_lines:
        return ' '.join(comment_lines)
    
    return ""

def infer_purpose_from_code(entity: CodeEntity) -> str:
    """
    Use LLM to infer purpose from code.
    
    Args:
        entity: CodeEntity to infer purpose for.
        
    Returns:
        Inferred purpose description.
    """
    prompt = f"""
    You're analyzing a code entity. Please infer the purpose of this {entity.type} from its code:
    
    Entity name: {entity.name}
    Entity type: {entity.type}
    
    ```
    {entity.code[:4000]}  # Truncate to avoid token limits
    ```
    
    Please respond with a concise 1-2 sentence description of the purpose of this {entity.type}.
    Focus on what it does, not how it does it. Just provide the description without additional text.
    """
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.3,
        )
        purpose = response.choices[0].message.content.strip()
        return purpose
    except Exception as e:
        logger.error(f"Error inferring purpose using LLM: {str(e)}")
        return f"Purpose of {entity.name} (inferred from code structure)"

def extract_constructor_params(entity: CodeEntity) -> List[Dict[str, str]]:
    """
    Extract constructor parameters from a class entity.
    
    Args:
        entity: CodeEntity representing a class.
        
    Returns:
        List of parameter dictionaries with name and type.
    """
    params = []
    
    # Look for constructor in the code
    lines = entity.code.split('\n')
    in_constructor = False
    constructor_def = ""
    
    for line in lines:
        if re.search(r'(constructor|__init__)\s*\(', line):
            in_constructor = True
            constructor_def += line
        elif in_constructor and ')' in line:
            constructor_def += line
            break
        elif in_constructor:
            constructor_def += line
    
    if constructor_def:
        # Extract parameters
        param_match = re.search(r'\((.*?)\)', constructor_def)
        if param_match:
            param_str = param_match.group(1)
            
            # Handle 'self' or 'this' in different languages
            param_str = re.sub(r'^(self|this),\s*', '', param_str)
            
            # Split parameters
            if param_str.strip():
                param_list = [p.strip() for p in param_str.split(',')]
                for param in param_list:
                    # Try to extract type information
                    type_match = re.search(r':\s*([A-Za-z0-9_<>[\]]+)', param)
                    type_info = type_match.group(1) if type_match else 'unknown'
                    
                    # Extract parameter name
                    name_match = re.search(r'([A-Za-z0-9_]+)', param)
                    if name_match:
                        params.append({
                            'name': name_match.group(1),
                            'type': type_info
                        })
    
    return params

def extract_class_outputs(entity: CodeEntity) -> List[Dict[str, str]]:
    """
    Extract public methods and properties from a class entity.
    
    Args:
        entity: CodeEntity representing a class.
        
    Returns:
        List of output dictionaries with name and type.
    """
    outputs = []
    
    # Extract methods
    if 'methods' in entity.metadata:
        for method in entity.metadata['methods']:
            # Skip private methods (starting with _ or __)
            if not method.startswith('_'):
                outputs.append({
                    'name': method,
                    'type': 'method'
                })
    
    # Try to extract properties
    lines = entity.code.split('\n')
    for line in lines:
        # Property patterns for different languages
        python_prop = re.search(r'@property\s+def\s+([A-Za-z0-9_]+)', line)
        js_prop = re.search(r'get\s+([A-Za-z0-9_]+)\s*\(', line)
        
        if python_prop:
            outputs.append({
                'name': python_prop.group(1),
                'type': 'property'
            })
        elif js_prop:
            outputs.append({
                'name': js_prop.group(1),
                'type': 'property'
            })
    
    return outputs

def extract_constraints(entity: CodeEntity) -> List[str]:
    """
    Extract constraints from entity code.
    
    Args:
        entity: CodeEntity to extract constraints from.
        
    Returns:
        List of constraint descriptions.
    """
    constraints = []
    
    # Look for validation code
    code = entity.code
    
    # Check for assertions
    assertions = re.findall(r'assert\s+(.+?)(?:,|\)|\n)', code)
    for assertion in assertions:
        constraints.append(f"Must satisfy: {assertion.strip()}")
    
    # Check for validation statements
    validations = []
    
    # if/raise pattern
    if_raises = re.findall(r'if\s+(.+?):\s*\n\s*raise', code, re.MULTILINE)
    for condition in if_raises:
        validations.append(f"Must not: {condition.strip()}")
    
    # Explicit validation functions
    validation_calls = re.findall(r'(?:validate|check|ensure|require)\w*\((.+?)\)', code)
    for call in validation_calls:
        validations.append(f"Validates: {call.strip()}")
    
    constraints.extend(validations)
    
    # If no constraints found and it's a complex entity, use LLM
    if not constraints and len(code.split('\n')) > 10:
        inferred = infer_constraints(entity)
        constraints.extend(inferred)
    
    return constraints

def infer_constraints(entity: CodeEntity) -> List[str]:
    """
    Use LLM to infer constraints from code.
    
    Args:
        entity: CodeEntity to infer constraints for.
        
    Returns:
        List of inferred constraints.
    """
    prompt = f"""
    You're analyzing a code entity to identify constraints and requirements. 
    Please infer any constraints or validation requirements for this {entity.type}:
    
    Entity name: {entity.name}
    Entity type: {entity.type}
    
    ```
    {entity.code[:4000]}  # Truncate to avoid token limits
    ```
    
    Please identify:
    1. Input validation requirements
    2. State constraints
    3. Pre/post conditions
    4. Exception conditions
    5. Resource requirements
    
    Format each constraint as a single sentence starting with "Must" or "Should".
    Respond with a JSON array of strings, with each string being a constraint.
    """
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            if isinstance(result, dict) and 'constraints' in result:
                return result['constraints']
            elif isinstance(result, list):
                return result
            else:
                # Handle unexpected format
                text_response = response.choices[0].message.content
                # Try to extract list-like structures
                constraints = re.findall(r'"([^"]+)"', text_response)
                if constraints:
                    return constraints
                else:
                    return ["Must satisfy implicit constraints (inferred from code)"]
        except json.JSONDecodeError:
            # If not valid JSON, try to parse as text
            text_response = response.choices[0].message.content
            lines = [line.strip() for line in text_response.split('\n') if line.strip()]
            constraints = [line for line in lines if line.startswith(('Must', 'Should'))]
            return constraints if constraints else ["Must satisfy implicit constraints (inferred from code)"]
            
    except Exception as e:
        logger.error(f"Error inferring constraints using LLM: {str(e)}")
        return []

def extract_behavior_description(entity: CodeEntity) -> str:
    """
    Extract or infer behavior description for an entity.
    
    Args:
        entity: CodeEntity to describe.
        
    Returns:
        Behavior description.
    """
    # For simple entities, derive from code structure
    if len(entity.code.split('\n')) < 10:
        return derive_behavior_from_structure(entity)
    
    # For complex entities, use LLM
    return infer_behavior(entity)

def derive_behavior_from_structure(entity: CodeEntity) -> str:
    """
    Derive behavior description from code structure for simple entities.
    
    Args:
        entity: CodeEntity to describe.
        
    Returns:
        Behavior description.
    """
    code = entity.code
    lines = code.split('\n')
    
    if entity.type == 'function':
        return f"Function that {entity.name.replace('_', ' ')}s"
    
    elif entity.type == 'class':
        methods = entity.metadata.get('methods', [])
        method_text = ', '.join(methods[:5])
        if len(methods) > 5:
            method_text += f", and {len(methods) - 5} more methods"
        
        return f"Class that implements {method_text}"
    
    elif entity.type == 'module':
        return f"Module containing {len(lines)} lines of code"
    
    return f"{entity.type.capitalize()} implementing {entity.name} functionality"

def infer_behavior(entity: CodeEntity) -> str:
    """
    Use LLM to infer behavior description from code.
    
    Args:
        entity: CodeEntity to describe.
        
    Returns:
        Inferred behavior description.
    """
    prompt = f"""
    You're analyzing a code entity. Please describe the behavior of this {entity.type} in detail:
    
    Entity name: {entity.name}
    Entity type: {entity.type}
    
    ```
    {entity.code[:4000]}  # Truncate to avoid token limits
    ```
    
    Please provide a detailed description of:
    1. What this code does
    2. How it works (algorithm/approach)
    3. Key features and behaviors
    
    Keep the description technical but understandable. Focus on behaviors, not implementation details.
    Write 2-4 paragraphs.
    """
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.3,
        )
        behavior = response.choices[0].message.content.strip()
        return behavior
    except Exception as e:
        logger.error(f"Error inferring behavior using LLM: {str(e)}")
        return f"The {entity.name} {entity.type} implements functionality as described in the code."

def extract_examples(entity: CodeEntity) -> Optional[List[Dict[str, Any]]]:
    """
    Extract examples from entity code or comments.
    
    Args:
        entity: CodeEntity to extract examples from.
        
    Returns:
        List of example dictionaries or None if no examples found.
    """
    examples = []
    
    # Look for examples in docstring
    if 'docstring' in entity.metadata and entity.metadata['docstring']:
        docstring = entity.metadata['docstring']
        
        # Look for example sections
        example_sections = re.findall(r'(?:Examples?|Usage):\s*\n(.*?)(?:\n\n|\Z)', 
                                     docstring, re.DOTALL)
        
        for section in example_sections:
            # Extract code blocks
            code_blocks = re.findall(r'```(?:\w+)?\s*\n(.*?)\n```', section, re.DOTALL)
            
            if code_blocks:
                for block in code_blocks:
                    examples.append({
                        'type': 'code',
                        'content': block.strip()
                    })
            else:
                # If no code blocks, use the whole section
                examples.append({
                    'type': 'text',
                    'content': section.strip()
                })
    
    # If no examples found, leave as None
    return examples if examples else None

def infer_architecture(structure_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use LLM to infer architectural specifications from codebase structure.
    
    Args:
        structure_summary: Dictionary summarizing codebase structure.
        
    Returns:
        Dictionary with architectural specifications.
    """
    # Convert structure summary to JSON
    structure_json = json.dumps(structure_summary, indent=2)
    
    prompt = f"""
    You're analyzing a codebase structure to infer its architecture. Please review this structure:
    
    ```json
    {structure_json}
    ```
    
    Based on this information, please infer the architecture of the system. Include:
    
    1. The overall purpose of the system
    2. The architectural patterns used
    3. Key components and their relationships
    4. Any constraints or design principles evident in the code
    
    Respond with a JSON object in this format:
    {{
        "purpose": "Overall purpose of the system",
        "description": "Detailed description of the architecture",
        "patterns": [
            {{
                "name": "Pattern name",
                "purpose": "What this pattern achieves",
                "components": ["component1", "component2"],
                "description": "How the pattern is implemented",
                "constraints": ["constraint1", "constraint2"]
            }}
        ],
        "constraints": ["constraint1", "constraint2"]
    }}
    """
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        logger.error(f"Error inferring architecture using LLM: {str(e)}")
        # Return a default architecture description
        return {
            "purpose": "Software system architecture",
            "description": "A software system with multiple components",
            "patterns": [],
            "constraints": []
        }