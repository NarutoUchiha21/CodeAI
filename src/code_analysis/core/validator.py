"""
File: validator.py
Purpose: Validates the re-implemented code against the original codebase
Generated by Code Reverse-Engineering System
"""

import logging
import os
import re
import difflib
import json
from typing import Dict, List, Any, Optional, Tuple
import ast
import astunparse
from models import GeneratedCode, ValidationResult

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def validate_implementation(original_path: str, generated_code: GeneratedCode) -> ValidationResult:
    """
    Validate the re-implemented code against the original codebase.
    
    Args:
        original_path: Path to the original codebase.
        generated_code: GeneratedCode object with the re-implementation.
        
    Returns:
        ValidationResult object with validation results.
    """
    logger.info(f"Validating implementation against original codebase at: {original_path}")
    
    # Step 1: Map generated files to original files
    file_mapping = map_generated_to_original(original_path, generated_code)
    
    # Step 2: Validate functionality
    functional_results = validate_functionality(original_path, generated_code, file_mapping)
    
    # Step 3: Validate structure
    structural_results = validate_structure(original_path, generated_code)
    
    # Step 4: Identify missing and additional features
    missing_features, additional_features = identify_feature_differences(
        original_path, generated_code, file_mapping
    )
    
    # Calculate overall success based on validation results
    success = (functional_results['equivalence'] > 70.0 and 
               structural_results['similarity'] > 60.0 and
               len(missing_features) < 5)
    
    # Collect all validation details
    validation_details = {
        "file_comparison": functional_results['file_comparison'],
        "structural_comparison": structural_results['details'],
        "missing_feature_details": functional_results['missing_details'],
        "additional_feature_details": functional_results['additional_details']
    }
    
    logger.info(f"Validation complete. Success: {success}")
    logger.info(f"Functional equivalence: {functional_results['equivalence']}%")
    logger.info(f"Structural similarity: {structural_results['similarity']}%")
    
    return ValidationResult(
        success=success,
        functional_equivalence=functional_results['equivalence'],
        structural_similarity=structural_results['similarity'],
        missing_features=missing_features,
        additional_features=additional_features,
        error_details=validation_details
    )

def map_generated_to_original(original_path: str, generated_code: GeneratedCode) -> Dict[str, str]:
    """
    Map generated files to their corresponding original files.
    
    Args:
        original_path: Path to the original codebase.
        generated_code: GeneratedCode object with the re-implementation.
        
    Returns:
        Dictionary mapping generated file paths to original file paths.
    """
    file_mapping = {}
    
    # Get list of all files in the original codebase
    original_files = []
    for root, _, files in os.walk(original_path):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, original_path)
            
            # Skip non-text files and hidden files
            if not is_text_file(file_path) or file.startswith('.'):
                continue
                
            original_files.append(rel_path)
    
    # Map generated files to original files based on path similarity and content similarity
    for gen_file in generated_code.files:
        gen_rel_path = gen_file.path
        
        # Try exact path match first
        if gen_rel_path in original_files:
            file_mapping[gen_rel_path] = gen_rel_path
            continue
        
        # Try filename match
        gen_filename = os.path.basename(gen_rel_path)
        filename_matches = [of for of in original_files if os.path.basename(of) == gen_filename]
        
        if len(filename_matches) == 1:
            # Single match by filename
            file_mapping[gen_rel_path] = filename_matches[0]
            continue
        elif len(filename_matches) > 1:
            # Multiple matches by filename, find the best one based on path similarity
            best_match = find_best_path_match(gen_rel_path, filename_matches)
            file_mapping[gen_rel_path] = best_match
            continue
        
        # Try content-based matching for remaining files
        best_match = find_best_content_match(gen_file.content, original_path, original_files)
        if best_match:
            file_mapping[gen_rel_path] = best_match
    
    return file_mapping

