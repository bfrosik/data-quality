=======
Install
=======

This section covers the basics of how to download and install `DQuality <https://github.com/bfrosik/data-quality>`_.

.. contents:: Contents:
   :local:

.. _pre-requisite-reference-label:

Pre-requisites 
==============

Each of the verifier requires parameter: configuration file. The configuration file must define schemas, and verifire's properties.
    
- :download:`default/dqconfig.ini <../../config/default/dqconfig.ini>`

The schemas can point to different files, in different paths, but it is advised to create a relative "*default/schemas*" folder containing the following files:

- :download:`default/schemas/pvs.json <../../config/default/schemas/pvs.json>` containing the list of Process variable (PV) of your beamline PVs with their acceptable value range.

- :download:`default/schemas/tags.json <../../config/default/schemas/tags.json>` containing the list valid HDF file tags, attributes and array dimentions.

- :download:`schemas/dependencies.json <../../config/default/schemas/dependencies.json>` containing the list of valid relation among data sets in the same HDF file.

- :download:`default/schemas/limits.json <../../config/default/schemas/limits.json>` containing the threshold values for the quality check calculations.

Installing from source
======================
  
Clone the `DQuality <https://github.com/bfrosik/data-quality>`_  
from `GitHub <https://github.com>`_ repository::

    git clone https://github.com/bfrosik/data-quality.git DQuality

then::

    cd DQuality
    python setup.py install


Installing from Conda/Binstar (coming soon)
===========================================

First you must have `Conda <http://continuum.io/downloads>`_ 
installed, then open a terminal or a command prompt window and run::

    conda install -c ....


Updating the installation (coming soon)
=======================================

Data Management is an active project, so we suggest you update your installation 
frequently. To update the installation run in your terminal::

    conda update -c ....

For some more information about using Conda, please refer to the 
`docs <http://conda.pydata.org/docs>`__.
    
