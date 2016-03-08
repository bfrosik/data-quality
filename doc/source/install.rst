=======
Install
=======

This section covers the basics of how to download and install `DQuality <https://github.com/bfrosik/data-quality>`_.

.. contents:: Contents:
   :local:

.. _pre-requisite-reference-label:

Pre-requisites 
==============

Before testing `DQuality <https://github.com/bfrosik/data-quality>`_  on your data files you need to create in your home directory the following files:
    
- :download:`dqconfig.ini <config/dqconfig.ini>`

You must also create in your home directory a "*dqschemas*" folder containing the following files:

- :download:`dqschemas/pvs.json.json <config/dqschemas/pvs.json>` containing the list of Process variable (PV) of your beamline PVs with their acceptable value range.

- :download:`dqschemas/basicHDF.json <config/dqschemas/basicHDF.json>` containing the list valid HDF file tags, attributes and array dimentions.

- :download:`dqschemas/dependencies.json <config/dqschemas/dependencies.json>` containing the list of valid relation among data sets in the same HDF file.

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
    