def is_text_file(file_path: str) -> bool:
    """
    Check if a file is a text file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        True if the file is a text file, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(4096)
        return True
    except UnicodeDecodeError:
        return False

def find_best_path_match(gen_path: str, candidates: List[str]) -> str:
    """
    Find the best match for a generated file path among candidate original paths.
    
    Args:
        gen_path: Generated file path.
        candidates: List of candidate original file paths.
        
    Returns:
        Best matching original file path.
    """
    best_score = 0
    best_match = candidates[0]
    
    gen_parts = gen_path.split(os.path.sep)
    
    for candidate in candidates:
        cand_parts = candidate.split(os.path.sep)
        
        # Calculate path similarity score
        score = 0
        for i in range(min(len(gen_parts), len(cand_parts))):
            # Compare from the end (filename first, then parent directories)
            gen_idx = len(gen_parts) - i - 1
            cand_idx = len(cand_parts) - i - 1
            
            if gen_parts[gen_idx] == cand_parts[cand_idx]:
                score += 10  # Higher weight for exact matches
            elif gen_parts[gen_idx].lower() == cand_parts[cand_idx].lower():
                score += 5   # Lower weight for case-insensitive matches
            else:
                similarity = difflib.SequenceMatcher(None, gen_parts[gen_idx], cand_parts[cand_idx]).ratio()
                score += similarity * 3  # Even lower weight for partial matches
        
        if score > best_score:
            best_score = score
            best_match = candidate
    
    return best_match

def find_best_content_match(gen_content: str, original_path: str, original_files: List[str]) -> Optional[str]:
    """
    Find the best content match for a generated file among original files.
    
    Args:
        gen_content: Generated file content.
        original_path: Path to the original codebase.
        original_files: List of original file paths.
        
    Returns:
        Best matching original file path or None if no good match found.
    """
    best_score = 0.3  # Minimum similarity threshold
    best_match = None
    
    # Normalize generated content for comparison
    gen_content = normalize_content(gen_content)
    
    for orig_file in original_files:
        try:
            with open(os.path.join(original_path, orig_file), 'r', encoding='utf-8') as f:
                orig_content = f.read()
            
            # Normalize original content for comparison
            orig_content = normalize_content(orig_content)
            
            # Calculate content similarity
            similarity = difflib.SequenceMatcher(None, gen_content, orig_content).ratio()
            
            if similarity > best_score:
                best_score = similarity
                best_match = orig_file
        except Exception as e:
            logger.warning(f"Error reading file {orig_file}: {e}")
    
    return best_match

def normalize_content(content: str) -> str:
    """
    Normalize code content for comparison by removing comments, whitespace, etc.
    
    Args:
        content: Code content to normalize.
        
    Returns:
        Normalized code content.
    """
    # Remove comments
    content = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    
    # Remove docstrings
    content = re.sub(r'""".*?"""', '', content, flags=re.DOTALL)
    content = re.sub(r"'''.*?'''", '', content, flags=re.DOTALL)
    
    # Remove empty lines and leading/trailing whitespace
    lines = [line.strip() for line in content.split('\n')]
    lines = [line for line in lines if line]
    
    # Join lines and remove extra whitespace
    content = ' '.join(lines)
    content = re.sub(r'\s+', ' ', content)
    
    return content.strip()

def validate_functionality(
    original_path: str, 
    generated_code: GeneratedCode, 
    file_mapping: Dict[str, str]
) -> Dict[str, Any]:
    """
    Validate the functional equivalence of the generated code.
    
    Args:
        original_path: Path to the original codebase.
        generated_code: GeneratedCode object with the re-implementation.
        file_mapping: Mapping from generated to original file paths.
        
    Returns:
        Dictionary with validation results.
    """
    file_comparison = []
    total_similarity = 0.0
    total_files = 0
    
    missing_details = []
    additional_details = []
    
    for gen_file in generated_code.files:
        gen_path = gen_file.path
        
        if gen_path in file_mapping:
            orig_path = file_mapping[gen_path]
            orig_full_path = os.path.join(original_path, orig_path)
            
            # Read original file content
            try:
                with open(orig_full_path, 'r', encoding='utf-8') as f:
                    orig_content = f.read()
                
                # Compare functionality
                if gen_path.endswith('.py'):
                    # For Python files, compare AST structures
                    comparison_result = compare_python_functionality(gen_file.content, orig_content)
                else:
                    # For other files, use simpler comparison
                    comparison_result = compare_general_functionality(gen_file.content, orig_content)
                
                # Add comparison result
                file_comparison.append({
                    'generated_path': gen_path,
                    'original_path': orig_path,
                    'similarity': comparison_result['similarity'],
                    'missing_elements': comparison_result['missing'],
                    'additional_elements': comparison_result['additional']
                })
                
                # Add to totals
                total_similarity += comparison_result['similarity']
                total_files += 1
                
                # Add to missing and additional details
                if comparison_result['missing']:
                    missing_details.append({
                        'file': gen_path,
                        'elements': comparison_result['missing']
                    })
                
                if comparison_result['additional']:
                    additional_details.append({
                        'file': gen_path,
                        'elements': comparison_result['additional']
                    })
                
            except Exception as e:
                logger.error(f"Error comparing files {gen_path} and {orig_path}: {e}")
                file_comparison.append({
                    'generated_path': gen_path,
                    'original_path': orig_path,
                    'similarity': 0.0,
                    'error': str(e)
                })
        else:
            # No matching original file
            file_comparison.append({
                'generated_path': gen_path,
                'original_path': None,
                'similarity': 0.0,
                'additional_elements': ['entire file']
            })
            
            additional_details.append({
                'file': gen_path,
                'elements': ['entire file']
            })
    
    # Check for original files without generated counterparts
    mapped_originals = set(file_mapping.values())
    unmapped_originals = [of for of in get_original_code_files(original_path) if of not in mapped_originals]
    
    for orig_path in unmapped_originals:
        file_comparison.append({
            'generated_path': None,
            'original_path': orig_path,
            'similarity': 0.0,
            'missing_elements': ['entire file']
        })
        
        missing_details.append({
            'file': orig_path,
            'elements': ['entire file']
        })
    
    # Calculate average similarity percentage
    if total_files > 0:
        avg_similarity = (total_similarity / total_files) * 100
    else:
        avg_similarity = 0.0
    
    return {
        'equivalence': avg_similarity,
        'file_comparison': file_comparison,
        'missing_details': missing_details,
        'additional_details': additional_details
    }

def get_original_code_files(original_path: str) -> List[str]:
    """
    Get list of code files in the original codebase.
    
    Args:
        original_path: Path to the original codebase.
        
    Returns:
        List of relative file paths.
    """
    code_files = []
    code_extensions = {'.py', '.js', '.ts', '.html', '.css', '.java', '.c', '.cpp', '.h', '.php', '.rb', '.go', '.rs'}
    
    for root, _, files in os.walk(original_path):
        for file in files:
            _, ext = os.path.splitext(file)
            if ext.lower() in code_extensions and not file.startswith('.'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, original_path)
                code_files.append(rel_path)
    
    return code_files

def compare_python_functionality(gen_content: str, orig_content: str) -> Dict[str, Any]:
    """
    Compare functionality of Python code using AST analysis.
    
    Args:
        gen_content: Generated Python code content.
        orig_content: Original Python code content.
        
    Returns:
        Dictionary with comparison results.
    """
    try:
        # Parse both files into AST
        gen_ast = ast.parse(gen_content)
        orig_ast = ast.parse(orig_content)
        
        # Extract functions, classes, and methods from both ASTs
        gen_elements = extract_python_elements(gen_ast)
        orig_elements = extract_python_elements(orig_ast)
        
        # Compare elements
        return compare_python_elements(gen_elements, orig_elements)
        
    except Exception as e:
        logger.error(f"Error comparing Python functionality: {e}")
        return {
            'similarity': 0.0,
            'missing': ['Error parsing Python code'],
            'additional': []
        }

def extract_python_elements(tree: ast.AST) -> Dict[str, Any]:
    """
    Extract functions, classes, and methods from a Python AST.
    
    Args:
        tree: AST of Python code.
        
    Returns:
        Dictionary of extracted elements.
    """
    elements = {
        'functions': {},
        'classes': {},
        'imports': [],
        'globals': []
    }
    
    # Extract functions
    for node in ast.walk(tree):
        # Get imports
        if isinstance(node, ast.Import):
            for name in node.names:
                elements['imports'].append(name.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for name in node.names:
                elements['imports'].append(f"{module}.{name.name}")
        
        # Get top-level functions
        elif isinstance(node, ast.FunctionDef) and isinstance(node.parent, ast.Module):
            func_def = {
                'name': node.name,
                'args': [arg.arg for arg in node.args.args],
                'returns': astunparse.unparse(node.returns).strip() if node.returns else None,
                'body_hash': hash(astunparse.unparse(node.body))
            }
            elements['functions'][node.name] = func_def
        
        # Get classes
        elif isinstance(node, ast.ClassDef):
            class_def = {
                'name': node.name,
                'bases': [astunparse.unparse(base).strip() for base in node.bases],
                'methods': {}
            }
            
            # Get methods
            for method in [n for n in node.body if isinstance(n, ast.FunctionDef)]:
                method_def = {
                    'name': method.name,
                    'args': [arg.arg for arg in method.args.args],
                    'returns': astunparse.unparse(method.returns).strip() if method.returns else None,
                    'body_hash': hash(astunparse.unparse(method.body))
                }
                class_def['methods'][method.name] = method_def
            
            elements['classes'][node.name] = class_def
        
        # Get global variable assignments
        elif isinstance(node, ast.Assign) and isinstance(node.parent, ast.Module):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    elements['globals'].append(target.id)
    
    return elements

def compare_python_elements(gen_elements: Dict[str, Any], orig_elements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare Python code elements for functional similarity.
    
    Args:
        gen_elements: Elements extracted from generated code.
        orig_elements: Elements extracted from original code.
        
    Returns:
        Dictionary with comparison results.
    """
    missing = []
    additional = []
    similarity_scores = []
    
    # Compare functions
    for func_name, orig_func in orig_elements['functions'].items():
        if func_name in gen_elements['functions']:
            gen_func = gen_elements['functions'][func_name]
            
            # Compare function signatures
            args_similarity = compare_lists(gen_func['args'], orig_func['args'])
            
            # Body similarity is binary (1 if hash matches, 0 if not)
            body_similarity = 1.0 if gen_func['body_hash'] == orig_func['body_hash'] else 0.5
            
            # Combined similarity for this function
            func_similarity = (args_similarity + body_similarity) / 2
            similarity_scores.append(func_similarity)
        else:
            missing.append(f"Function: {func_name}")
    
    # Check for additional functions
    for func_name in gen_elements['functions']:
        if func_name not in orig_elements['functions']:
            additional.append(f"Function: {func_name}")
    
    # Compare classes
    for class_name, orig_class in orig_elements['classes'].items():
        if class_name in gen_elements['classes']:
            gen_class = gen_elements['classes'][class_name]
            
            # Compare class bases
            bases_similarity = compare_lists(gen_class['bases'], orig_class['bases'])
            similarity_scores.append(bases_similarity)
            
            # Compare methods
            for method_name, orig_method in orig_class['methods'].items():
                if method_name in gen_class['methods']:
                    gen_method = gen_class['methods'][method_name]
                    
                    # Compare method signatures
                    args_similarity = compare_lists(gen_method['args'], orig_method['args'])
                    
                    # Body similarity is binary (1 if hash matches, 0 if not)
                    body_similarity = 1.0 if gen_method['body_hash'] == orig_method['body_hash'] else 0.5
                    
                    # Combined similarity for this method
                    method_similarity = (args_similarity + body_similarity) / 2
                    similarity_scores.append(method_similarity)
                else:
                    missing.append(f"Method: {class_name}.{method_name}")
            
            # Check for additional methods
            for method_name in gen_class['methods']:
                if method_name not in orig_class['methods']:
                    additional.append(f"Method: {class_name}.{method_name}")
                    
        else:
            missing.append(f"Class: {class_name}")
    
    # Check for additional classes
    for class_name in gen_elements['classes']:
        if class_name not in orig_elements['classes']:
            additional.append(f"Class: {class_name}")
    
    # Compare imports (less weight)
    imports_similarity = compare_lists(gen_elements['imports'], orig_elements['imports'])
    similarity_scores.append(imports_similarity * 0.5)  # Lower weight for imports
    
    # Compare globals (less weight)
    globals_similarity = compare_lists(gen_elements['globals'], orig_elements['globals'])
    similarity_scores.append(globals_similarity * 0.5)  # Lower weight for globals
    
    # Calculate overall similarity
    if similarity_scores:
        overall_similarity = sum(similarity_scores) / len(similarity_scores)
    else:
        overall_similarity = 0.0
    
    return {
        'similarity': overall_similarity,
        'missing': missing,
        'additional': additional
    }

