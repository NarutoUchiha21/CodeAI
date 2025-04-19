import os
import logging
import re
from typing import Dict, List, Any, Tuple
import json
import ast
import astunparse
from models import CodeEntity, CodebaseAnalysis

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# File extensions to language mapping
LANGUAGE_EXTENSIONS = {
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

def analyze_codebase(codebase_path: str) -> CodebaseAnalysis:
    """
    Analyze a codebase and extract its structure, entities, and dependencies.
    
    Args:
        codebase_path: Path to the root directory of the codebase.
        
    Returns:
        CodebaseAnalysis object with the analysis results.
    """
    logger.info(f"Analyzing codebase at: {codebase_path}")
    
    # Initialize analysis results
    entities = []
    languages = {}
    dependencies = {}
    structure = {"directories": [], "files": []}
    metrics = {
        "total_files": 0,
        "total_lines": 0,
        "total_entities": 0,
        "complexity": {}
    }
    
    # Check if the path exists and is a directory
    if not os.path.exists(codebase_path):
        logger.error(f"Codebase path does not exist: {codebase_path}")
        return CodebaseAnalysis(
            entities=entities,
            languages=languages,
            dependencies=dependencies,
            structure=structure,
            metrics=metrics
        )
    
    if not os.path.isdir(codebase_path):
        logger.error(f"Codebase path is not a directory: {codebase_path}")
        return CodebaseAnalysis(
            entities=entities,
            languages=languages,
            dependencies=dependencies,
            structure=structure,
            metrics=metrics
        )
    
    # List of directories to skip
    skip_dirs = ['.git', 'node_modules', '__pycache__', '.hg', '.svn', '.venv', 'venv', 'env']
    
    # Walk through the codebase directory
    for root, dirs, files in os.walk(codebase_path):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        # Add current directory to structure
        rel_path = os.path.relpath(root, codebase_path)
        if rel_path != '.':
            structure["directories"].append(rel_path)
        
        for file in files:
            file_path = ''
            rel_file_path = ''
            try:
                file_path = os.path.join(root, file)
                rel_file_path = os.path.relpath(file_path, codebase_path)
                
                # Skip hidden files
                if file.startswith('.'):
                    continue
                    
                # Skip certain file patterns
                if any(pattern in file for pattern in ['.pyc', '.min.js', '.map']):
                    continue
                
                # Get file extension
                _, ext = os.path.splitext(file)
                language = LANGUAGE_EXTENSIONS.get(ext.lower(), 'Unknown')
                
                # Check if file exists and is a regular file
                if not os.path.exists(file_path) or not os.path.isfile(file_path):
                    logger.info(f"Skipping non-regular file: {rel_file_path}")
                    continue
                
                # Check file size first to avoid stat-ing large files
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > 1024 * 1024:  # 1MB
                        logger.info(f"Skipping large file: {rel_file_path} ({file_size} bytes)")
                        continue
                except (OSError, IOError) as e:
                    logger.warning(f"Error getting file size for {file_path}: {e}")
                    continue
                
                # Skip binary files
                if is_binary_file(file_path):
                    logger.info(f"Skipping binary file: {rel_file_path}")
                    continue
                
                structure["files"].append(rel_file_path)
                
                # Read file content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Count lines
                line_count = len(content.splitlines())
                metrics["total_lines"] += line_count
                metrics["total_files"] += 1
                
                # Update language statistics
                if language in languages:
                    languages[language] += line_count
                else:
                    languages[language] = line_count
                
                # Parse and analyze code based on language
                file_entities, file_dependencies = parse_file(rel_file_path, content, language)
                
                # Add entities and dependencies to results
                entities.extend(file_entities)
                dependencies.update(file_dependencies)
                
                # Update metrics
                metrics["total_entities"] += len(file_entities)
                
            except Exception as e:
                logger.error(f"Error analyzing file {file}: {str(e)}")
    
    # Calculate complexity metrics
    metrics["complexity"] = calculate_complexity(entities, dependencies)
    
    logger.info(f"Analysis complete. Found {len(entities)} entities in {metrics['total_files']} files.")
    
    return CodebaseAnalysis(
        entities=entities,
        languages=languages,
        dependencies=dependencies,
        structure=structure,
        metrics=metrics
    )

def is_binary_file(file_path: str) -> bool:
    """
    Check if a file is binary.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        True if the file is binary, False otherwise.
    """
    import stat
    import os
    
    # First check if it's a regular file (not a socket, FIFO, device, etc.)
    try:
        mode = os.stat(file_path).st_mode
        if not stat.S_ISREG(mode):
            # Skip non-regular files
            return True
    except (OSError, IOError):
        # If we can't stat the file, consider it binary/skip it
        return True
    
    # Try to read the file as text
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)  # Try to read as text
        return False
    except (UnicodeDecodeError, OSError, IOError):
        return True

