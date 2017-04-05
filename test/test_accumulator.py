import os
import shutil
import time
from multiprocessing import Process
import test.test_utils.verify_results as res
import test.test_utils.modify_settings as mod
import dquality.accumulator as acc


logfile = os.path.join(os.getcwd(),"default.log")
config_test = os.path.join(os.getcwd(),"test/dqconfig_test.ini")
schemas_test = os.path.join(os.getcwd(),"test/schemas_test")
data_file = os.path.join(os.getcwd(),"test/data/test_data.h5")
interrupt_file = os.path.join(os.getcwd(),"test/data/INTERRUPT.h5")
report_file = os.path.join(os.getcwd(),"test/data/test_data.report")
schemas = os.path.join(os.getcwd(),"test/schemas")
limits = os.path.join(schemas,"limits.json")
data_type = 'data_white'

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


def clean(file1=None, file2=None):
    open(logfile, 'w').close()
    if file1 is not None:
        os.remove(file1)
    if file2 is not None:
        os.remove(file2)


def copy_file(source, dest1, dest2):
    time.sleep(1)
    shutil.copyfile(source, dest1)
    shutil.copyfile(source, dest2)


def test_qualitychecks_report_for_file():
    config = init('ba')
    data_path = os.path.join(os.getcwd(),"test/data1")
    new_data1 = os.path.join(data_path,"test_data1.h5")
    new_data2 = os.path.join(data_path,"test_data2.h5")

    if not os.path.exists(data_path):
        os.makedirs(data_path)
    p = Process(target=copy_file, args=(data_file, new_data1, new_data2))
    p.start()

    bad_indexes = acc.verify(config, data_path, data_type, 2, 'True')
    bad_indexes_type = bad_indexes[data_type]
    bad_data1 = bad_indexes_type[new_data1]
    bad_data2 = bad_indexes_type[new_data2]
    assert 0 in bad_data1
    assert 0 in bad_data2
    assert 4 in bad_data1
    assert not res.is_text_in_file(logfile, 'no file extension specified. Monitoring for all files')
    clean(new_data1, new_data2)


def test_qualitychecks_one_report():
    config = init('bc')
    data_path = os.path.join(os.getcwd(),"test/data1")
    new_data1 = os.path.join(data_path,"test_data3.h5")
    new_data2 = os.path.join(data_path,"test_data4.h5")

    if not os.path.exists(data_path):
        os.makedirs(data_path)
    p = Process(target=copy_file, args=(data_file, new_data1, new_data2))
    p.start()

    bad_indexes = acc.verify(config, data_path, data_type, 2, False)
    bad_data = bad_indexes[data_type]
    assert 0 in bad_data
    assert 4 in bad_data
    assert 5 in bad_data
    assert 9 in bad_data
    assert not res.is_text_in_file(logfile, 'no file extension specified. Monitoring for all files')
    clean(new_data1, new_data2)


def test_no_extentions_interrupt():
    config = init('bd')
    data_path = os.path.join(os.getcwd(),"test/data1")
    new_data1 = os.path.join(data_path,"INTERRUPT")
    new_data2 = os.path.join(data_path,"INTERRUPT.h5")

    find = 'extensions'
    replace = 'extensionsx'
    mod.replace_text_in_file(config, find, replace)

    if not os.path.exists(data_path):
        os.makedirs(data_path)
    p = Process(target=copy_file, args=(data_file, new_data1, new_data2))
    p.start()

    bad_indexes = acc.verify(config, data_path, data_type, 2, True)
    assert len(bad_indexes) is 0
    assert res.is_text_in_file(logfile, 'no file extension specified. Monitoring for all files')
    clean()


def test_bad_directory():
    config = init('be')
    directory = "bad_dir"
    # the file.verify will exit with -1
    try:
        acc.verify(config, directory, data_type, 1)
    except:
        pass
    time.sleep(1)
    assert res.is_text_in_file(logfile, 'parameter error: directory bad_dir does not exist')
    clean()

def test_conf_error_no_limits():
    config = init('bf')
    find = 'limits'
    replace = 'limitsx'
    mod.replace_text_in_file(config, find, replace)
    # the file.verify will exit with -1
    try:
        acc.verify(config, None, data_type, 1)
    except:
        pass
    time.sleep(1)
    assert res.is_text_in_file(logfile, 'configuration error: limits is not configured')
    clean()


def test_no_limit():
    config = init('bg')
    find = 'limits.json'
    replace = 'limitsx.json'
    mod.replace_text_in_file(config, find, replace)
    # the file.verify will exit with -1
    try:
        acc.verify(config, None, data_type, 1, True)
    except:
        pass
    time.sleep(1)
    assert res.is_text_in_file(logfile, 'configuration error: file test/schemas/limitsx.json does not exist')
    clean()
