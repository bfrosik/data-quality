Globus Copy & Share
===================

Module to copy data from a Globus Personal shared folder to a remote Globus server share and, optionally, share the remote
folder with a user by sending an e-mail.

For help and to run::

    python globus_copy.py -h

Pre-requisites
++++++++++++++

Before using **globus_copy** for the first time you need to have setup an account on `Globus <https://www.globus.org/>`__, 
installed a  `Globus Connect Personal endpoint <https://www.globus.org/globus-connect-personal/>`__
on the computer you want to share data from and met the the Globus Command Line Interface (CLI) 
`pre-requisites <http://dev.globus.org/cli/using-the-cli/#prerequisites>`__, then edit 
the GMagic `Globus configuration file <https://github.com/decarlof/DMagic/blob/master/config/globus.ini>`__ :

- **settings**: Set the cli_user/cli_address.

- **globus connect personal**: set the globus connect personal endpoint as **user** # **host**. 

- login as **user** on `Globus <https://www.globus.org/>`__ and add the folder you want to share as a  `Globus **share** <https://support.globus.org/entries/23602336>`__

- **globus remote server**: set the globus remote server endpoint. 

Tasks
+++++

- Data Copying and Sharing

    globus_copy copies a folder from a `Globus Connect Personal endpoint <https://www.globus.org/globus-connect-personal/>`__ to a Globus remote server and, optionally, sends an invitation e-mail (drop-dox style) to the user to access the remote folder. Since what is shared is a link to the folder, users will have access to the current and any future content. 

Download file: :download:`globus_copy.py<../../../doc/demo/globus_copy.py>`

.. literalinclude:: ../../../doc/demo/globus_copy.py    :tab-width: 4    :linenos:    :language: guess
