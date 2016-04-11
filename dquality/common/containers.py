from multiprocessing import Lock
import dquality.common.constants as const

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
    locks = {const.QUALITYCHECK_MEAN : Lock(), const.QUALITYCHECK_STD : Lock(), const.STAT_MEAN : Lock()}
    lens = {const.QUALITYCHECK_MEAN : 0, const.QUALITYCHECK_STD : 0, const.STAT_MEAN : 0}

    def __init__(self):
        self.bad_indexes = {}
        self.good_indexes = {}
        self.results = {const.QUALITYCHECK_MEAN : [], const.QUALITYCHECK_STD : [], const.STAT_MEAN : []}

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

    def handle_result(self,result):
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
        return res
