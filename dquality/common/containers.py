from multiprocessing import Lock
import dquality.common.constants as const
from multiprocessing import Process
import importlib
from os import path
import sys
import dquality.realtime.pv_feedback_driver as drv
if sys.version[0] == '2':
    import thread as thread
else:
    import _thread as thread


class Result:
    """
    This class is a container of result and parameters linked to the subject of the verification, and the
    verification type.
    """
    def __init__(self, res, quality_id, error):
        self.res = res
        self.quality_id = quality_id
        self.error = error


class Results:
    """
    This class is a container of results of all quality checks for a single frame, and attributes such as flag
    indicating if all quality checks passed, dat type, and index.
    """
    def __init__(self, type, index, failed, results):
        self.type = type
        self.index = index
        self.failed = failed
        self.results = []
        for qc in results:
            self.results.append(results[qc])


class Data:
    """
    This class is a container of data.
    """
    def __init__(self, status, slice=None, type=None, acq_time = None):
        self.status = status
        if status == const.DATA_STATUS_DATA:
            self.slice = slice
            self.type = type
            if acq_time is not None:
                self.acq_time = acq_time


class Feedback:
    """
    This class is a container of real-time feedback related information.
    """
    def __init__(self, feedback_type, ):
        """
        Constructor

        Parameters
        ----------
        feedback_type : list
            a list of configured feedbac types. Possible options: console, log, and pv
        """
        self.feedback_type = feedback_type

    def set_feedback_pv(self, feedback_pvs, detector):
        """
        This function sets feedback_pvs, and detector fields.

        Parameters
        ----------
        feedback_pvs : list
            a list of feedback process variables names, for each data type combination with the
            applicable quality check
        detector : str
            a pv name of the detector
        """
        self.feedback_pvs = feedback_pvs
        self.detector = detector

    def set_logger(self, logger):
        """
        This function sets logger.

        Parameters
        ----------
        logger : Logger
            an instance of Logger
        """
        self.logger = logger

    def set_driver(self, driver):
        """
        This function sets driver.

        Parameters
        ----------
        driver : FbDriver
            an instance of FbDriver
        """
        self.driver = driver

    def write_to_pv(self, pv, index):
        """
        This function calls write method on driver field to update pv.

        Parameters
        ----------
        pv : str
            a name of the pv, contains information about the data type and quality check (i.e. data_white_mean)
        index : int
            index of failed frame
        """
        self.driver.write(pv, index)

    def quality_feedback(self, feedbackq):
        """
        This function provides feedback as defined by the feedback_type in a real time.

        If the feedback type contains pv type, this function creates server and initiates driver handling the feedback
        pvs.It dequeues results from the 'feedbackq' queue and processes all feedback types that have been configured.
        It will stop processing the queue when it dequeues data indicating end status.

        Parameters
        ----------
        feedbackq : Queue
            a queue that will deliver Result objects of failed quality check

        Returns
        -------
        none
        """
        if const.FEEDBACK_PV in self.feedback_type:
            server = drv.FbServer()
            driver = server.init_driver(self.detector, self.feedback_pvs)
            thread.start_new_thread(server.activate_pv, ())
            self.set_driver(driver)

        evaluating = True
        while evaluating:
            while not feedbackq.empty():
                try:
                    result = feedbackq.get_nowait()
                    if result == const.DATA_STATUS_END:
                        evaluating = False
                    else:
                        if const.FEEDBACK_CONSOLE in self.feedback_type:
                            print ('failed frame '+str(result.index)+ ' result of '+const.to_string(result.quality_id)+ ' is '+ str(result.res))
                        if const.FEEDBACK_LOG in self.feedback_type:
                            self.logger.info('failed frame '+str(result.index)+ ' result of '+const.to_string(result.quality_id)+ ' is '+ str(result.res))
                        if const.FEEDBACK_PV in self.feedback_type:
                            quality_check = const.to_string(result.quality_id)
                            self.write_to_pv(result.type + '_' + quality_check, result.index)
                except:
                    pass