def compare_lists(list1: List[str], list2: List[str]) -> float:
    """
    Compare two lists and return a similarity score.
    
    Args:
        list1: First list.
        list2: Second list.
        
    Returns:
        Similarity score between 0.0 and 1.0.
    """
    if not list1 and not list2:
        return 1.0
    
    if not list1 or not list2:
        return 0.0
    
    # Count matching elements
    matches = sum(1 for item in list1 if item in list2)
    
    # Calculate similarity as Jaccard similarity
    union_size = len(set(list1).union(set(list2)))
    similarity = matches / union_size
    
    return similarity

def compare_general_functionality(gen_content: str, orig_content: str) -> Dict[str, Any]:
    """
    Compare functionality of general code (non-Python).
    
    Args:
        gen_content: Generated code content.
        orig_content: Original code content.
        
    Returns:
        Dictionary with comparison results.
    """
    # Normalize content
    gen_normalized = normalize_content(gen_content)
    orig_normalized = normalize_content(orig_content)
    
    # Calculate similarity
    similarity = difflib.SequenceMatcher(None, gen_normalized, orig_normalized).ratio()
    
    # Extract key elements based on file type
    if gen_content.strip().startswith('<'):
        # HTML-like file
        missing_elements = find_missing_html_elements(gen_content, orig_content)
        additional_elements = find_additional_html_elements(gen_content, orig_content)
    elif 'function' in gen_content and '{' in gen_content:
        # JavaScript-like file
        missing_elements = find_missing_js_elements(gen_content, orig_content)
        additional_elements = find_additional_js_elements(gen_content, orig_content)
    else:
        # Generic text comparison
        missing_elements = []
        additional_elements = []
    
    return {
        'similarity': similarity,
        'missing': missing_elements,
        'additional': additional_elements
    }

