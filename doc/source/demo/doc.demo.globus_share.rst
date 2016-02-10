Globus Share
============

Module to share a Globus Personal shared folder with a user by sending an e-mail.

For help and to run::

    python globus_share.py -h

Pre-requisites
++++++++++++++

Before using **globus_share** for the first time you need to have setup an account on `Globus <https://www.globus.org/>`__, 
installed a  `Globus Connect Personal endpoint <https://www.globus.org/globus-connect-personal/>`__
on the computer you want to share data from and met the the Globus Command Line Interface (CLI) 
`pre-requisites <http://dev.globus.org/cli/using-the-cli/#prerequisites>`__ then edit the GMagic 
`Globus configuration file <https://github.com/decarlof/DMagic/blob/master/config/globus.ini>`__ :

- **settings**: Set the cli_user/cli_address.

- **globus connect personal**: set the globus connect personal endpoint as **user** # **host**. 

- login as **user** on `Globus <https://www.globus.org/>`__ and add the folder you want to share as a  `Globus **share** <https://support.globus.org/entries/23602336>`__


Tasks
+++++

- Data Sharing

    globus_share sends an invitation e-mail (drop-dox style) to the user. Since what is shared is a link to the folder, users will have access to the current and any future content. 


Download file: :download:`globus_share.py<../../../doc/demo/globus_share.py>`

.. literalinclude:: ../../../doc/demo/globus_share.py    :tab-width: 4    :linenos:    :language: guess