def parse_file(file_path: str, content: str, language: str) -> Tuple[List[CodeEntity], Dict[str, List[str]]]:
    """
    Parse a file and extract code entities and dependencies.
    
    Args:
        file_path: Path to the file.
        content: Content of the file.
        language: Programming language of the file.
        
    Returns:
        Tuple of (entities, dependencies) where entities is a list of CodeEntity objects
        and dependencies is a dict mapping entity names to lists of dependency names.
    """
    entities = []
    dependencies = {}
    
    # Parse and extract entities based on language
    if language == 'Python':
        entities, dependencies = parse_python_file(file_path, content)
    elif language in ['JavaScript', 'TypeScript']:
        entities, dependencies = parse_js_ts_file(file_path, content)
    else:
        # Simple parsing for other languages
        entities, dependencies = parse_generic_file(file_path, content, language)
    
    return entities, dependencies

def parse_python_file(file_path: str, content: str) -> Tuple[List[CodeEntity], Dict[str, List[str]]]:
    """
    Parse a Python file using the ast module to extract entities and dependencies.
    
    Args:
        file_path: Path to the file.
        content: Content of the file.
        
    Returns:
        Tuple of (entities, dependencies).
    """
    entities = []
    dependencies = {}
    
    try:
        # Parse Python code using AST
        tree = ast.parse(content)
        
        # Extract imports
        file_imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    file_imports.append(name.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for name in node.names:
                    file_imports.append(f"{module}.{name.name}")
        
        # Extract classes and functions
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_entity = CodeEntity(
                    name=node.name,
                    type='class',
                    path=file_path,
                    code=astunparse.unparse(node),
                    dependencies=[],
                    metadata={
                        'docstring': ast.get_docstring(node),
                        'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                        'parent_classes': [base.id if isinstance(base, ast.Name) else astunparse.unparse(base).strip() for base in node.bases],
                    }
                )
                
                # Identify class dependencies
                class_deps = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        class_deps.append(base.id)
                
                entities.append(class_entity)
                dependencies[node.name] = class_deps
            
            elif isinstance(node, ast.FunctionDef):
                func_entity = CodeEntity(
                    name=node.name,
                    type='function',
                    path=file_path,
                    code=astunparse.unparse(node),
                    dependencies=[],
                    metadata={
                        'docstring': ast.get_docstring(node),
                        'args': [arg.arg for arg in node.args.args],
                        'returns': extract_return_type(node),
                    }
                )
                
                # Identify function dependencies
                func_deps = []
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Call) and isinstance(subnode.func, ast.Name):
                        func_deps.append(subnode.func.id)
                
                entities.append(func_entity)
                dependencies[node.name] = func_deps
        
        # Add the module itself as an entity
        module_name = os.path.basename(file_path).split('.')[0]
        module_entity = CodeEntity(
            name=module_name,
            type='module',
            path=file_path,
            code=content,
            dependencies=file_imports,
            metadata={
                'docstring': ast.get_docstring(tree),
            }
        )
        entities.append(module_entity)
        dependencies[module_name] = file_imports
        
    except SyntaxError as e:
        logger.error(f"Syntax error in Python file {file_path}: {str(e)}")
        # Add the file as an entity even if parsing failed
        module_name = os.path.basename(file_path).split('.')[0]
        module_entity = CodeEntity(
            name=module_name,
            type='module',
            path=file_path,
            code=content,
            dependencies=[],
            metadata={
                'parse_error': str(e),
            }
        )
        entities.append(module_entity)
    
    return entities, dependencies