def find_missing_html_elements(gen_content: str, orig_content: str) -> List[str]:
    """Find HTML elements in original but not in generated content."""
    # Simple regex-based extraction of elements (full parsing would be better)
    orig_elements = set(re.findall(r'<([a-zA-Z0-9]+)[^>]*id=[\'"]([^\'"]+)[\'"]', orig_content))
    gen_elements = set(re.findall(r'<([a-zA-Z0-9]+)[^>]*id=[\'"]([^\'"]+)[\'"]', gen_content))
    
    missing = []
    for element_type, element_id in orig_elements:
        if (element_type, element_id) not in gen_elements:
            missing.append(f"{element_type}#{element_id}")
    
    return missing

def find_additional_html_elements(gen_content: str, orig_content: str) -> List[str]:
    """Find HTML elements in generated but not in original content."""
    # Simple regex-based extraction of elements (full parsing would be better)
    orig_elements = set(re.findall(r'<([a-zA-Z0-9]+)[^>]*id=[\'"]([^\'"]+)[\'"]', orig_content))
    gen_elements = set(re.findall(r'<([a-zA-Z0-9]+)[^>]*id=[\'"]([^\'"]+)[\'"]', gen_content))
    
    additional = []
    for element_type, element_id in gen_elements:
        if (element_type, element_id) not in orig_elements:
            additional.append(f"{element_type}#{element_id}")
    
    return additional