class Aggregate:
    """
    This class is a container of results.

    The results are organized in three dictionaries.
    "bad_indexes": dictionary contains keys that are indexes of slices that not pass one or more quality checks.
    The values are results organized in dictionaries, where the keays are quality check method index.
    "good_indexes" is a similarly organized dictionary that contains indexes for which all quality checks passed.
    "results": a dictionary keyed by quality check id and a value of list of all results for "good" indexes.

    The class has locks, for each quality check type. The lock are used to access the results. One thread is adding
    to the results, and another thread (statistical checks) are reading the stored data to do statistical calculations.

    """

    def __init__(self, data_type, quality_checks, aggregate_limit, feedbackq = None):
        """
        Constructor

        Parameters
        ----------
        data_type : str
            data type related to the aggregate
        quality_checks : list
            a list of quality checks that apply for this data type
        feedbackq : Queue
            optional, if the real time feedback is requested, the queue will be used to pass results to the process
            responsible for delivering the feedback in areal time
        """
        self.data_type = data_type
        self.feedbackq = feedbackq
        self.aggregate_limit = aggregate_limit

        self.bad_indexes = {}
        self.good_indexes = {}

        self.results = {}
        self.lock = Lock()
        for qc in quality_checks:
            self.results[qc] = []


    def get_results(self, check):
        """
        This returns the results of a given quality check.

        This operation uses lock, as other process writes to results.

        Parameters
        ----------
        check : int
            a value indication quality check id

        Returns
        -------
        res : list
            a list containing results that passed the given quality check
        """
        self.lock.acquire()
        res = self.results[check]
        self.lock.release()
        return res


    def add_result(self, result, check):
        """
        This add a new result for a given quality check to results.

        This operation uses lock, as other process reads the results.

        Parameters
        ----------
        result : Result
            a result instance

        check : int
            a value indication quality check id

        Returns
        -------
        none
        """
        self.lock.acquire()
        self.results[check].append(result)
        self.lock.release()


    def handle_results(self, results):
        """
        This handles all results for one frame.

        If the flag indicates that at least one quality check failed the index will be added into 'bad_indexes'
        dictionary, otherwise into 'good_indexes'. It also delivers the failed results to the feedback process
        using the feedbackq, if real time feedback was requasted.

        Parameters
        ----------
        result : Result
            a result instance

        check : int
            a value indication quality check id

        Returns
        -------
        none
        """
        def send_feedback():
            if self.feedbackq is not None:
                for result in results.results:
                    if result.error != 0:
                        result.index = results.index
                        result.type = results.type
                        self.feedbackq.put(result)

        if self.aggregate_limit == -1:
            if results.failed:
                send_feedback()
        else:
            if results.failed:
                self.bad_indexes[results.index] = results.results
                send_feedback()
            else:
                self.good_indexes[results.index] = results.results
                for result in results.results:
                    self.add_result(result.res, result.quality_id)


    def is_empty(self):
        """
        Returns True if the fields are empty, False otherwise.

        Parameters
        ----------
        none

        Returns
        -------
        True if empty, False otherwise
        """
        return len(self.bad_indexes) == 0 and len(self.good_indexes) == 0


class Consumer_adapter():
    """
    This class is an adapter starting consumer process.
    """

    def __init__(self, module_path):
        """
        constructor

        Parameters
        ----------
        module_path : str
            a path where the consumer module is installed
        """
        sys.path.append(path.abspath(module_path))

    def start_process(self, q, module, args):
        """
        This function starts the consumer process.

        It first imports the consumer module, and starts consumer process.

        Parameters
        ----------
        q : Queue
            a queue on which the frames will be delivered
        module : str
            the module that needs to be imported
        args : list
            a list of arguments required by the consumer process
        """
        mod = importlib.import_module(module)
        status_def = [const.DATA_STATUS_DATA, const.DATA_STATUS_MISSING, const.DATA_STATUS_END]
        p = Process(target=mod.consume, args=(q, status_def, args,))
        p.start()


