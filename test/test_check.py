import shutil
import time
import os
import dquality.check as check
import test.test_utils.verify_results as res

config = "test/dqconfig_test.ini"
data_file = "test/data/test_data.h5"
logfile = "default.log"
schemas = "test/schemas"

def xtest_setup():
    # shutil.copyfile("test/epics.py", "epics.py")
    if not os.path.isdir(schemas):
        shutil.copytree("test/schemas_test", schemas)


def clean():
    open(logfile, 'w').close()


def xtest_check_hdf():
    try:
        check.hdf(config, data_file)
    except:
        pass

    time.sleep(1)
    clean()


def xtest_check_pv():
    try:
        check.pv(config)
    except:
        pass

    time.sleep(1)
    assert res.is_text_in_file(logfile, 'PV ID32ds:Energy.VAL has value out of range. The value is 4.0 but should be greater_than 10.0')
    assert res.is_text_in_file(logfile, 'PV S:SRcurrentAI has value out of range. The value is 4.0 but should be greater_than 50.0')
    clean()


def xtest_check_monitor():
    try:
        check.monitor(config, "something", 1)
    except:
        pass

    time.sleep(1)
    clean()


def xtest_check_accumulator():
    try:
        check.accumulator(config, "something", "data_white", 1, True)
    except:
        pass

    time.sleep(1)
    assert res.is_text_in_file(logfile, 'parameter error: directory something does not exist')
    clean()


def xtest_check_data():
    try:
        check.data(config, data_file)
    except:
        pass

    time.sleep(1)
    clean()


def xtest_check_hdf_dependency():
    try:
        check.hdf_dependency(config, data_file)
    except:
        pass

    time.sleep(1)
    clean()

