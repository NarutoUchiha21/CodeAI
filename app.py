import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
import tempfile
import shutil
import uuid
import json

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Set up temporary directory for uploaded codebases
TEMP_UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'codebase_uploads')
os.makedirs(TEMP_UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = TEMP_UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload size

# Import components
from code_analyzer import analyze_codebase
from spec_extractor import extract_specifications
from strategy_generator import generate_strategy
from code_generator import generate_code
from validator import validate_implementation
from knowledge_graph import create_knowledge_graph
from visualizer import create_visualizations
from agent_orchestrator import orchestrate_agents

# Routes
@app.route('/')
def index():
    """Redirect to upload page"""
    return redirect(url_for('upload'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Handle codebase upload from ZIP file or Git repository"""
    if request.method == 'POST':
        upload_type = request.form.get('upload_type', 'zip')
        
        # Create a unique folder for this upload
        upload_id = str(uuid.uuid4())
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_id)
        os.makedirs(upload_path, exist_ok=True)
        
        try:
            if upload_type == 'zip':
                # Handle ZIP file upload
                if 'codebase' not in request.files:
                    flash('No file part')
                    return redirect(request.url)
                
                file = request.files['codebase']
                
                # If user does not select file, browser also
                # submit an empty part without filename
                if file.filename == '':
                    flash('No selected file')
                    return redirect(request.url)
                
                if file:
                    # Save the zipfile
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(upload_path, filename)
                    file.save(file_path)
                    
                    # Extract the zipfile
                    shutil.unpack_archive(file_path, upload_path)
                    # Remove the zip file after extraction
                    os.remove(file_path)
                    
                    # Store the project name based on the zip filename
                    project_name = os.path.splitext(filename)[0]
                    
            elif upload_type == 'git':
                # Handle Git repository clone
                git_url = request.form.get('git_url')
                git_branch = request.form.get('git_branch', None)  # Optional branch
                
                if not git_url:
                    flash('No Git repository URL provided')
                    return redirect(request.url)
                
                try:
                    from git import Repo
                    
                    # Extract repository name from URL to use as project name
                    repo_name = git_url.rstrip('/').split('/')[-1]
                    if repo_name.endswith('.git'):
                        repo_name = repo_name[:-4]  # Remove .git suffix
                    
                    # Clone the repository
                    logger.info(f"Cloning Git repository from {git_url}")
                    clone_args = {'url': git_url, 'to_path': upload_path}
                    
                    # Add branch if specified
                    if git_branch:
                        clone_args['branch'] = git_branch
                    
                    Repo.clone_from(**clone_args)
                    project_name = repo_name
                    
                except Exception as e:
                    logger.error(f"Error cloning Git repository: {e}")
                    flash(f"Error cloning Git repository: {str(e)}")
                    # Clean up created directory
                    shutil.rmtree(upload_path)
                    return redirect(request.url)
            else:
                flash('Invalid upload type')
                return redirect(request.url)
            
            # Store the upload_id in session for tracking this project
            session['upload_id'] = upload_id
            session['project_name'] = project_name
            
            # Redirect to the analysis page
            return redirect(url_for('analyze'))
            
        except Exception as e:
            logger.error(f"Error processing upload: {e}")
            flash(f"Error processing upload: {str(e)}")
            # Clean up created directory
            if os.path.exists(upload_path):
                shutil.rmtree(upload_path)
            return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/analyze')
def analyze():
    """Analyze the uploaded codebase"""
    upload_id = session.get('upload_id')
    if not upload_id:
        flash('No uploaded codebase found. Please upload one first.')
        return redirect(url_for('upload'))
    
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_id)
    
    try:
        # Analyze the codebase
        analysis_result = analyze_codebase(upload_path)
        
        # Store the result in session
        session['analysis_result'] = analysis_result
        
        # Create knowledge graph
        knowledge_graph = create_knowledge_graph(analysis_result)
        session['knowledge_graph'] = knowledge_graph
        
        # Create visualizations
        visualizations = create_visualizations(analysis_result, knowledge_graph)
        
        return render_template('analysis.html', 
                            analysis=analysis_result,
                            visualizations=visualizations,
                            project_name=session.get('project_name', 'Unnamed Project'))
    except Exception as e:
        logger.error(f"Error analyzing codebase: {e}")
        flash(f"Error analyzing codebase: {str(e)}")
        return redirect(url_for('upload'))

@app.route('/specifications')
def specifications():
    """Extract specifications from the analyzed codebase"""
    analysis_result = session.get('analysis_result')
    if not analysis_result:
        flash('No analysis results found. Please analyze a codebase first.')
        return redirect(url_for('upload'))
    
    try:
        # Extract specifications
        specs = extract_specifications(analysis_result)
        
        # Store specs in session
        session['specifications'] = specs
        
        return render_template('specifications.html', 
                            specifications=specs,
                            project_name=session.get('project_name', 'Unnamed Project'))
    except Exception as e:
        logger.error(f"Error extracting specifications: {e}")
        flash(f"Error extracting specifications: {str(e)}")
        return redirect(url_for('analyze'))

@app.route('/strategy')
def strategy():
    """Generate implementation strategy based on specifications"""
    specs = session.get('specifications')
    if not specs:
        flash('No specifications found. Please extract specifications first.')
        return redirect(url_for('specifications'))
    
    try:
        # Generate implementation strategy
        implementation_strategy = generate_strategy(specs)
        
        # Store strategy in session
        session['implementation_strategy'] = implementation_strategy
        
        return render_template('strategy.html', 
                            strategy=implementation_strategy,
                            project_name=session.get('project_name', 'Unnamed Project'))
    except Exception as e:
        logger.error(f"Error generating strategy: {e}")
        flash(f"Error generating strategy: {str(e)}")
        return redirect(url_for('specifications'))

@app.route('/implementation')
def implementation():
    """Implement code based on strategy and specifications"""
    specs = session.get('specifications')
    strategy = session.get('implementation_strategy')
    
    if not specs or not strategy:
        flash('Missing specifications or strategy. Please complete previous steps first.')
        return redirect(url_for('strategy'))
    
    try:
        # Orchestrate agents to implement the code
        implementation_result = orchestrate_agents(specs, strategy)
        
        # Generate the actual code
        generated_code = generate_code(implementation_result)
        
        # Store generated code in session
        session['generated_code'] = generated_code
        
        return render_template('implementation.html', 
                            implementation=generated_code,
                            project_name=session.get('project_name', 'Unnamed Project'))
    except Exception as e:
        logger.error(f"Error implementing code: {e}")
        flash(f"Error implementing code: {str(e)}")
        return redirect(url_for('strategy'))

@app.route('/validation')
def validation():
    """Validate the re-implemented code against the original"""
    upload_id = session.get('upload_id')
    generated_code = session.get('generated_code')
    
    if not upload_id or not generated_code:
        flash('Missing uploaded codebase or generated code. Please complete previous steps first.')
        return redirect(url_for('implementation'))
    
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_id)
    
    try:
        # Validate the implementation
        validation_results = validate_implementation(upload_path, generated_code)
        
        return render_template('validation.html', 
                            validation=validation_results,
                            project_name=session.get('project_name', 'Unnamed Project'))
    except Exception as e:
        logger.error(f"Error validating implementation: {e}")
        flash(f"Error validating implementation: {str(e)}")
        return redirect(url_for('implementation'))

@app.route('/download/<file_type>')
def download(file_type):
    """Download generated files (specs, code, etc.)"""
    if file_type == 'specifications':
        data = session.get('specifications')
    elif file_type == 'strategy':
        data = session.get('implementation_strategy')
    elif file_type == 'code':
        data = session.get('generated_code')
    else:
        flash(f"Unknown file type: {file_type}")
        return redirect(url_for('index'))
    
    if not data:
        flash(f"No {file_type} data available")
        return redirect(url_for('index'))
    
    # Convert to JSON and return as downloadable file
    response = jsonify(data)
    response.headers["Content-Disposition"] = f"attachment; filename={file_type}.json"
    return response

# Cleanup process - remove temporary files after session expires
@app.teardown_appcontext
def cleanup_upload(error):
    try:
        # Only try to access session if we're in a request context
        from flask import has_request_context
        if has_request_context():
            upload_id = session.get('upload_id')
            if upload_id:
                try:
                    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_id)
                    if os.path.exists(upload_path):
                        shutil.rmtree(upload_path)
                except Exception as e:
                    logger.error(f"Error cleaning up upload directory: {e}")
    except Exception as e:
        logger.error(f"Error in cleanup_upload: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
