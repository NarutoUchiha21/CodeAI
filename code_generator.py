import logging
from typing import Dict, List, Any, Optional, Tuple
import os
import re
import json
from models import ImplementationStrategy, GeneratedFile, GeneratedCode, Specification
from openai import OpenAI
import uuid

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def generate_code(implementation_result: Dict[str, Any]) -> GeneratedCode:
    """
    Generate code based on implementation strategy and specifications.
    
    Args:
        implementation_result: Result from agent orchestrator with specifications
                              and implementation details.
        
    Returns:
        GeneratedCode object with the complete implementation.
    """
    logger.info("Generating code based on implementation results")
    
    specifications = implementation_result['specifications']
    implementation_details = implementation_result['implementation_details']
    file_structure = implementation_result['file_structure']
    
    # Generate files based on the file structure
    generated_files = []
    
    for file_info in file_structure:
        file_path = file_info['path']
        file_purpose = file_info['purpose']
        entity_specs = file_info['entities']
        
        # Get specifications for entities in this file
        file_specs = [spec for spec in specifications 
                     if spec.entity_name in entity_specs]
        
        # Generate file content
        file_content, derived_from = generate_file_content(
            file_path, 
            file_purpose, 
            file_specs, 
            implementation_details
        )
        
        # Create GeneratedFile object
        generated_file = GeneratedFile(
            path=file_path,
            content=file_content,
            purpose=file_purpose,
            derived_from=derived_from
        )
        
        generated_files.append(generated_file)
    
    # Calculate execution instructions
    execution_instructions = generate_execution_instructions(
        generated_files, 
        implementation_details.get('execution', {})
    )
    
    return GeneratedCode(
        files=generated_files,
        structure=file_structure,
        execution_instructions=execution_instructions
    )

def generate_file_content(
    file_path: str, 
    file_purpose: str,
    file_specs: List[Specification],
    implementation_details: Dict[str, Any]
) -> Tuple[str, List[str]]:
    """
    Generate content for a single file.
    
    Args:
        file_path: Path of the file to generate.
        file_purpose: Purpose of the file.
        file_specs: List of specifications for entities in this file.
        implementation_details: Implementation details from agent orchestrator.
        
    Returns:
        Tuple of (file_content, derived_from) where derived_from is a list of
        specification entity names this file was derived from.
    """
    # Extract file extension
    _, ext = os.path.splitext(file_path)
    
    # Determine language based on file extension
    language = determine_language(ext)
    
    # Get any existing implementation snippets for this file
    file_snippets = []
    for snippet in implementation_details.get('code_snippets', []):
        if snippet.get('file_path') == file_path:
            file_snippets.append(snippet.get('code', ''))
    
    # Extract entity names for tracking derived_from
    derived_from = [spec.entity_name for spec in file_specs]
    
    # Use existing snippets or generate new content
    if file_snippets:
        # Combine snippets into file content
        file_content = '\n\n'.join(file_snippets)
        
        # Add any missing imports or includes
        file_content = add_missing_imports(file_content, file_specs, language)
    else:
        # Generate content using LLM
        file_content = generate_file_with_llm(file_path, file_purpose, file_specs, language)
    
    # Add standard header comment
    header = generate_file_header(file_path, file_purpose, language)
    file_content = f"{header}\n\n{file_content}"
    
    return file_content, derived_from

def determine_language(extension: str) -> str:
    """
    Determine programming language based on file extension.
    
    Args:
        extension: File extension including the dot.
        
    Returns:
        Language name.
    """
    language_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.html': 'HTML',
        '.css': 'CSS',
        '.java': 'Java',
        '.c': 'C',
        '.cpp': 'C++',
        '.h': 'C/C++ Header',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.go': 'Go',
        '.rs': 'Rust',
    }
    
    return language_map.get(extension.lower(), 'Unknown')

