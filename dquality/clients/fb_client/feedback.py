import dquality.common.constants as const
import dquality.clients.fb_client.pv_feedback as pv_fb
import dquality.clients.fb_client.pv_feedback_12 as pv_fb_12


class Feedback(object):
    """
    This class is a container of real-time feedback related information.
    """
    def __init__(self, q, feedback_type, **kwargs):
        """
        Constructor

        Parameters
        ----------
        feedback_type : list
            a list of configured feedbac types. Possible options: console, log, and pv
        """
        self.q = q
        self.feedback_type = feedback_type
        # create pv driver if pv feedback
        if const.FEEDBACK_PV in self.feedback_type:
            # base support
            self.pv = pv_fb.PV_FB(**kwargs)
        elif const.FEEDBACK_PV_12 in self.feedback_type:
            # customized support for beamline12
            self.pv = pv_fb_12.PV_FB_12(**kwargs)


    def set_logger(self, logger):
        """
        This function sets logger.

        Parameters
        ----------
        logger : Logger
            an instance of Logger
        """
        self.logger = logger


    def deliver(self):
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
        self.pv.start_driver() #in the same process
        evaluating = True
        while evaluating:
            results = self.q.get()

            if results == const.DATA_STATUS_END:
                evaluating = False
            elif results == const.DATA_STATUS_MISSING:
                pass
            else:
                if results.failed:
                    for result in results.results:
                        if result.error != 0:
                            # for console and log feedback deliver only the errors
                            if const.FEEDBACK_CONSOLE in self.feedback_type:
                                print ('failed frame ' + str(results.index) + ' result of ' +
                                       result.quality_id + ' is ' + str(result.res))
                            if const.FEEDBACK_LOG in self.feedback_type:
                                self.logger.info('failed frame ' + str(results.index) + ' result of ' +
                                                 result.quality_id + ' is ' + str(result.res))
                if not self.pv is None:
                    self.pv.write_to_pv(results)

