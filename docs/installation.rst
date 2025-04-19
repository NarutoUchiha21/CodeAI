Installation
============

This page provides detailed instructions for installing the Code Analysis System.

Requirements
-----------

The Code Analysis System requires Python 3.8 or higher. The following dependencies are automatically installed when you install the package:

* numpy>=1.21.0
* pandas>=1.3.0
* networkx>=2.6.0
* scikit-learn>=0.24.0
* transformers>=4.30.0
* torch>=2.0.0
* flask>=2.0.0
* flask-cors>=3.0.0
* jinja2>=3.0.0

Installation Methods
------------------

From PyPI
~~~~~~~~~

The easiest way to install the Code Analysis System is using pip:

.. code-block:: bash

   pip install code-analysis-system

From Source
~~~~~~~~~~

To install from source, clone the repository and install in development mode:

.. code-block:: bash

   git clone https://github.com/yourusername/code-analysis-system.git
   cd code-analysis-system
   pip install -e .

Development Installation
~~~~~~~~~~~~~~~~~~~~~~

For development, install with the development dependencies:

.. code-block:: bash

   pip install -e ".[dev]"

This will install additional packages needed for development:

* pytest>=7.0.0
* pytest-cov>=4.0.0
* black>=22.0.0
* isort>=5.0.0
* flake8>=4.0.0
* mypy>=0.900
* sphinx>=4.0.0
* sphinx-rtd-theme>=1.0.0

Virtual Environment
-----------------

It's recommended to use a virtual environment to avoid conflicts with other packages:

.. code-block:: bash

   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install code-analysis-system

Configuration
------------

After installation, you may want to configure the system. Create a configuration file at ``~/.config/code_analysis/config.json``:

.. code-block:: json

   {
     "api_keys": {
       "openai": "your-api-key-here"
     },
     "output_dir": "output",
     "log_level": "INFO"
   }

Verify Installation
-----------------

To verify that the installation was successful, run:

.. code-block:: bash

   code-analysis --version

You should see the version number of the installed package.

Troubleshooting
--------------

Common Issues
~~~~~~~~~~~~

1. **ImportError: No module named 'code_analysis'**

   Make sure you've installed the package correctly. Try reinstalling:

   .. code-block:: bash

      pip uninstall code-analysis-system
      pip install code-analysis-system

2. **ModuleNotFoundError: No module named 'torch'**

   Some dependencies might not be installed correctly. Try installing them manually:

   .. code-block:: bash

      pip install torch transformers

3. **Permission denied**

   You might need to use sudo (on Linux/Mac) or run as administrator (on Windows):

   .. code-block:: bash

      sudo pip install code-analysis-system

Getting Help
~~~~~~~~~~~

If you encounter any issues not covered here, please:

1. Check the `GitHub issues <https://github.com/yourusername/code-analysis-system/issues>`_
2. Join our `Discord community <https://discord.gg/your-discord>`_
3. Email support at support@example.com 