def add_missing_imports(
    content: str, 
    specs: List[Specification],
    language: str
) -> str:
    """
    Add missing imports or includes to the file content.
    
    Args:
        content: Existing file content.
        specs: List of specifications for entities in this file.
        language: Programming language.
        
    Returns:
        Updated file content with imports.
    """
    # Collect dependencies from specs
    dependencies = []
    for spec in specs:
        if spec.dependencies:
            dependencies.extend(spec.dependencies)
    
    # Remove duplicates
    dependencies = list(set(dependencies))
    
    # Check if imports are already present
    if language == 'Python':
        # Check if import statements need to be added
        existing_imports = set(re.findall(r'(?:import|from)\s+([^\s\.]+)', content))
        needed_imports = [dep for dep in dependencies if dep not in existing_imports]
        
        if needed_imports:
            import_block = '\n'.join([f"import {dep}" for dep in needed_imports])
            
            # Add to the beginning of the file, after any existing imports
            if re.search(r'^import', content, re.MULTILINE):
                # Find the last import statement
                last_import = list(re.finditer(r'^(?:import|from)', content, re.MULTILINE))[-1]
                last_import_end = content.find('\n', last_import.start()) + 1
                
                # Insert after the last import
                content = content[:last_import_end] + import_block + '\n\n' + content[last_import_end:]
            else:
                # Add at the beginning
                content = import_block + '\n\n' + content
    
    elif language == 'JavaScript' or language == 'TypeScript':
        existing_imports = set(re.findall(r'(?:import|require)\s+[^\'\"]*[\'\"](.*?)[\'\"]\)?', content))
        needed_imports = [dep for dep in dependencies if dep not in existing_imports]
        
        if needed_imports:
            import_block = '\n'.join([f"import {dep} from '{dep}';" for dep in needed_imports])
            
            # Add to the beginning of the file, after any existing imports
            if re.search(r'^import', content, re.MULTILINE):
                # Find the last import statement
                last_import = list(re.finditer(r'^import', content, re.MULTILINE))[-1]
                last_import_end = content.find('\n', last_import.start()) + 1
                
                # Insert after the last import
                content = content[:last_import_end] + import_block + '\n\n' + content[last_import_end:]
            else:
                # Add at the beginning
                content = import_block + '\n\n' + content
    
    # Handle other languages as needed
    
    return content

def generate_file_header(file_path: str, file_purpose: str, language: str) -> str:
    """
    Generate a standard header comment for a file.
    
    Args:
        file_path: Path of the file.
        file_purpose: Purpose of the file.
        language: Programming language.
        
    Returns:
        Header comment string.
    """
    file_name = os.path.basename(file_path)
    
    header_content = [
        f"File: {file_name}",
        f"Purpose: {file_purpose}",
        f"Generated by Code Reverse-Engineering System"
    ]
    
    if language == 'Python':
        header = '"""' + '\n'.join(header_content) + '"""'
    elif language in ['JavaScript', 'TypeScript', 'Java', 'C', 'C++', 'PHP']:
        header = '/**\n' + '\n'.join([f' * {line}' for line in header_content]) + '\n */'
    elif language == 'HTML':
        header = '<!--\n' + '\n'.join(header_content) + '\n-->'
    elif language == 'CSS':
        header = '/*\n' + '\n'.join([f' * {line}' for line in header_content]) + '\n */'
    else:
        # Generic comment format
        header = '\n'.join([f'# {line}' for line in header_content])
    
    return header

def generate_file_with_llm(
    file_path: str, 
    file_purpose: str,
    file_specs: List[Specification],
    language: str
) -> str:
    """
    Generate file content using LLM.
    
    Args:
        file_path: Path of the file to generate.
        file_purpose: Purpose of the file.
        file_specs: List of specifications for entities in this file.
        language: Programming language.
        
    Returns:
        Generated file content.
    """
    # Prepare specifications for LLM
    specs_json = []
    for spec in file_specs:
        spec_dict = {
            "entity_name": spec.entity_name,
            "entity_type": spec.entity_type,
            "purpose": spec.purpose,
            "inputs": spec.inputs,
            "outputs": spec.outputs,
            "constraints": spec.constraints,
            "dependencies": spec.dependencies,
            "behavior": spec.behavior[:500] if spec.behavior else None  # Limit length
        }
        specs_json.append(spec_dict)
    
    file_name = os.path.basename(file_path)
    
    prompt = f"""
    You are an expert software developer. Your task is to generate code for a file in a software project
    based on specifications.
    
    File information:
    - File path: {file_path}
    - File name: {file_name}
    - Purpose: {file_purpose}
    - Language: {language}
    
    The file should implement the following specifications:
    ```json
    {json.dumps(specs_json, indent=2)}
    ```
    
    Requirements:
    1. Generate complete, production-quality code for the entire file
    2. Implement all specified entities according to their specifications
    3. Include all necessary imports/includes
    4. Add appropriate error handling
    5. Include comments explaining complex parts
    6. Follow best practices for {language}
    7. Ensure code is secure and free from common vulnerabilities
    
    Generate only the code content. Do not include any explanation or markdown formatting.
    Do not include the file header comment, as it will be added separately.
    """
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=4000,
        )
        
        generated_content = response.choices[0].message.content.strip()
        
        # Remove any markdown code block formatting if present
        generated_content = re.sub(r'^```\w*\n', '', generated_content)
        generated_content = re.sub(r'\n```$', '', generated_content)
        
        return generated_content
        
    except Exception as e:
        logger.error(f"Error generating file content using LLM: {str(e)}")
        # Return a placeholder with error information
        return f"""
# ERROR: Failed to generate content for {file_path}
# Error message: {str(e)}

# TODO: Implement the following entities:
{chr(10).join([f"# - {spec.entity_name} ({spec.entity_type}): {spec.purpose}" for spec in file_specs])}
"""

