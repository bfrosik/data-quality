API reference
=============

`DQuality <https://github.com/bfrosik/data-quality>`_ provides the following funtionalities:
    - "*PV*": Before data collection start, `DQuality <https://github.com/bfrosik/data-quality>`_ verifies that the experiment setup PVs, i.e. all required setup data,  are valid and their values are within a predefined range.     - "*File*": `DQuality <https://github.com/bfrosik/data-quality>`_ verifies the quality of the data and meta-data structure after all data is collected and during the data processing steps.
    - "*Data*": `DQuality <https://github.com/bfrosik/data-quality>`_ verifies the quality of the data after all data is collected and during the data processing steps. A set of QC functions is provided to assess the image quality against different criteria (mean, dynamic range, structural similarity, multi-scale structural similarity, visual information fidelity, most apparent distortion, etc.) :cite:`MohammadiES14`. The resulting "*index*", related to the quantitive QC functions, defines whether the data is of good or poor quality. The index values, at first, are set by the research/tests with trial data sets. The QC function "*index*" range will eventually be learned by implementing a learning mechanism. Any calculated "*index*" quality parameter is stored, in the case of hdf format, in the file itself with a corresponding tag. If the data file format supports only raw data (no meta-data), the quality parameter results are stored in a separate file with a name corresponding to the data file. In both cases the experiment user receives visual feedback on the data quality.
    
    - "*Monitor*": `DQuality <https://github.com/bfrosik/data-quality>`_ is able to monitor the "*File*" and "*Data*" quality during data collection.    - "*Dependencies*": ......

.. rubric:: **DQuality Modules:**

.. toctree::

   api/dquality.pv
   api/dquality.file
   api/dquality.data
   api/dquality.monitor
   api/dquality.dependency

.. automodule:: dquality
   :members:
   :undoc-members:
   :show-inheritance: 
