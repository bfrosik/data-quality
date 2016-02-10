Experiment Monitor
==================

DMagic active directory monitoring example. (Download file: :download:`dm_monitor.py<../../../doc/demo/dm_monitor.py>`)

Pre-requisites
++++++++++++++

Experiment Monitor relies on the following configuration:

- **local**: this is the computer where the detector is connected. The raw data directory is located on a local disk of this computer. Experiment Monitor runs on local.

- **personal**: this is a computer, generally different from local, where the data analysis will be completed. On personal you need to run a `Globus Connect Personal endpoint <https://www.globus.org/globus-connect-personal/>`__ and configure a Globus shared folder by setting the GMagic `Globus configuration <https://github.com/decarlof/DMagic/blob/master/config/globus.ini>`__ file.


- access to the `APS scheduling system <https://schedule.aps.anl.gov/>`__ by setting the GMagic `Scheduling configuration <https://github.com/decarlof/DMagic/blob/master/config/scheduling.ini>`__ file.

- ssh public key sharing: local and personal are configured to ssh into each other with no password required.


Tasks
+++++

.. contents:: Contents:
   :local:

- Unique data directory creation

    Using the current date and accessing the APS scheduling system, Experiment Monitor creates a unique folder *YYYY-MM/pi_last_name* on **local** and on **personal** .

- Data Collection
    
    Configure your data collection software running on **local** to store the raw data in the newly created directory *YYYY-MM/pi_last_name* and start to collect data.
    
- Data Monitoring
    
    Experiment Monitor will look for new files on **local** and copy them to **personal**.
    
- Data Sharing

    Experiment Monitor sends an e-mail to the users with a link to access the data on **personal**. The user e-mails are retrieved using the current date and accessing the APS scheduling system. Since what is shared is a link to the folder, users will have remote access to the raw data as they are collected and to any data analysis results generated in the same folder at a later time.