def find_missing_js_elements(gen_content: str, orig_content: str) -> List[str]:
    """Find JavaScript elements in original but not in generated content."""
    # Extract functions and classes
    orig_functions = set(re.findall(r'function\s+([A-Za-z0-9_$]+)\s*\(', orig_content))
    gen_functions = set(re.findall(r'function\s+([A-Za-z0-9_$]+)\s*\(', gen_content))
    
    orig_classes = set(re.findall(r'class\s+([A-Za-z0-9_$]+)', orig_content))
    gen_classes = set(re.findall(r'class\s+([A-Za-z0-9_$]+)', gen_content))
    
    missing = []
    for func in orig_functions:
        if func not in gen_functions:
            missing.append(f"Function: {func}")
    
    for cls in orig_classes:
        if cls not in gen_classes:
            missing.append(f"Class: {cls}")
    
    return missing

def find_additional_js_elements(gen_content: str, orig_content: str) -> List[str]:
    """Find JavaScript elements in generated but not in original content."""
    # Extract functions and classes
    orig_functions = set(re.findall(r'function\s+([A-Za-z0-9_$]+)\s*\(', orig_content))
    gen_functions = set(re.findall(r'function\s+([A-Za-z0-9_$]+)\s*\(', gen_content))
    
    orig_classes = set(re.findall(r'class\s+([A-Za-z0-9_$]+)', orig_content))
    gen_classes = set(re.findall(r'class\s+([A-Za-z0-9_$]+)', gen_content))
    
    additional = []
    for func in gen_functions:
        if func not in orig_functions:
            additional.append(f"Function: {func}")
    
    for cls in gen_classes:
        if cls not in orig_classes:
            additional.append(f"Class: {cls}")
    
    return additional

