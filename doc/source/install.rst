=======
Install
=======

This section covers the basics of how to download and install `DQuality <https://github.com/bfrosik/data-quality>`_.

.. contents:: Contents:
   :local:

.. _pre-requisite-reference-label:

Pre-requisites 
==============

Each of the verifier requires a parameter configuration file. The configuration files must define schemas and verifier's properties and be located
in the user account home directory under a .dquality/default folder. 
    
- :download:`~/.dquality/default/dqconfig.ini <../../config/default/dqconfig.ini>`

The schemas should be saved under "*default/schemas*" folder and contain the following files:

- :download:`~/.dquality/default/schemas/pvs.json <../../config/default/schemas/pvs.json>` containing the list of Process variable (PV) of your beamline PVs with their acceptable value range.

- :download:`~/.dquality/default/schemas/tags.json <../../config/default/schemas/tags.json>` containing the list valid HDF file tags, attributes and array dimentions.

- :download:`~/.dquality/default/schemas/dependencies.json <../../config/default/schemas/dependencies.json>` containing the list of valid relation among data sets in the same HDF file.

- :download:`~/.dquality/default/schemas/limits.json <../../config/default/schemas/limits.json>` containing the threshold values for the quality check calculations.

- :download:`~/.dquality/default/schemas/data_tags.json <../../config/default/schemas/data_tags.json>` containing the dictionary of hdf tags of data sets by data type.

- :download:`~/.dquality/default/schemas/quality_checks.json <../../config/default/schemas/quality_checks.json>` containing the dictionary of quality check calculations. The keys are the slice verification methods, values are lists of stat methods.

Different instruments generating data that require different sets of configuration files can be configured as ~/.dquality/instrument1,
~/.dquality/instrument2 etc. with the same schemas subfolder structure.

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
    
