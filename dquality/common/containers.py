from multiprocessing import Lock
import dquality.common.constants as const
from multiprocessing import Process
from threading import Timer
import os
import stat


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

class FileSeek():
    """
    This class provides file discovery functionality. An instance is initialized with parameters.
    On the start the FileSeek checks for existing files. After that it periodically checks
    for new files in monitored directory and subdirectories. Upon finding a new or updated file it
    velidates the file and enqueues into the queue on success.
    """

    def __init__(self, q, polling_period, logger, file_type):
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
        self.q = q
        self.polling_period = polling_period
        self.processed_files = None
        self.logger = logger
        self.file_type = file_type
        self.done = False

    def get_files(self, folder, ext, discovered_files=None):
        """
        Finds files in a given directory and subdirectories.

        Parameters
        ----------
        folder : str
            a folder name that will be checked for files

        ext : list
            list of file extensions that will be discovered

        discovered_files : dict
            a dictionary to add the discovered files to

        Returns
        -------
        dict
            a dictionary with keys as files in a monitored folder and subdirectories
        """

        current_files = discovered_files
        if current_files is None:
            current_files = {}
        if os.path.isdir(folder):
            files = os.listdir(folder)
            for f in files:
                full_path = os.path.join(folder, f)
                if os.path.isfile(full_path):
                    match = False
                    for fext in ext:
                        if f.endswith(fext):
                            match = True
                    if match:
                        statResult = os.stat(full_path)
                        file_info = {}
                        file_info['fileSize'] = statResult[stat.ST_SIZE]
                        file_info['fileModificationTime'] = statResult[stat.ST_MTIME]
                        current_files[full_path] = file_info
                elif os.path.isdir(full_path):
                    current_files = self.get_files(full_path, ext, current_files)
        return current_files

    def notify(self, file_name):
        """
        This method performs action to notify stakeholders about a file.
        Currently the notification is done by using queue.
        This method validates the file first. If file validated successfully, the full file name is enqueued.
        The file might not validate if has been discovered before it is complete. In such situation, the file will
        be discovered again when updated.

        Parameters
        ----------
        file_name : str
            a full name of a file

        Returns
        -------
        none
        """

        if self.file_type == const.FILE_TYPE_GE:
            validator = FileValidatorGe()
            if validator.is_valid(file_name):
                self.q.put(file_name)
        else:
            # the velidator is not implemented, so for now pass all discovered files
            self.q.put(file_name)

    def process_files(self, previous_files, current_files):
        """
        This method compares new latest discovered files with previously found files. The new files are reported
        through notify to the stakeholders.

        Parameters
        ----------
        previous_files : dict
            a dictionary of previously found files

        current_files : dict
            a dictionary of currently found files

        Returns
        -------
        none
        """

        for file_name in current_files.keys():
            if not file_name in previous_files:
                # new file, must be updated
                self.notify(file_name)
            else:
                # old file, check timestamp
                prev_file_info = previous_files.get(file_name)
                prev_modification_time = prev_file_info.get('fileModificationTime', '')
                file_info = current_files.get(file_name)
                modification_time = file_info.get('fileModificationTime')
                if modification_time != prev_modification_time:
                    # file has been modified, need to process it
                    self.notify(file_name)


    def poll_file_system(self, folder, ext):
        """
        This method initiates for polling the file information off of the file system.

        Parameters
        ----------
        folder : str
            a folder name that will be checked for files

        ext : list
            list of file extensions that will be discovered

        discovered_files : dict
            a dictionary to add the discovered files to

        Returns
        -------
        none
        """

        try:
            current_files = self.get_files(folder, ext)
            self.process_files(self.processed_files, current_files)
            self.processed_files = current_files
        except:
            self.logger.error('Could not poll directory %s' % (folder))
        self.start_observing(folder, ext)

    def start_observing(self, folder, ext):
        """
        This method startss for polling the file information off of the file system.

        Parameters
        ----------
        folder : str
            a folder name that will be checked for files

        ext : list
            list of file extensions that will be discovered

        discovered_files : dict
            a dictionary to add the discovered files to

        Returns
        -------
        none
        """

        if self.processed_files is None:
            self.processed_files = self.get_files(folder, ext)
        if self.done:
            return

        t = Timer(self.polling_period, self.poll_file_system, [folder, ext])
        self.t = t
        t.start()

    def stop_observing(self):
        """
        This method stops the polling the file information off of the file system.

        Parameters
        ----------
        none

        Returns
        -------
        none
        """

        self.t.cancel()
        self.done = True


class FileValidatorGe():
    """
    This class is an interface to the concrete file verification functionality.
    """
    def is_valid(self, file):
        """
        This method checks if the ge file is compatible with the standards.

        Parameters
        ----------
        file : str
            file name

        Returns
        -------
        True if validated, False otherwise
        """

        import struct as st

        fp = open(file, 'rb')
        offset = 8192

        fp.seek(18)
        size, nframes = st.unpack('<ih',fp.read(6))
        if size != 2048:
            return False

        fsize = os.stat(str(fp).split("'")[1]).st_size
        nframes_calc = (fsize - offset)/(2*size**2)

        if nframes != nframes_calc:
            return False

        return True