def validate_structure(original_path: str, generated_code: GeneratedCode) -> Dict[str, Any]:
    """
    Validate the structural similarity of the generated code.
    
    Args:
        original_path: Path to the original codebase.
        generated_code: GeneratedCode object with the re-implementation.
        
    Returns:
        Dictionary with validation results.
    """
    # Get original structure
    orig_structure = extract_codebase_structure(original_path)
    
    # Get generated structure
    gen_structure = {
        'files': [f.path for f in generated_code.files],
        'directories': list(set([os.path.dirname(f.path) for f in generated_code.files if os.path.dirname(f.path)]))
    }
    
    # Compare structures
    comparison = compare_structures(gen_structure, orig_structure)
    
    return {
        'similarity': comparison['similarity'],
        'details': comparison
    }

def extract_codebase_structure(path: str) -> Dict[str, List[str]]:
    """
    Extract the structure of a codebase.
    
    Args:
        path: Path to the codebase.
        
    Returns:
        Dictionary with files and directories.
    """
    structure = {
        'files': [],
        'directories': []
    }
    
    for root, dirs, files in os.walk(path):
        rel_path = os.path.relpath(root, path)
        if rel_path != '.':
            structure['directories'].append(rel_path)
        
        for file in files:
            # Skip hidden and binary files
            if file.startswith('.') or not is_text_file(os.path.join(root, file)):
                continue
                
            file_path = os.path.join(rel_path, file)
            if rel_path == '.':
                file_path = file
                
            structure['files'].append(file_path)
    
    return structure

