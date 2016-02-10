Experiment Setup
================

DMagic example on how to automatically set up an experiment data directory and share it with the users. Experiment Setup also automatically copies the data and shares them with users from a remote Globus server. (Download file: :download:`dm_setup.py<../../../doc/demo/dm_setup.py>`)

Pre-requisites
++++++++++++++

Experiment Setup relies on the following configuration:

- **local**: this is the computer where the detector is connected. The raw data directory to share will be created on a local disk of this computer. Experiment Setup runs on local.

- **personal**: this is a computer running a `Globus Connect Personal endpoint <https://www.globus.org/globus-connect-personal/>`__.   Configure a Globus shared folder on this computer by setting the GMagic `Globus configuration <https://github.com/decarlof/DMagic/blob/master/config/globus.ini>`__ file. In this example the Globus Connect Personal endpoint  runs on **local**.

- **remote**: this is a Globus server with share enabled (e.g. petrel). Configure the remote Globus server by setting the GMagic `Globus configuration <https://github.com/decarlof/DMagic/blob/master/config/globus.ini>`__ file.

- access to the `APS scheduling system <https://schedule.aps.anl.gov/>`__ by setting the GMagic `Scheduling configuration <https://github.com/decarlof/DMagic/blob/master/config/scheduling.ini>`__ file.

Tasks
+++++

.. contents:: Contents:
   :local:

- Unique data directory creation

    Using the current date and accessing the APS scheduling system, Experiment Setup creates a unique folder *YYYY-MM/pi_last_name* on **local**. 
  
- Data Sharing

    Experiment Setup sends an e-mail to the users with a link to access the data on **personal**. Experiment Setup also copies the data to **remote** and sends an e-mail to the users with a link to access the data on **remote**.
    The user e-mails are retrieved using the current date and accessing the APS scheduling system. Since what is shared is a link to the folder, users will have remote access to the raw data as they are collected and to any data generated or copied in the same folder at a later time.


