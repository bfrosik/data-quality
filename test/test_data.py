import os
import time
import shutil
import test.test_utils.modify_settings as mod
import test.test_utils.verify_results as res

import dquality.data as data

logfile = os.path.join(os.getcwd(),"default.log")
config_test = os.path.join(os.getcwd(),"test/dqconfig_test.ini")
schemas_test = os.path.join(os.getcwd(),"test/schemas_test")
limits_test = os.path.join(schemas_test,"limits.json")
data_file = os.path.join(os.getcwd(),"test/data/test_data.h5")
report_file = os.path.join(os.getcwd(),"test/data/test_data.report")
schemas = os.path.join(os.getcwd(),"test/schemas")

def print_log():
    f = open(logfile, 'r')
    print (f.read())

def init(id):
    config = 'test/conf' + id + '.ini'
    config =  os.path.join(os.getcwd(),config)
    shutil.copyfile(config_test, config)
    find = 'limits'
    replace = 'limits'+ id
    mod.replace_text_in_file(config, find, replace)
    if not os.path.isdir(schemas):
        shutil.copytree(schemas_test, schemas)
    limits = 'test/schemas/limits' + id + '.json'
    limits = os.path.join(os.getcwd(), limits)
    shutil.copyfile(limits_test, limits)
    return config, limits


def clean():
    open(logfile, 'w').close()


def test_qualitychecks():
    config, limits = init('a')
    bad_indexes = data.verify(config, data_file)
    bad_data_white = bad_indexes['data_white']
    bad_data = bad_indexes['data']
    bad_data_dark = bad_indexes['data_dark']
    assert 0 in bad_data_white
    assert 1 in bad_data_white
    assert 3 in bad_data_white
    assert 4 in bad_data_white
    assert 0 in bad_data
    assert 3 in bad_data
    assert 4 in bad_data
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
    print_log()
    assert res.is_text_in_file(logfile, 'parameter error: file data/test_datax.h5 does not exist')
    clean()

def test_conf_error_no_limits():
    config, limits = init('b')
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
    config, limits = init('c')
    find = 'limits'
    replace = 'limitsx'
    mod.replace_text_in_file(config, find, replace)
    # the file.verify will exit with -1
    try:
        data.verify(config, None)
    except:
        pass
    time.sleep(1)
    assert res.is_text_in_file(logfile, 'configuration error: file test/schemas/limitsxc.json does not exist')
    clean()

test_qualitychecks()
test_bad_file()
test_conf_error_no_limits()
test_no_limit()