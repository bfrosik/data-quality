Howto
=====

This file provides instructions how to use the framework to add more features.

How to define quality check functions in quality_checks.json file.

This framework classifies two types of quality checks: the frame verification check, and statistical check.
Frame verification check calculates characteristic of a given frame (for example mean value) and tests the result against limits.
Statistical quality check uses previously stored results of frame verification check to evaluate the current result.

Follow the steps below to add a frame verification check:
- add the method in dquality.common.qualitychecks.py file. The signature should be: function_name(data, index, results, all_limits). Look at the example method "validate_mean_signal_intensity" for the meaning of the parameters.
- define quality id in a dquality/common/constants.py file that is unique in respect to other quality checks constants, and update mapper in the constants.py file. The constant value should be less than 100.
- add a dictionary entry to the quality_checks.json file where key is the string representation of a constant defining the method, and value is an empty list.

 Follow the steps below to add a statistical quality check:
- add the method to dquality/common/qualitychecks.py file. The signature should be: function_name(result, aggregate, results, all_limits). Look at the example statistical method "validate_stat_mean" for the meaning of the parameters.
- define quality id in a dquality/common/constants.py file that is unique in respect to other  quality checks constants, and update mapper in the constants.py file. The constant value should be greater or equal 100.
- find a key of the frame verification check that the statistical check uses, and add an entry to the corresponding list, where the entry is  a a constant defining the statistical check method.

example:

The following quality_checks.json file { "QUALITYCHECK_MEAN" : ["STAT_MEAN"], "QUALITYCHECK_STD" : []} defines that each frame will be verified by frame verification functions:
defined by constants: QUALITYCHECK_MEAN, and QUALITYCHECK_STD. Right aftre a frame is evaluated with QUALITYCHECK_MEAN, the statistical quality check STAT_MEAN evaluates the frame further, using the previous results.
