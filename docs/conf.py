# Configuration file for the Sphinx documentation builder.

project = "tiptop_ipy"
copyright = "2024, The TIPTOP team, wrapped by Kieran Leschinski"
author = "Kieran Leschinski"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = []

# Napoleon settings (for Google/NumPy style docstrings)
napoleon_google_docstrings = False
napoleon_numpy_docstrings = True

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "astropy": ("https://docs.astropy.org/en/stable/", None),
}

# Autodoc settings
autodoc_member_order = "bysource"
autodoc_typehints = "description"
