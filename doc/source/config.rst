============
Cofiguration
============

This describes configuration mandatory/optional parameters common to all verifiers, and then additional parameters
for each verifier.

    - common:
'log_file' - optional, a log file name including path. If not specified, the log file default.log will be
             created in the running directory
'time_zone'  - optional, time zone that will be displayed as part of timestamp in log file. If not specified,
               it defaults to 'America/Chicago'

    - pv verifier:
'pv_file' - mandatory, json file name including path that specifies pv requirements

    - hdf verifier:
'schema' - mandatory, json file name including path that specifies hdf tags requirements
'verification_type' - optional. Currently the software supports 'hdf_structure' and 'hdf_tags' types. If not
              specified it defaults to 'hdf_structure' type. When configured to 'hdf_structure' the tags and
              attributes specified in 'schema' file will be evaluated. If configured to 'hdf_tags', only presence
              of the tags specified in 'schema' file will be evaluated.

    - dependency verifier:
'dependencies' - mandatory, json file name including path that specifies hdf tags dependency requirements

    - data verifier:
'limits' - mandatory, json file name including path that specifies limits used in quality checks
'quality_checks' - mandatory, json file name including path that lists all quality methods that will be used
                   to validate the data.
'file_type' - optional, data file type. Currently the software supports FILE_TYPE_GE and FILE_TYPE_HDF formats. If not
              specified it defaults to FILE_TYPE_HDF format.
'data_tags' - required for hdf type file. json file name including path that maps hdf tags
              to data types ('data', 'data_dark', 'data_white') that will be verified.
'report_type' - optional, defines report specifics. Currently the software supports 'REPORT_NONE', 'REPORT_FULL', and
                'REPORT_ERRORS' types. If not specified it defaults to 'REPORT_FULL' type. If the type is 'REPORT_NONE',
                no report file will be created; if the type is 'REPORT_ERRORS', only the bad frames will be reported;
                and for the 'REPORT_FULL' report type all frames and check results are reported.
'feedback_type' - optional, defines a real time feedback when validating data. For data verifier it should not be set,
                  or set to "FEEDBACK_NONE'

    - monitor:
'limits' - mandatory, json file name including path that specifies limits used in quality checks
'quality_checks' - mandatory, json file name including path that lists all quality methods that will be used
                   to validate the data.
'file_type' - optional, data file type. Currently the software supports FILE_TYPE_GE and FILE_TYPE_HDF formats. If not
              specified it defaults to FILE_TYPE_HDF format.
'data_tags' - optional, but required for hdf type file. json file name including path that maps hdf tags
              to data types ('data', 'data_dark', 'data_white') that will be verified.
'report_type' - optional, defines report specifics. Currently the software supports 'REPORT_NONE', 'REPORT_FULL', and
                'REPORT_ERRORS' types. If not specified it defaults to 'REPORT_FULL' type. If the type is 'REPORT_NONE',
                no report file will be created; if the type is 'REPORT_ERRORS', only the bad frames will be reported;
                and for the 'REPORT_FULL' report type all frames and check results are reported.
'feedback_type' - optional, defines a real time feedback when validating data. For monitor it should not be set, or
                  set to "FEEDBACK_NONE'
'extensions' - optional, file extentions to minitor for. If not specified, it monitors for all types of files.

    - accumulator:
'limits' - mandatory, json file name including path that specifies limits used in quality checks
'quality_checks' - mandatory, json file name including path that lists all quality methods that will be used
                   to validate the data.
'report_type' - optional, defines report specifics. Currently the software supports 'REPORT_NONE', 'REPORT_FULL', and
                'REPORT_ERRORS' types. If not specified it defaults to 'REPORT_FULL' type. If the type is 'REPORT_NONE',
                no report file will be created; if the type is 'REPORT_ERRORS', only the bad frames will be reported;
                and for the 'REPORT_FULL' report type all frames and check results are reported.
'feedback_type' - optional, defines a real time feedback when validating data. For accumulator it should not be set, or
                  set to "FEEDBACK_NONE'

    - real_time verifier:
'limits' - mandatory, json file name including path that specifies limits used in quality checks
'quality_checks' - mandatory, json file name including path that lists all quality methods that will be used
                   to validate the data.
'report_type' - optional, defines report specifics. Currently the software supports 'REPORT_NONE', 'REPORT_FULL', and
                'REPORT_ERRORS' types. If not specified it defaults to 'REPORT_FULL' type. If the type is 'REPORT_NONE',
                no report file will be created; if the type is 'REPORT_ERRORS', only the bad frames will be reported;
                and for the 'REPORT_FULL' report type all frames and check results are reported.
'feedback_type' - optional, defines a real time feedback when validating data. Currently the software supports
                  'FEEDBACK_NONE', 'FEEDACK_PRINT', 'FEEDBACK_PV', and 'FEEDBACK_PRINT_PV'. If not specified it
                  defaults to 'FEEDBACK_NONE'. If the type is 'FEEDBACK_PRINT', the software will print the verification
                  results in the real time; if the type is 'FEEDBACK_PV', the software gives feedback via PVs;
                  and for the 'FEEDBACK_PRINT_PV' the feedback is given via PVs and print.
'detector' - mandatory, specifies EPICS Area Detector prefix, as defined in the area detector configuration
'detector_basic' - mandatory, specifies EPICS Area Detector second prefix that is used for the basic PVs, as defined
                   in the area detector configuration
'detector_image' - mandatory, specifies EPICS Area Detector second prefix that is used for the image PVs, as defined
                   in the area detector configuration
'no_frames' - mandatory, number of frames that the real time verifier will evaluate. It will run undefinately when set
              to -1.

