import threading
import os
import time
from test.test_utils.set_config import init
from test.test_utils.cleanup import clean
import test.test_utils.modify_settings as mod
import test.test_utils.verify_results as res

import dquality.file as file

def on_exit_test(test):
    init()
    tt = threading.Thread(target=test, args = () )
    tt.start()
    time.sleep(.5)

def test_conf_error_no_schema():
    conf_file = "dqconfig.ini"
    find = 'schema'
    replace = 'schemax'
    mod.replace_text_in_file(conf_file, find, replace)
    # the file.verify will exit with -1
    file.verify(conf_file, None)

def test_no_schema():
    conf_file = "dqconfig.ini"
    find = 'tags'
    replace = 'tagsx'
    mod.replace_text_in_file(conf_file, find, replace)
    # the file.verify will exit with -1
    file.verify(conf_file, None)

def test_conf_error_no_type():
    conf_file = "dqconfig.ini"
    find = 'verification_type'
    replace = 'verification_typex'
    mod.replace_text_in_file(conf_file, find, replace)
    # the file.verify will exit with -1
    file.verify(conf_file, None)

def test_bad_type():
    conf_file = "dqconfig.ini"
    find = 'hdf_structure'
    replace = 'hdf_structurex'
    mod.replace_text_in_file(conf_file, find, replace)
    # the file.verify will exit with -1
    file.verify(conf_file, None)

def test_bad_file():
    conf_file = "dqconfig.ini"
    data_file = "data/test_datax.h5"
    # the file.verify will exit with -1
    file.verify(conf_file, data_file)

def test_tags_missing_tags():
    schema_file = "schemas/tags.json"
    conf_file = "dqconfig.ini"
    find = 'hdf_structure'
    replace = 'hdf_tags'
    mod.replace_text_in_file(conf_file, find, replace)
    data_file = "data/test_data.h5"
    file.verify(conf_file, data_file)

def test_tags_no_missing_tags():
    schema_file = "schemas/tags.json"
    conf_file = "dqconfig.ini"
    find = 'hdf_structure'
    replace = 'hdf_tags'
    mod.replace_text_in_file(conf_file, find, replace)
    match = 'missing'
    mod.delete_line_in_file(schema_file, match)
    data_file = "data/test_data.h5"
    file.verify(conf_file, data_file)

def test_struct_missing_tags_attrib():
    schema_file = "schemas/tags.json"
    conf_file = "dqconfig.ini"
    data_file = "data/test_data.h5"
    file.verify(conf_file, data_file)

def test_struct_no_missing():
    schema_file = "schemas/tags.json"
    conf_file = "dqconfig.ini"
    match = 'missing'
    mod.delete_line_in_file(schema_file, match)
    match = 'axes'
    mod.delete_line_in_file(schema_file, match)
    match = 'degrees'
    mod.delete_line_in_file(schema_file, match)
    data_file = "data/test_data.h5"
    file.verify(conf_file, data_file)

def ver_conf_error_no_schema():
    logfile = os.path.join(os.getcwd(),"default.log")
    return res.is_text_in_file(logfile, 'configuration error: schema is not configured')

def ver_no_schema():
    logfile = os.path.join(os.getcwd(),"default.log")
    return res.is_text_in_file(logfile, 'configuration error: file schemas/tagsx.json does not exist')

def ver_conf_error_no_type():
    logfile = os.path.join(os.getcwd(),"default.log")
    return res.is_text_in_file(logfile, 'config error: verification type not configured')

def ver_bad_type():
    logfile = os.path.join(os.getcwd(),"default.log")
    return res.is_text_in_file(logfile, 'configured verification type hdf_structurex is not supported')

def ver_bad_file():
    logfile = os.path.join(os.getcwd(),"default.log")
    return res.is_text_in_file(logfile, 'parameter error: file data/test_datax.h5 does not exist')

def ver_tags_missing_tags():
    logfile = os.path.join(os.getcwd(),"default.log")
    if res.is_text_in_file(logfile, '/exchange/missing'):
        return res.is_text_in_file(logfile, '/exchange/missing1')
    else:
        return False

def ver_tags_no_missing_tags():
    logfile = os.path.join(os.getcwd(),"default.log")
    return not res.is_text_in_file(logfile, 'not found')

def ver_struct_missing_tags_attrib():
    logfile = os.path.join(os.getcwd(),"default.log")
    if not res.is_text_in_file(logfile, '/exchange/missing'):
        return False
    if not res.is_text_in_file(logfile, '/exchange/missing1'):
        return False
    if not res.is_text_in_file(logfile, 'should be axes:theta_dark:y:x'):
        return False
    if not res.is_text_in_file(logfile, 'should be axes:theta_white:y:x'):
        return False
    if not res.is_text_in_file(logfile, 'attributes are missing in tag /exchange/theta'):
        return False

    return True

def ver_struct_no_missing_tags():
    logfile = os.path.join(os.getcwd(),"default.log")
    return os.stat(logfile).st_size == 0


on_exit_test(test_conf_error_no_schema)
print ver_conf_error_no_schema()
clean()

on_exit_test(test_no_schema)
print ver_no_schema()
clean()

on_exit_test(test_conf_error_no_type)
print ver_conf_error_no_type()
clean()

on_exit_test(test_bad_type)
print ver_bad_type()
clean()

on_exit_test(test_bad_file)
print ver_bad_file()
clean()

init()
test_tags_missing_tags()
print ver_tags_missing_tags()
clean()

init()
test_tags_no_missing_tags()
print ver_tags_no_missing_tags()
clean()

init()
test_struct_missing_tags_attrib()
print ver_struct_missing_tags_attrib()
clean()

init()
test_struct_no_missing()
print ver_struct_no_missing_tags()
clean()
