API reference
=============

`DQuality <https://github.com/bfrosik/data-quality>`_ provides the following funtionalities:

    - "*PV*": Before data collection start, verify that the experiment setup PVs, i.e. all required setup data,  are valid and their values are within a predefined range. 

    - "*Hdf*": verify the correctness of the data and meta-data structure in an hdf5 file.

    - "*Hdf Dependencies*": verify dependencies between the data and meta-data structure in an hdf5 file.

    - "*Data*": verify the quality of the data after data is collected in a file. A set of QC functions is provided to assess the image quality against different criteria (mean, dynamic range, structural similarity, multi-scale structural similarity, visual information fidelity, most apparent distortion, etc.) :cite:`MohammadiES14`. The resulting "*limit*", related to the quantitive QC functions, defines whether the data is of good or poor quality. The limit values, at first, are set by the research/tests with trial data sets. The QC function "*limit*" range will eventually be learned by implementing a learning mechanism. Any calculated "*result*" quality parameter is stored, in the case of hdf format, in the file itself with a corresponding tag. If the data file format supports only raw data (no meta-data), the quality parameter results are stored in a separate file with a name corresponding to the data file.

    - "*Monitor*", "*Monitor_polling*": monitor the active data collection directory and run "*Data*" on each new file.
    
    - "*Accumulator*": monitor the active data collection directory where each new file is part of the same data set.

    - "*Realtime*": verifies the quality of the active EPICS Channel Access data in a real time.

    - "*Check*": provides a wrapper to "*PV*", "*Hdf*", "*Hdf Dependencies*", "*Data*", "*Monitor*", and "*Accumulator*".

    - "*realtime.Check*": provides a wrapper to "*Realtime*".

.. rubric:: **DQuality Modules:**

.. toctree::

   api/dquality.realtime.real_time
   api/dquality.realtime.check

.. automodule:: dquality.realtime
   :members:
   :undoc-members:
   :show-inheritance:

.. toctree::

   api/dquality.accumulator
   api/dquality.check
   api/dquality.data
   api/dquality.hdf
   api/dquality.hdf_dependency
   api/dquality.monitor
   api/dquality.pv

.. automodule:: dquality
   :members:
   :undoc-members:
   :show-inheritance: 

