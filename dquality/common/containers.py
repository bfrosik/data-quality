from multiprocessing import Lock
import dquality.common.constants as const
from multiprocessing import Queue, Process

class Result:
    """
    This class is a container of result and parameters linked to the subject of the verification, and the
    verification type.
    """
    def __init__(self, res, index, quality_id, error):
        self.res = res
        self.index = index
        self.quality_id = quality_id
        self.error = error

class Data:
    """
    This class is a container of data. One of the members is a 2D arrray. Other members will be added later
    """
    def __init__(self, slice, ):
        self.slice = slice

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

    def __init__(self, quality_checks, feedbackq, feedback_obj = None):
        if feedback_obj is not None:
            self.feedback_type = feedback_obj.feedback_type
            self.feedbackq = feedbackq
            #TODO check if feedback_pv and save
            # start process that will update epics Quality PVs
            p = Process(target=self.quality_feedback, args=(self.feedbackq, feedback_obj,))
            p.start()
        else:
            self.feedback_type = None

        self.bad_indexes = {}
        self.good_indexes = {}
        methods = []
        for qc in quality_checks:
            methods.append(qc)
            for sqc in quality_checks[qc]:
                methods.append(sqc)

        self.results = {}
        self.locks = {}
        self.lens = {}
        for qc in methods:
            self.results[qc] = []
            self.locks[qc] = Lock()
            self.lens[qc] = 0


    def get_results_len(self, check):
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
        lock = self.locks[check]
        lock.acquire()
        length = self.lens[check]
        lock.release()
        return length


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
        lock = self.locks[check]
        lock.acquire()
        self.results[check].append(result)
        self.lens[check] += 1
        lock.release()


    def all_good_on_result(self, result):
        """
        This function take a result instance that contains information about the result and the subject. If the
        slice did not pass verification for any of the quality check, it will return False. If all quality checks
        passed it will return True. The function maintains the containers; the slice index will be added to a
        "good_index" dictionary if all quality checks passed, and to "bad_index" otherwise.

        Parameters
        ----------
        result : Result
            a result instance

        Returns
        -------
        boolean
            True if all quelity checks passed
            False otherwise
        """
        res = False
        index = result.index
        if result.error is const.NO_ERROR:
            bad_index = self.bad_indexes.get(index)
            if bad_index is None:
                res = True
                good_index = self.good_indexes.get(index)
                if good_index is None:
                    entry = {result.quality_id : result.res}
                    self.good_indexes[index] = entry
                else:
                    good_index[result.quality_id] = result.res
                self.add_result(result.res, result.quality_id)
            else:
                bad_index[result.quality_id] = result.res
        else:
            good_index = self.good_indexes.get(index)
            if good_index is None:
                bad_index = self.bad_indexes.get(index)
                if bad_index is None:
                    entry = {result.quality_id : result.res}
                    self.bad_indexes[index] = entry
                else:
                    bad_index[result.quality_id] = result.res
            else:
                self.good_indexes.pop(index)
                bad_index = good_index
                bad_index[result.quality_id] = result.res
                self.bad_indexes[index] = bad_index

        if not res and self.feedback_type is not None:
            self.feedbackq.put(result)

        return res


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
            if result == 'all_data':
                evaluating = False
            else:
                if const.FEEDBACK_CONSOLE in feedback_obj.feedback_type:
                    print ('failed frame '+str(result.index)+ ' result of '+const.check_tostring(result.quality_id)+ ' is '+ str(result.res))
                if const.FEEDBACK_LOG in feedback_obj.feedback_type:
                    feedback_obj.logger.info('failed frame '+str(result.index)+ ' result of '+const.check_tostring(result.quality_id)+ ' is '+ str(result.res))
                if const.FEEDBACK_PV in feedback_obj.feedback_type:
                    print ('pv feedback not supported yet')