def extract_return_type(func_node: ast.FunctionDef) -> str:
    """Extract return type hint from a function definition."""
    if func_node.returns:
        return astunparse.unparse(func_node.returns).strip()
    return "None"

def parse_js_ts_file(file_path: str, content: str) -> Tuple[List[CodeEntity], Dict[str, List[str]]]:
    """
    Parse a JavaScript or TypeScript file to extract entities and dependencies.
    
    Args:
        file_path: Path to the file.
        content: Content of the file.
        
    Returns:
        Tuple of (entities, dependencies).
    """
    entities = []
    dependencies = {}
    
    # Simple regex-based extraction for JS/TS
    # In a production system, you would use a proper JS/TS parser
    
    # Extract imports
    imports = []
    import_pattern = r'import\s+(?:{[^}]*}|[^{]*)\s+from\s+[\'"]([^\'"]+)[\'"]'
    for match in re.finditer(import_pattern, content):
        imports.append(match.group(1))
    
    require_pattern = r'(?:const|let|var)\s+([^\s=]+)\s*=\s*require\([\'"]([^\'"]+)[\'"]\)'
    for match in re.finditer(require_pattern, content):
        variable_name = match.group(1)
        module_name = match.group(2)
        imports.append(module_name)
    
    # Extract classes
    class_pattern = r'class\s+([A-Za-z0-9_$]+)(?:\s+extends\s+([A-Za-z0-9_$.]+))?\s*{'
    for match in re.finditer(class_pattern, content):
        class_name = match.group(1)
        parent_class = match.group(2)
        
        # Find class bounds
        start_pos = match.start()
        # This is a simplification - proper parsing needs to account for nested braces
        class_content = extract_block_content(content, start_pos)
        
        class_entity = CodeEntity(
            name=class_name,
            type='class',
            path=file_path,
            code=class_content,
            dependencies=[parent_class] if parent_class else [],
            metadata={
                'parent_class': parent_class,
                'methods': extract_methods(class_content),
            }
        )
        
        entities.append(class_entity)
        dependencies[class_name] = [parent_class] if parent_class else []
    
    # Extract functions
    function_pattern = r'(?:function|async function)\s+([A-Za-z0-9_$]+)\s*\([^)]*\)\s*{'
    for match in re.finditer(function_pattern, content):
        func_name = match.group(1)
        start_pos = match.start()
        func_content = extract_block_content(content, start_pos)
        
        func_entity = CodeEntity(
            name=func_name,
            type='function',
            path=file_path,
            code=func_content,
            dependencies=[],
            metadata={}
        )
        
        entities.append(func_entity)
        # Function dependencies would require more complex analysis
        dependencies[func_name] = []
    
    # Extract arrow functions assigned to variables
    arrow_func_pattern = r'(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:\([^)]*\)|[^=]*)\s*=>\s*'
    for match in re.finditer(arrow_func_pattern, content):
        func_name = match.group(1)
        start_pos = match.start()
        # For arrow functions, content extraction is more complex
        # This is a simplification
        end_pos = find_statement_end(content, start_pos)
        func_content = content[start_pos:end_pos]
        
        func_entity = CodeEntity(
            name=func_name,
            type='function',
            path=file_path,
            code=func_content,
            dependencies=[],
            metadata={
                'arrow_function': True
            }
        )
        
        entities.append(func_entity)
        dependencies[func_name] = []
    
    # Add the module itself as an entity
    module_name = os.path.basename(file_path).split('.')[0]
    module_entity = CodeEntity(
        name=module_name,
        type='module',
        path=file_path,
        code=content,
        dependencies=imports,
        metadata={}
    )
    entities.append(module_entity)
    dependencies[module_name] = imports
    
    return entities, dependencies

