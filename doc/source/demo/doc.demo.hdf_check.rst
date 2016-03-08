HDF File
========


This module requires the "*schema*" section of the
:download:`dqconfig.ini <../config/dqconfig.ini>` file to be set.
If "*schema*" is not configured, the function returns True, as no verification is needed.

In case the "*verification_type*" of the
:download:`dqconfig.ini <../config/dqconfig.ini>` file
is set, the follow up logic determines, what type of verification should be applied.

Currently, for the HDF schema, both "*hdf_structure*" and "*hdf_tags*" verification types are supported.

DQuality HDF file check example. (Download file: :download:`hdf_check.py<../../../doc/demo/hdf_check.py>`)

.. literalinclude:: ../../../doc/demo/hdf_check.py    :tab-width: 4    :linenos:    :language: guess
