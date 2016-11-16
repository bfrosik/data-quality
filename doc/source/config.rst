============
Cofiguration
============

This describes configuration of mandatory and optional parameters. The common section depicts parameters used by all
verifiers. A list of additional parameters specific for each verifier follows.

--------------------
common configuration
--------------------
- 'log_file':
optional, a log file name including path. If not specified, the log file default.log will be created in the running
directory

- 'time_zone':
optional, time zone that will be displayed as part of timestamp in log file. If not specified, it defaults to
'America/Chicago'

-----------
pv verifier
-----------
- 'pv_file':
mandatory, json file name including path that specifies pv requirements

------------
hdf verifier
------------
- 'schema':
mandatory, json file name including path that specifies hdf tags requirements

- 'verification_type':
optional. Currently the software supports 'hdf_structure' and 'hdf_tags' types. If not specified it defaults to
'hdf_structure' type. When configured to 'hdf_structure' the tags and attributes specified in 'schema' file will be
evaluated. If configured to 'hdf_tags', only presence of the tags specified in 'schema' file will be evaluated.

-------------------
dependency verifier
-------------------
- 'dependencies':
mandatory, json file name including path that specifies hdf tags dependency requirements

-------------
data verifier
-------------
- 'limits':
mandatory, json file name including path that specifies limits used in quality checks 'quality_checks': mandatory,
json file name including path that lists all quality methods that will be used to validate the data.

- 'file_type':
optional, data file type. Currently the software supports FILE_TYPE_GE and FILE_TYPE_HDF formats. If not specified it
defaults to FILE_TYPE_HDF format.

- 'data_tags':
required for hdf type file. json file name including path that maps hdf tags to data types ('data', 'data_dark','data_white') that will be verified.

- 'report_type':
optional, defines report specifics. Currently the software supports 'none', 'full', and 'errors' types. If not specified it defaults to 'full' type. If the type is 'none', no report file will be created; if the type is 'errors', only the bad frames will be reported; and for the 'full' report type all frames and check results are reported.

- 'report_dir':
optional, a directory where report files will be located. If not configured, the report files are created along the data files.

- 'feedback_type':
optional, defines a real time feedback when validating data. For data verifier it should not be set, or set to
"none'

-------
monitor
-------
- 'limits':
mandatory, json file name including path that specifies limits used in quality checks 'quality_checks': mandatory,
json file name including path that lists all quality methods that will be used to validate the data.

- 'file_type':
optional, data file type. Currently the software supports FILE_TYPE_GE and FILE_TYPE_HDF formats. If not specified it
defaults to FILE_TYPE_HDF format.

- 'data_tags':
required for hdf type file. json file name including path that maps hdf tags to data types ('data', 'data_dark',
'data_white') that will be verified.

- 'report_type':
optional, defines report specifics. Currently the software supports 'none', 'full', and 'errors' types. If not specified it defaults to 'full' type. If the type is 'none', no report file will be created; if the type is 'errors', only the bad frames will be reported; and for the 'full' report type all frames and check results are reported.

- 'report_dir':
optional, a directory where report files will be located. If not configured, the report files are created along the data files.

- 'feedback_type':
optional, defines a real time feedback when validating data. For data verifier it should not be set, or set to
"none'

-----------
accumulator
-----------
- 'limits':
mandatory, json file name including path that specifies limits used in quality checks 'quality_checks': mandatory,
json file name including path that lists all quality methods that will be used to validate the data.

- 'quality_checks':
mandatory, json file name including path that lists all quality methods that will be used to validate the data.

- 'report_type':
optional, defines report specifics. Currently the software supports 'none', 'full', and 'errors' types. If not specified it defaults to 'full' type. If the type is 'none', no report file will be created; if the type is 'errors', only the bad frames will be reported; and for the 'full' report type all frames and check results are reported.

- 'feedback_type':
optional, defines a real time feedback when validating data. For data verifier it should not be set, or set to
"none'

------------------
real_time verifier
------------------
- 'limits':
mandatory, json file name including path that specifies limits used in quality checks 'quality_checks': mandatory,
json file name including path that lists all quality methods that will be used to validate the data.

- 'quality_checks':
mandatory, json file name including path that lists all quality methods that will be used to validate the data.

- 'report_type':
optional, defines report specifics. Currently the software supports 'none', 'full', and 'errors' types. If not specified it defaults to 'full' type. If the type is 'none', no report file will be created; if the type is 'errors', only the bad frames will be reported; and for the 'full' report type all frames and check results are reported.

- 'feedback_type':
optional, a list that defines a real time feedback when validating data. Currently the software supports 'log',
'console', and 'pv'. If the list contains 'console', the software will print the failed verification results in the real time; if the list contain 'log', the failed results will be logged. 

- 'detector':
mandatory, specifies EPICS Area Detector prefix, as defined in the area detector configuration

- 'detector_basic':
mandatory, specifies EPICS Area Detector second prefix that is used for the basic PVs, as defined in the area detector
configuration

- 'detector_image':
mandatory, specifies EPICS Area Detector second prefix that is used for the image PVs, as defined in the area detector
configuration

- 'no_frames':
mandatory, number of frames that the real time verifier will evaluate. It will run undefinately when set to -1.

