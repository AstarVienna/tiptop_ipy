Installation
============

Requirements
------------

- Python 3.9+
- numpy
- astropy
- matplotlib
- requests
- requests_toolbelt
- PyYAML

Install from GitHub
-------------------

.. code-block:: bash

   pip install git+https://github.com/astronomyk/tiptop_ipy.git

Install for development
-----------------------

.. code-block:: bash

   git clone https://github.com/astronomyk/tiptop_ipy.git
   cd tiptop_ipy
   pip install -e .

Verify the installation
-----------------------

.. code-block:: python

   from tiptop_ipy import TipTop

   # List available instruments
   TipTop.list_instruments()

   # Check the server is reachable
   TipTop.ping()
