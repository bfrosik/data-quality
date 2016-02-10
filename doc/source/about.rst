============
About DMagic 
============

Data collection at the Advanced Photon Source (APS) can generate massive 
amount of data and often the beamline staff can be overwhelmed by 
routine data management tasks like sharing, distributing and archiving.

`DMagic <https://github.com/decarlof/DMagic>`_ aims to provide easy command-like
instruction to automate the majority of beamline scientist data 
management tasks. The toolbox has been developed to support the APS Imaging 
Group data management activities but it can be easily adopted and implemented
at any APS beamline. 

`DMagic <https://github.com/decarlof/DMagic>`_ relies on automatic access to the  
`APS scheduling system <https://schedule.aps.anl.gov/>`__ 
and makes extent use of `Globus <https://www.globus.org/>`__.

Basic functionality include the ability, for a given experiment date, to retrieve the users' 
email addresses from the APS scheduling system and automatically send an e-mail to the users 
containing a link (drop-box style) to retrieve the data. 

Monitor a directory and copy any new files to a globus connect personal or remote server endpoints.

Data can be shared directly from the beamline machine or from a Globus server.
