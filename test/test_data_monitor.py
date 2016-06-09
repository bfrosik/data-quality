import os
import shutil
import time
from multiprocessing import Process
import test.test_utils.verify_results as res
import test.test_utils.modify_settings as mod
import dquality.data_monitor as monitor


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

def copy_file(source, dest):
    time.sleep(1)
    shutil.copyfile(source, dest)


# def test_qualitychecks():
#     config = init('a')
#     data_path = os.path.join(os.getcwd(),"test/data1")
#     new_data = os.path.join(data_path,"test_data.h5")

#     if not os.path.exists(data_path):
#         os.makedirs(data_path)
#     p = Process(target=copy_file, args=(data_file, new_data,))
#     p.start()

#     bad_indexes_file = monitor.verify(config, data_path, 1)
#     bad_indexes = bad_indexes_file[new_data]
#     bad_data_white = bad_indexes['data_white']
#     bad_data = bad_indexes['data']
#     bad_data_dark = bad_indexes['data_dark']
#     assert 0 in bad_data_white
#     assert 1 in bad_data_white
#     assert 3 in bad_data_white
#     assert 4 in bad_data_white
#     assert 0 in bad_data
#     assert 3 in bad_data
#     assert 4 in bad_data
#     assert 0 in bad_data_dark
#     assert 1 in bad_data_dark
#     assert 2 in bad_data_dark
#     #assert 3 in bad_data_dark
#     assert 4 in bad_data_dark
#     clean()


# def test_bad_directory():
#     config = init('b')
#     directory = "bad_dir"
#     # the file.verify will exit with -1
#     try:
#         monitor.verify(config, directory, 1)
#     except:
#         pass
#     time.sleep(1)
#     assert res.is_text_in_file(logfile, 'parameter error: directory bad_dir does not exist')
#     clean()

# def test_conf_error_no_limits():
#     config = init('c')
#     find = 'limits'
#     replace = 'limitsx'
#     mod.replace_text_in_file(config, find, replace)
#     # the file.verify will exit with -1
#     try:
#         monitor.verify(config, None, 1)
#     except:
#         pass
#     time.sleep(1)
#     assert res.is_text_in_file(logfile, 'configuration error: limits is not configured')
#     clean()


# def test_no_limit():
#     config = init('c')
#     find = 'limits.json'
#     replace = 'limitsx.json'
#     mod.replace_text_in_file(config, find, replace)
#     # the file.verify will exit with -1
#     try:
#         monitor.verify(config, None, 1)
#     except:
#         pass
#     time.sleep(1)
#     assert res.is_text_in_file(logfile, 'configuration error: file test/schemas/limitsx.json does not exist')
#     clean()
