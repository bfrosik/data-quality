==================
Install directions
==================

This section covers the basics of how to download and install `DMagic <https://github.com/decarlof/DMagic>`_.

.. contents:: Contents:
   :local:


Pre-requisites
==============

Before using `DMagic <https://github.com/decarlof/DMagic>`_  you need to have setup an account 
on `Globus <https://www.globus.org/>`__, installed a 
`Globus Connect Personal endpoint <https://www.globus.org/globus-connect-personal/>`__
on the APS computer you want to share data from and met the the Globus 
Command Line Interface (CLI) `pre-requisites <http://dev.globus.org/cli/using-the-cli/#prerequisites>`__.

To access the `APS scheduling system <https://schedule.aps.anl.gov/>`__ you need 
valid APS credentials.

Finally you must also create in your home directory configuration files for 
`globus <https://github.com/decarlof/DMagic/blob/master/config/globus.ini>`__ 
and `scheduling <https://github.com/decarlof/DMagic/blob/master/config/scheduling.ini>`__ 
systems.


Installing from source
======================

Install the following::

    pip install suds
    pip install ipdb
    pip install validate-email
    pip install pyinotify
    
Clone the `DMagic <https://github.com/decarlof/DMagic>`_  
from `GitHub <https://github.com>`_ repository::

    git clone https://github.com/decarlof/DMagic.git DMagic

then::

    cd DMagic
    python setup.py install


Installing from Conda/Binstar (coming soon)
===========================================

First you must have `Conda <http://continuum.io/downloads>`_ 
installed, then open a terminal or a command prompt window and run::

    conda install -c https://conda.anaconda.org/decarlof dmagic


Updating the installation (coming soon)
=======================================

Data Management is an active project, so we suggest you update your installation 
frequently. To update the installation run in your terminal::

    conda update -c https://conda.anaconda.org/decarlof dmagic

For some more information about using Conda, please refer to the 
`docs <http://conda.pydata.org/docs>`__.
    