def compare_structures(gen_structure: Dict[str, List[str]], orig_structure: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Compare codebase structures.
    
    Args:
        gen_structure: Generated codebase structure.
        orig_structure: Original codebase structure.
        
    Returns:
        Dictionary with comparison results.
    """
    # Compare files
    file_similarity = compare_lists(gen_structure['files'], orig_structure['files'])
    
    # Compare directories
    dir_similarity = compare_lists(gen_structure['directories'], orig_structure['directories'])
    
    # Calculate missing and additional files
    missing_files = [f for f in orig_structure['files'] if f not in gen_structure['files']]
    additional_files = [f for f in gen_structure['files'] if f not in orig_structure['files']]
    
    # Calculate missing and additional directories
    missing_dirs = [d for d in orig_structure['directories'] if d not in gen_structure['directories']]
    additional_dirs = [d for d in gen_structure['directories'] if d not in orig_structure['directories']]
    
    # Calculate overall similarity (weighted)
    overall_similarity = (file_similarity * 0.7 + dir_similarity * 0.3) * 100
    
    return {
        'similarity': overall_similarity,
        'file_similarity': file_similarity,
        'directory_similarity': dir_similarity,
        'missing_files': missing_files,
        'additional_files': additional_files,
        'missing_directories': missing_dirs,
        'additional_directories': additional_dirs
    }

def identify_feature_differences(
    original_path: str, 
    generated_code: GeneratedCode, 
    file_mapping: Dict[str, str]
) -> Tuple[List[str], List[str]]:
    """
    Identify missing and additional features in the generated code.
    
    Args:
        original_path: Path to the original codebase.
        generated_code: GeneratedCode object with the re-implementation.
        file_mapping: Mapping from generated to original file paths.
        
    Returns:
        Tuple of (missing_features, additional_features).
    """
    # Initialize lists
    missing_features = []
    additional_features = []
    
    # Extract features from comparison
    for gen_file in generated_code.files:
        gen_path = gen_file.path
        
        if gen_path in file_mapping:
            orig_path = file_mapping[gen_path]
            
            try:
                with open(os.path.join(original_path, orig_path), 'r', encoding='utf-8') as f:
                    orig_content = f.read()
                
                # Extract features from the file based on its type
                if gen_path.endswith('.py'):
                    # Python file
                    file_missing, file_additional = compare_python_features(gen_file.content, orig_content)
                elif gen_path.endswith(('.js', '.ts')):
                    # JavaScript/TypeScript file
                    file_missing, file_additional = compare_js_features(gen_file.content, orig_content)
                elif gen_path.endswith('.html'):
                    # HTML file
                    file_missing, file_additional = compare_html_features(gen_file.content, orig_content)
                else:
                    # Other file types
                    file_missing, file_additional = [], []
                
                # Add file-specific features to the main lists
                missing_features.extend([f"{orig_path}: {feature}" for feature in file_missing])
                additional_features.extend([f"{gen_path}: {feature}" for feature in file_additional])
                
            except Exception as e:
                logger.error(f"Error comparing features for {gen_path} and {orig_path}: {e}")
    
    # Add completely missing files as missing features
    mapped_originals = set(file_mapping.values())
    unmapped_originals = [of for of in get_original_code_files(original_path) if of not in mapped_originals]
    
    for orig_path in unmapped_originals:
        # Check if this is an important file
        try:
            with open(os.path.join(original_path, orig_path), 'r', encoding='utf-8') as f:
                file_content = f.read()
                
                # If file has substantial content, consider it a missing feature
                if len(file_content.strip()) > 100:
                    missing_features.append(f"Missing file: {orig_path}")
        except Exception:
            pass
    
    return missing_features, additional_features

def compare_python_features(gen_content: str, orig_content: str) -> Tuple[List[str], List[str]]:
    """
    Compare Python features between generated and original code.
    
    Args:
        gen_content: Generated Python code content.
        orig_content: Original Python code content.
        
    Returns:
        Tuple of (missing_features, additional_features).
    """
    try:
        # Parse both files into AST
        gen_ast = ast.parse(gen_content)
        orig_ast = ast.parse(orig_content)
        
        # Extract classes and functions
        gen_classes = [node.name for node in gen_ast.body if isinstance(node, ast.ClassDef)]
        orig_classes = [node.name for node in orig_ast.body if isinstance(node, ast.ClassDef)]
        
        gen_functions = [node.name for node in gen_ast.body if isinstance(node, ast.FunctionDef)]
        orig_functions = [node.name for node in orig_ast.body if isinstance(node, ast.FunctionDef)]
        
        # Find missing and additional features
        missing = []
        for cls in orig_classes:
            if cls not in gen_classes:
                missing.append(f"Class: {cls}")
        
        for func in orig_functions:
            if func not in gen_functions:
                missing.append(f"Function: {func}")
        
        additional = []
        for cls in gen_classes:
            if cls not in orig_classes:
                additional.append(f"Class: {cls}")
        
        for func in gen_functions:
            if func not in orig_functions:
                additional.append(f"Function: {func}")
        
        return missing, additional
        
    except Exception as e:
        logger.error(f"Error comparing Python features: {e}")
        return [], []

def compare_js_features(gen_content: str, orig_content: str) -> Tuple[List[str], List[str]]:
    """
    Compare JavaScript/TypeScript features between generated and original code.
    
    Args:
        gen_content: Generated JS/TS code content.
        orig_content: Original JS/TS code content.
        
    Returns:
        Tuple of (missing_features, additional_features).
    """
    # Extract functions
    orig_functions = set(re.findall(r'(?:function|const|let|var)\s+([A-Za-z0-9_$]+)\s*(?:=\s*function|\([^)]*\)\s*{)', orig_content))
    gen_functions = set(re.findall(r'(?:function|const|let|var)\s+([A-Za-z0-9_$]+)\s*(?:=\s*function|\([^)]*\)\s*{)', gen_content))
    
    # Extract classes
    orig_classes = set(re.findall(r'class\s+([A-Za-z0-9_$]+)', orig_content))
    gen_classes = set(re.findall(r'class\s+([A-Za-z0-9_$]+)', gen_content))
    
    # Find missing and additional features
    missing = []
    for func in orig_functions:
        if func not in gen_functions:
            missing.append(f"Function: {func}")
    
    for cls in orig_classes:
        if cls not in gen_classes:
            missing.append(f"Class: {cls}")
    
    additional = []
    for func in gen_functions:
        if func not in orig_functions:
            additional.append(f"Function: {func}")
    
    for cls in gen_classes:
        if cls not in orig_classes:
            additional.append(f"Class: {cls}")
    
    return missing, additional

def compare_html_features(gen_content: str, orig_content: str) -> Tuple[List[str], List[str]]:
    """
    Compare HTML features between generated and original code.
    
    Args:
        gen_content: Generated HTML code content.
        orig_content: Original HTML code content.
        
    Returns:
        Tuple of (missing_features, additional_features).
    """
    # Extract elements with IDs
    orig_elements = set(re.findall(r'<([a-zA-Z0-9]+)[^>]*id=[\'"]([^\'"]+)[\'"]', orig_content))
    gen_elements = set(re.findall(r'<([a-zA-Z0-9]+)[^>]*id=[\'"]([^\'"]+)[\'"]', gen_content))
    
    # Extract forms
    orig_forms = set(re.findall(r'<form[^>]*action=[\'"]([^\'"]+)[\'"]', orig_content))
    gen_forms = set(re.findall(r'<form[^>]*action=[\'"]([^\'"]+)[\'"]', gen_content))
    
    # Find missing and additional features
    missing = []
    for element_type, element_id in orig_elements:
        if (element_type, element_id) not in gen_elements:
            missing.append(f"Element: {element_type}#{element_id}")
    
    for form_action in orig_forms:
        if form_action not in gen_forms:
            missing.append(f"Form: {form_action}")
    
    additional = []
    for element_type, element_id in gen_elements:
        if (element_type, element_id) not in orig_elements:
            additional.append(f"Element: {element_type}#{element_id}")
    
    for form_action in gen_forms:
        if form_action not in orig_forms:
            additional.append(f"Form: {form_action}")
    
    return missing, additional
