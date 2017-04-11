import os
import shutil
import time
from multiprocessing import Process
import test.test_utils.verify_results as res
import test.test_utils.modify_settings as mod
import dquality.monitor_polling as monitor


logfile = os.path.join(os.getcwd(),"default.log")
config_test = os.path.join(os.getcwd(),"test/dqconfig_test.ini")
schemas_test = os.path.join(os.getcwd(),"test/schemas_test")
data_file = os.path.join(os.getcwd(),"test/data/test_data.h5")
report_file = os.path.join(os.getcwd(),"test/data/test_data.report")
interrupt_file = os.path.join(os.getcwd(),"test/data/INTERRUPT.h5")
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

def copy_file(source, dest):
    time.sleep(1)
    shutil.copyfile(source, dest)


def test_qualitychecks():
    config = init('ab')
    data_path = os.path.join(os.getcwd(),"test/data1")
    new_data = os.path.join(data_path,"test_data.h5")

    if not os.path.exists(data_path):
        os.makedirs(data_path)
    p = Process(target=copy_file, args=(data_file, new_data,))
    p.start()

    bad_indexes_file = monitor.verify(config, data_path, 1)
    bad_indexes = bad_indexes_file[new_data]
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


def test_no_extentions_interrupt():
    config = init('bb')
    data_path = os.path.join(os.getcwd(),"test/data1")
    new_data = os.path.join(data_path,"INTERRUPT")

    find = 'extensions'
    replace = 'extensionsx'
    mod.replace_text_in_file(config, find, replace)

    if not os.path.exists(data_path):
        os.makedirs(data_path)
    p = Process(target=copy_file, args=(interrupt_file, new_data,))
    p.start()

    bad_indexes = monitor.verify(config, data_path, 2)
    assert len(bad_indexes) is 0
    assert res.is_text_in_file(logfile, 'no file extension specified. Monitoring for all files')
    clean()


def test_bad_directory():
    config = init('ac')
    directory = "bad_dir"
    # the file.verify will exit with -1
    try:
        monitor.verify(config, directory, 1)
    except:
        pass
    time.sleep(1)
    assert res.is_text_in_file(logfile, 'parameter error: directory bad_dir does not exist')
    clean()

def test_conf_error_no_limits():
    config = init('ad')
    find = 'limits'
    replace = 'limitsx'
    mod.replace_text_in_file(config, find, replace)
    # the file.verify will exit with -1
    try:
        monitor.verify(config, None, 1)
    except:
        pass
    time.sleep(1)
    assert res.is_text_in_file(logfile, 'configuration error: limits is not configured')
    clean()


def test_no_limit():
    config = init('ae')
    find = 'limits.json'
    replace = 'limitsx.json'
    mod.replace_text_in_file(config, find, replace)
    # the file.verify will exit with -1
    try:
        monitor.verify(config, None, 1)
    except:
        pass
    time.sleep(1)
    assert res.is_text_in_file(logfile, 'configuration error: file test/schemas/limitsx.json does not exist')
    clean()


def test_ge():
    config = init('af')
    data_path = os.path.join(os.getcwd(),"test/data1")
    data_file = os.path.join(os.getcwd(),"test/data/test_data.ge4")
    new_data = os.path.join(data_path,"test_data.ge4")

    find = 'HDF'
    replace = 'GE'
    mod.replace_text_in_file(config, find, replace)
    mod.delete_line_in_file(config, 'extensions')
    mod.add_line_to_file(config, "'extensions' = .ge, .ge4, .ge3")


    if not os.path.exists(data_path):
        os.makedirs(data_path)
    p = Process(target=copy_file, args=(data_file, new_data,))
    p.start()

    bad_indexes_file = monitor.verify(config, data_path, 1)
    bad_indexes = bad_indexes_file[new_data]
    bad_data = bad_indexes['data']
    assert 1 in bad_data
    assert 2 in bad_data
    assert 3 in bad_data
    assert 4 in bad_data
    clean()


def test_ge_corrupted_file():
    config = init('ag')
    data_path = os.path.join(os.getcwd(),"test/data1")
    data_file = os.path.join(os.getcwd(),"test/data/test_data.h5")
    new_data = os.path.join(data_path,"test_data.ge4")

    find = 'HDF'
    replace = 'GE'
    mod.replace_text_in_file(config, find, replace)
    mod.delete_line_in_file(config, 'extensions')
    mod.add_line_to_file(config, "'extensions' = .ge, .ge4, .ge3")


    if not os.path.exists(data_path):
        os.makedirs(data_path)
    p = Process(target=copy_file, args=(data_file, new_data,))

    data_file = os.path.join(os.getcwd(),"test/data/test_data.ge4")
    new_data = os.path.join(data_path,"test_data1.ge4")
    p1 = Process(target=copy_file, args=(data_file, new_data,))
    p.start()
    p1.start()

    bad_indexes_file = monitor.verify(config, data_path, 1)
    bad_indexes = bad_indexes_file[new_data]
    bad_data = bad_indexes['data']
    assert 1 in bad_data
    assert 2 in bad_data
    assert 3 in bad_data
    assert 4 in bad_data
    clean()
