import dquality.common.constants as const
import dquality.common.utilities as utils
from epics import caput, caget


class Feedback(object):
    """
    This class is a container of real-time feedback related information.
    """

    def __init__(self,feedback, detector, quality_checks, logger):
        """
        Constructor

        Parameters
        ----------
        feedback_type : list
            a list of configured feedbac types. Possible options: console, log, and pv
        """

        self.feedback_type = feedback
        if const.FEEDBACK_PV in self.feedback_type:
            self.detector = detector
            #zero out the ctr pvs
            feedback_pvs = utils.get_feedback_pvs(quality_checks)
            for fb_pv in feedback_pvs:
                caput(self.detector + ':data_' + fb_pv + '_ctr', 0)

        if const.FEEDBACK_LOG in self.feedback_type:
            self.logger = logger


    def deliver(self, results):
        """
        This function provides feedback as defined by the feedback_type in a real time.

        If the feedback type contains pv type, this function creates server and initiates driver handling the feedback
        pvs.It dequeues results from the 'q' queue and processes all feedback types that have been configured.
        It will stop processing the queue when it dequeues data indicating end status.

        Parameters
        ----------
        none

        Returns
        -------
        none
        """
        if results.failed:
            for result in results.results:
                if result.error != 0:
                    # for console and log feedback deliver only the errors
                    if const.FEEDBACK_CONSOLE in self.feedback_type:
                        print('failed frame ' + str(results.index) + ' result of ' +
                              result.quality_id + ' is ' + str(result.res))
                    if const.FEEDBACK_LOG in self.feedback_type:
                        self.logger.info('failed frame ' + str(results.index) + ' result of ' +
                                         result.quality_id + ' is ' + str(result.res))
                    if const.FEEDBACK_PV in self.feedback_type:
                        pv = self.detector + ':' + results.type + '_' + result.quality_id
                        caput(pv + '_res', result.res)
                        counter = caget(pv + '_ctr') + 1
                        caput(pv + '_ctr', counter)

