from multiprocessing import Lock
import dquality.common.constants as const
from multiprocessing import Process
import importlib
from os import path
import sys


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
    This class is a container of results of all quality checks for a single frame, and a flag indicating if all
    quality checks passed.
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
    This class is a container of data. One of the members is a 2D arrray. Other members will be added later
    """
    def __init__(self, status, slice=None, type=None):
        self.status = status
        if status == const.DATA_STATUS_DATA:
            self.slice = slice
            self.type = type


class Feedback:
    """
    This class is a container of real-time feedback related information.
    """
    def __init__(self, feedback_type, ):
        self.feedback_type = feedback_type

    def set_feedback_pv(self, feedback_pv):
        self.feedback_pv = feedback_pv

    def set_logger(self, logger):
        self.logger = logger

    def set_driver(self, driver):
        self.driver = driver


class Aggregate:
    """
    This class is a container of results. The results are organized in three dictionaries.
    "bad_indexes": dictionary contains keys that are indexes of slices that not pass one or more quality checks.
    The values are results organized in dictionaries, where the keays are quality check method index.
    "good_indexes" is a similarly organized dictionary that contains indexes for which all quality checks passed.
    "results": a dictionary keyed by quality check id and a value of list of all results for "good" indexes.

    The class has locks, for each quality check type. The lock are used to access the results. One thread is adding
    to the results, and another thread (statistical checks) are reading the stored data to do statistical calculations.

    """

    def __init__(self, data_type, quality_checks, feedbackq, feedback_obj = None):
        self.data_type = data_type
        if feedback_obj is not None:
            self.feedback_type = feedback_obj.feedback_type
            self.feedbackq = feedbackq
            #TODO check if feedback_pv and save
            # start process that will provide continuous feedback
            p = Process(target=self.quality_feedback, args=(self.feedbackq, feedback_obj,))
            p.start()
        else:
            self.feedback_type = None

        self.bad_indexes = {}
        self.good_indexes = {}

        self.results = {}
        self.lock = Lock()
        self.lens = {}
        for qc in quality_checks:
            self.results[qc] = []
            self.lens[qc] = 0


    def get_results(self, check):
        """
        This returns current length of the results of a given quality check. This operation uses lock, as other
        process writes new results.

        Parameters
        ----------
        check : int
            a value indication quality check id

        Returns
        -------
        int
            the length of the results list for the given quality check
        """
        self.lock.acquire()
        res = self.results[check]
        self.lock.release()
        return res


    def add_result(self, result, check):
        """
        This add a new result for a given quality check to results. This operation uses lock, as other
        process reads the length.

        Parameters
        ----------
        result : Result
            a result instance

        check : int
            a value indication quality check id

        Returns
        -------
        None
        """
        self.lock.acquire()
        self.results[check].append(result)
        self.lens[check] += 1
        self.lock.release()


    def handle_results(self, results):
        def deep_copy(frame_results):
            res = {}
            for result in frame_results:
                res[result.quality_id] = result.res
            return res

        if results.failed:
            self.bad_indexes[results.index] = deep_copy(results.results)
            if self.feedback_type is not None:
                for result in results.results:
                    if result.error != 0:
                        result.index = results.index
                        self.feedbackq.put(result)
        else:
            self.good_indexes[results.index] = deep_copy(results.results)
            for result in results.results:
                self.add_result(result.res, result.quality_id)


    def quality_feedback(self, feedbackq, feedback_obj):
        """
        This function take a result instance that contains information about the result and the subject. If the
        slice did not pass verification for any of the quality check, it will return False. If all quality checks
        passed it will return True. The function maintains the containers; the slice index will be added to a
        "good_index" dictionary if all quality checks passed, and to "bad_index" otherwise.

        Parameters
        ----------
        feedbackq : Queue
            a queue that will deliver Result objects of failed quality check

        feedback_obj : Feedback
            a Feedback instance that contains all information for real-time feedback

        Returns
        -------
        boolean
            True if all quelity checks passed
            False otherwise
        """

        evaluating = True
        while evaluating:
            result = feedbackq.get()
            if result == const.DATA_STATUS_END:
                evaluating = False
            else:
                if const.FEEDBACK_CONSOLE in feedback_obj.feedback_type:
                    print ('failed frame '+str(result.index)+ ' result of '+const.check_tostring(result.quality_id)+ ' is '+ str(result.res))
                if const.FEEDBACK_LOG in feedback_obj.feedback_type:
                    feedback_obj.logger.info('failed frame '+str(result.index)+ ' result of '+const.check_tostring(result.quality_id)+ ' is '+ str(result.res))
                if const.FEEDBACK_PV in feedback_obj.feedback_type:
                    print ('pv feedback not supported yet')

    def is_empty(self):
        return len(self.bad_indexes) == 0 and len(self.good_indexes) == 0


class Consumer_adapter():
    """
    This class provides file discovery functionality. An instance is initialized with parameters.
    On the start the FileSeek checks for existing files. After that it periodically checks
    for new files in monitored directory and subdirectories. Upon finding a new or updated file it
    velidates the file and enqueues into the queue on success.
    """

    def __init__(self, module_path):
        """
        constructor

        Parameters
        ----------
        q : Queue
            a queue used to pass discovered files

        polling_period : int
            number of second defining polling period

        logger : Logger
            logger instance

        file_type : int
            a constant defining type of data file. Supporting FILE_TYPE_GE and FILE_TYPE_HDF
        """
        sys.path.append(path.abspath(module_path))

    def start_process(self, q, module, args):
        mod = importlib.import_module(module)
        p = Process(target=mod.consume, args=(q, args,))
        p.start()


