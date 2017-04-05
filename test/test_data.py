import os
import time
import shutil
import test.test_utils.modify_settings as mod
import test.test_utils.verify_results as res
import dquality.check as check

import dquality.data as data

logfile = os.path.join(os.getcwd(),"default.log")
config_test = os.path.join(os.getcwd(),"test/dqconfig_test.ini")
schemas_test = os.path.join(os.getcwd(),"test/schemas_test")
data_file = os.path.join(os.getcwd(),"test/data/test_data.h5")
report_file = os.path.join(os.getcwd(),"test/data/test_data.report")
schemas = os.path.join(os.getcwd(),"test/schemas")
limits = os.path.join(schemas,"limits.json")

def print_log():
    f = open(logfile, 'r')
    print (f.read())

def init(id):
    config = 'test/conf' + id + '.ini'
    config =  os.path.join(os.getcwd(),config)
    shutil.copyfile(config_test, config)
    if not os.path.isdir(schemas):
        shutil.copytree(schemas_test, schemas)
    return config


def clean():
    open(logfile, 'w').close()


def test_qualitychecks():
    config = init('a')
    bad_indexes = data.verify(config, data_file)
    bad_data_white = bad_indexes['data_white']
    bad_data = bad_indexes['data']
    bad_data_dark = bad_indexes['data_dark']
    assert 5 in bad_data_white
    assert 9 in bad_data_white
    assert 10 in bad_data
    assert 13 in bad_data
    assert 14 in bad_data
    assert 0 in bad_data_dark
    assert 1 in bad_data_dark
    assert 2 in bad_data_dark
    assert 3 in bad_data_dark
    assert 4 in bad_data_dark
    clean()


def test_bad_file():
    data_file = "data/test_datax.h5"
    # the file.verify will exit with -1
    try:
        data.verify(config_test, data_file)
    except:
        pass
    time.sleep(1)
    assert res.is_text_in_file(logfile, 'parameter error: file data/test_datax.h5 does not exist')
    clean()

def test_conf_error_no_limits():
    config = init('b')
    find = 'limits'
    replace = 'limitsx'
    mod.replace_text_in_file(config, find, replace)
    # the file.verify will exit with -1
    try:
        data.verify(config, None)
    except:
        pass
    time.sleep(1)
    assert res.is_text_in_file(logfile, 'configuration error: limits is not configured')
    clean()


def test_no_limit():
    config = init('c')
    find = 'limits.json'
    replace = 'limitsx.json'
    mod.replace_text_in_file(config, find, replace)
    # the file.verify will exit with -1
    try:
        check.data(config, None)
    except:
        pass
    time.sleep(1)
    assert res.is_text_in_file(logfile, 'configuration error: file test/schemas/limitsx.json does not exist')
    clean()

def test_ge():
    config = init('d')
    find = 'HDF'
    replace = 'GE'
    mod.replace_text_in_file(config, find, replace)
    data_file = os.path.join(os.getcwd(),"test/data/test_data.ge4")
    bad_indexes = data.verify(config, data_file)
    bad_data = bad_indexes['data']
    assert 1 in bad_data
    assert 2 in bad_data
    assert 3 in bad_data
    assert 4 in bad_data
    clean()
