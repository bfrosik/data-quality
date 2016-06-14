Howto
=====

This file provides instructions how to use the framework to add more features.

How to add a statistical quality check.

Statistical quality check uses previously stored results to evaluate the current result. Follow the steps below.
- add your method to dquality/common/qualitychecks.py file. The signature should be: function_name(result, aggregate, results, all_limits). Look at the example statistical method "validate_stat_mean" for the meaning of the parameters.

- define quality id in a dquality/common/constants.py file (for example STAT_MEAN = 3) that is unique in respect to other  quality checks constants.

- update function_mapper dictionary in the dquality/handler.py file. If the statistical method uses mean values, it should be added to the list with the const.QUALITYCHECK_MEAN, if the method uses standard deviation values, it should be added to the list with the const.QUALITYCHECK_STD.

- add import "from dquality.common.qualitychecks import validate_stat_mean" in dquality/handler.py file.
