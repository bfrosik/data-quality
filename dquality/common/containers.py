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
    This class is a container of results of all quality checks for a single frame, and attributes such as flag
    indicating if all quality checks passed, dat type, and index.
    """
    def __init__(self, type, index, failed, results, text=None):
        self.text = text
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
    def __init__(self, status, slice=None, type=None, **kwargs):
        self.status = status
        if status == const.DATA_STATUS_DATA:
            self.slice = slice
            self.type = type
            for key in kwargs:  # styles is a regular dictionary
                setattr(self, key, kwargs[key])


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

    def __init__(self, data_type, quality_checks, **kwargs): #data_type, quality_checks, aggregate_limit=0, feedbackq = None):
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
        try:
            self.feedbackq = kwargs['feedbackq']
        except KeyError:
            self.feedbackq = None

        try:
            self.aggregate_limit = kwargs['aggregate_limit']
        except KeyError:
            self.aggregate_limit = -1

        self.bad_indexes = {}
        self.good_indexes = {}

        self.results = {}
        for qc in quality_checks:
            self.results[qc] = []


    def get_results(self, check):
        """
        This returns the results of a given quality check.

        Parameters
        ----------
        check : int
            a value indication quality check id

        Returns
        -------
        res : list
            a list containing results that passed the given quality check
        """
        res = self.results[check]
        return res


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
        if self.aggregate_limit == -1:
            if self.feedbackq is not None:
                self.feedbackq.put(results)
        else:
            if results.failed:
                self.bad_indexes[results.index] = results.results
                if self.feedbackq is not None:
                    self.feedbackq.put(results)
            else:
                self.good_indexes[results.index] = results.results
                for result in results.results:
                    self.results[result.quality_id].append(result)


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


