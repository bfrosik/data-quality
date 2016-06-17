=====About=====Data Quality assurance is an essential task to provide consistency, accuracy, reliability and reproducibility of scientific results :cite:`DataQuality`, :cite:`Hansen`, :cite:`Goldman2007`, :cite:`MohammadiES14`.

`DQuality <https://github.com/bfrosik/data-quality>`_ is a python toolbox to asses the quality of raw and processed data collected at the Advanced Photon Source (APS).

`DQuality <https://github.com/bfrosik/data-quality>`_ verifies that all experiment components `EPICS <http://www.aps.anl.gov/epics/>`_ Process Variables (PVs) 
like motor positions, storage ring parameters etc. are valid and their values are within a predefined range.

`DQuality <https://github.com/bfrosik/data-quality>`_ verifies that the raw data files saved in the `Data Exchange  <http://dxfile.readthedocs.io>`_ hdf5 file format contain a valid data and meta-data structure and that existing dependencies between the data and meta-data structure are correct.

`DQuality <https://github.com/bfrosik/data-quality>`_ provides live monitoring of the above functionalities for all raw data created in the active directory.

