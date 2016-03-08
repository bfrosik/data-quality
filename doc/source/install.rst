=======
Install
=======

This section covers the basics of how to download and install `DQuality <https://github.com/bfrosik/data-quality>`_.

.. contents:: Contents:
   :local:


.. _pre-requisite-reference-label:

Pre-requisites 
==============

Before testing `DQuality <https://github.com/bfrosik/data-quality>`_  on your data you need to create in your home directory a `config.ini <https://github.com/bfrosik/data-quality/blob/master/dquality/config.ini>`__ file to match your system.

You must also create in your home directory a "*schema*" folder containing the following files:

- `pv.json <https://github.com/bfrosik/data-quality/blob/master/dquality/schemas/pvs.json>`__ containing the list of Process variable (PV) of your beamline PVs with their acceptable value range.
- `basicHDF.json <https://github.com/bfrosik/data-quality/blob/master/dquality/schemas/basicHD5.json>`__ containing the list valid HDF file tags, attributes and array dimentions. 
- `dependencies.json <https://github.com/bfrosik/data-quality/blob/master/dquality/schemas/dependencies.json>`__ containing the list of valid relation among data sets in the same HDF file.


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
    
