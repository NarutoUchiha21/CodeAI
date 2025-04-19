"""
Sphinx configuration file.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, src_path)

# Project information
project = "Code Analysis System"
copyright = "2023, Your Name"
author = "Your Name"

# The full version, including alpha/beta/rc tags
release = "0.1.0"

# Add any Sphinx extension module names here
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

# Add any paths that contain templates here
templates_path = ["_templates"]

# List of patterns to exclude from source files
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The theme to use for HTML and HTML Help pages
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files
html_static_path = ["_static"]

# Intersphinx configuration
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
}

# Autodoc configuration
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
} 