def generate_execution_instructions(
    files: List[GeneratedFile],
    execution_details: Dict[str, Any]
) -> str:
    """
    Generate instructions for running the implemented code.
    
    Args:
        files: List of generated files.
        execution_details: Details about how to execute the code.
        
    Returns:
        String with execution instructions.
    """
    # Find entry point files
    entry_points = []
    
    for file in files:
        # Look for common entry point patterns
        if (
            re.search(r'if\s+__name__\s*==\s*[\'"]__main__[\'"]', file.content) or
            file.path.endswith('main.py') or
            file.path.endswith('app.py') or
            file.path.endswith('index.js') or
            file.path.endswith('server.js')
        ):
            entry_points.append(file.path)
    
    # Use execution details if available, otherwise generate based on file analysis
    if execution_details:
        instructions = execution_details.get('instructions', '')
        if not instructions:
            instructions = generate_default_instructions(entry_points, files)
    else:
        instructions = generate_default_instructions(entry_points, files)
    
    return instructions

def generate_default_instructions(entry_points: List[str], files: List[GeneratedFile]) -> str:
    """
    Generate default execution instructions based on entry points.
    
    Args:
        entry_points: List of entry point file paths.
        files: List of all generated files.
        
    Returns:
        String with default execution instructions.
    """
    instructions = [
        "# Execution Instructions",
        "",
        "## Prerequisites",
        "Ensure you have all the required dependencies installed.",
        "",
    ]
    
    # Check for common dependency patterns
    python_imports = set()
    js_imports = set()
    
    for file in files:
        if file.path.endswith('.py'):
            # Extract Python imports
            imports = re.findall(r'^\s*import\s+(\w+)', file.content, re.MULTILINE)
            froms = re.findall(r'^\s*from\s+(\w+)', file.content, re.MULTILINE)
            python_imports.update(imports + froms)
        
        elif file.path.endswith(('.js', '.ts')):
            # Extract JS/TS imports
            imports = re.findall(r'^\s*import.*?from\s+[\'"]([^\'"./][^\'"]*)[\'"]', file.content, re.MULTILINE)
            requires = re.findall(r'^\s*(?:const|let|var).*?require\([\'"]([^\'"./][^\'"]*)[\'"]', file.content, re.MULTILINE)
            js_imports.update(imports + requires)
    
    # Add dependency instructions
    if python_imports:
        instructions.extend([
            "### Python Dependencies",
            "Install Python dependencies:",
            "```",
            "pip install " + " ".join(sorted(python_imports)),
            "```",
            ""
        ])
    
    if js_imports:
        instructions.extend([
            "### JavaScript Dependencies",
            "Install JavaScript dependencies:",
            "```",
            "npm install " + " ".join(sorted(js_imports)),
            "```",
            ""
        ])
    
    # Add execution steps
    instructions.append("## Running the Application")
    
    if entry_points:
        instructions.append("You can run the application using the following entry points:")
        
        for entry in sorted(entry_points):
            if entry.endswith('.py'):
                instructions.extend([
                    f"### Run {os.path.basename(entry)}",
                    "```",
                    f"python {entry}",
                    "```",
                    ""
                ])
            elif entry.endswith('.js'):
                instructions.extend([
                    f"### Run {os.path.basename(entry)}",
                    "```",
                    f"node {entry}",
                    "```",
                    ""
                ])
            elif entry.endswith('.ts'):
                instructions.extend([
                    f"### Run {os.path.basename(entry)}",
                    "```",
                    f"ts-node {entry}",
                    "```",
                    ""
                ])
    else:
        instructions.append("No clear entry point was identified. You may need to determine the appropriate way to run the application based on the generated files.")
    
    return "\n".join(instructions)

if __name__ == "__main__":
    # Test with sample implementation details
    sample_implementation = {
        'specifications': [
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
            )
        ],
        'implementation_details': {
            'code_snippets': []
        },
        'file_structure': [
            {
                'path': 'calculator.py',
                'purpose': 'Implements the Calculator class',
                'entities': ['Calculator']
            }
        ]
    }
    
    generated_code = generate_code(sample_implementation)
    
    print(f"Generated {len(generated_code.files)} files:")
    for file in generated_code.files:
        print(f"\n{file.path}:")
        print(file.content[:200] + "..." if len(file.content) > 200 else file.content)
    
    print("\nExecution Instructions:")
    print(generated_code.execution_instructions)