def extract_block_content(content: str, start_pos: int) -> str:
    """Extract content of a code block (between { and }) starting from start_pos."""
    brace_count = 0
    in_block = False
    end_pos = start_pos
    
    for i in range(start_pos, len(content)):
        if content[i] == '{':
            brace_count += 1
            in_block = True
        elif content[i] == '}':
            brace_count -= 1
        
        if in_block and brace_count == 0:
            end_pos = i + 1
            break
    
    return content[start_pos:end_pos]

def find_statement_end(content: str, start_pos: int) -> int:
    """Find the end position of a statement starting from start_pos."""
    for i in range(start_pos, len(content)):
        if content[i] == ';' or content[i] == '\n':
            return i + 1
    
    return len(content)

def extract_methods(class_content: str) -> List[str]:
    """Extract method names from class content."""
    methods = []
    method_pattern = r'(?:async\s+)?([A-Za-z0-9_$]+)\s*\([^)]*\)\s*{'
    for match in re.finditer(method_pattern, class_content):
        method_name = match.group(1)
        if method_name not in ['constructor', 'class']:
            methods.append(method_name)
    
    return methods

def parse_generic_file(file_path: str, content: str, language: str) -> Tuple[List[CodeEntity], Dict[str, List[str]]]:
    """
    Generic parsing for languages without specific parsers.
    
    Args:
        file_path: Path to the file.
        content: Content of the file.
        language: Programming language of the file.
        
    Returns:
        Tuple of (entities, dependencies).
    """
    entities = []
    dependencies = {}
    
    # Just add the file as a single entity
    file_name = os.path.basename(file_path)
    file_entity = CodeEntity(
        name=file_name,
        type='file',
        path=file_path,
        code=content,
        dependencies=[],
        metadata={
            'language': language,
            'size': len(content),
        }
    )
    
    entities.append(file_entity)
    dependencies[file_name] = []
    
    return entities, dependencies

def calculate_complexity(entities: List[CodeEntity], dependencies: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Calculate complexity metrics for the codebase.
    
    Args:
        entities: List of code entities.
        dependencies: Map of entity dependencies.
        
    Returns:
        Dictionary of complexity metrics.
    """
    complexity = {
        "cyclomatic_complexity": {},
        "dependency_complexity": len(dependencies),
        "cohesion": {},
        "coupling": {},
    }
    
    # Simple cyclomatic complexity estimate
    for entity in entities:
        if entity.type in ['function', 'method']:
            # Count decision points (if, for, while, etc.)
            decision_points = (
                content_count(entity.code, "if ") +
                content_count(entity.code, "for ") +
                content_count(entity.code, "while ") +
                content_count(entity.code, "case ") +
                content_count(entity.code, "&&") +
                content_count(entity.code, "||")
            )
            complexity["cyclomatic_complexity"][entity.name] = 1 + decision_points
    
    # Calculate coupling metrics
    entity_names = [e.name for e in entities]
    for name, deps in dependencies.items():
        valid_deps = [d for d in deps if d in entity_names]
        complexity["coupling"][name] = len(valid_deps)
    
    return complexity

def content_count(content: str, substring: str) -> int:
    """Count occurrences of a substring in content."""
    return content.count(substring)

if __name__ == "__main__":
    # Test the analyzer on a sample codebase
    import sys
    if len(sys.argv) > 1:
        codebase_path = sys.argv[1]
        analysis = analyze_codebase(codebase_path)
        print(f"Analyzed {len(analysis.entities)} entities in {analysis.metrics['total_files']} files")
        print(f"Languages: {analysis.languages}")
