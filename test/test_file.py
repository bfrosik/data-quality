import threading
import os
import time
#from test.test_utils.set_config import init
from test.test_utils.cleanup import clean
import test.test_utils.modify_settings as mod
import test.test_utils.verify_results as res
from nose import with_setup

import dquality.file as file
import shutil

logfile = os.path.join(os.getcwd(),"test/default.log")
config_file = os.path.join(os.getcwd(),"test/dqconfig.ini")

def init():
    config = os.path.join(os.getcwd(),"test/dqconfig.ini")
    print (config)
    config_test = os.path.join(os.getcwd(),"test/dqconfig_test.ini")
    shutil.copyfile(config_test, config)

    schemas = os.path.join(os.getcwd(),"test/schemas")
    schemas_test = os.path.join(os.getcwd(),"test/schemas_test")
    shutil.copytree(schemas_test, schemas)

def on_exit_test(test):
    tt = threading.Thread(target=test, args = () )
    tt.start()
    time.sleep(1)

@with_setup(init, clean)
def test_conf_error_no_schema():
    conf_file = "dqconfig.ini"
    find = 'schema'
    replace = 'schemax'
    mod.replace_text_in_file(conf_file, find, replace)
    # the file.verify will exit with -1
    try:
        file.verify(conf_file, None)
    except:
        pass
    on_exit_test(test_no_schema)
    assert res.is_text_in_file(logfile, 'configuration error: schema is not configured')
    clean()


@with_setup(init, clean)
def test_no_schema():
    conf_file = "dqconfig.ini"
    find = 'tags'
    replace = 'tagsx'
    mod.replace_text_in_file(conf_file, find, replace)
    # the file.verify will exit with -1
    try:
        file.verify(conf_file, None)
    except:
        pass
    assert res.is_text_in_file(logfile, 'configuration error: file schemas/tagsx.json does not exist')
    clean()

@with_setup(init, clean)
def test_conf_error_no_type():
    conf_file = "dqconfig.ini"
    find = 'verification_type'
    replace = 'verification_typex'
    mod.replace_text_in_file(conf_file, find, replace)
    # the file.verify will exit with -1
    try:
        file.verify(conf_file, None)
    except:
        pass
    assert res.is_text_in_file(logfile, 'config error: verification type not configured')
    clean()

@with_setup(init, clean)
def test_bad_type():
    conf_file = "dqconfig.ini"
    find = 'hdf_structure'
    replace = 'hdf_structurex'
    mod.replace_text_in_file(conf_file, find, replace)
    # the file.verify will exit with -1
    try:
        file.verify(conf_file, None)
    except:
        pass
    assert res.is_text_in_file(logfile, 'configured verification type hdf_structurex is not supported')
    clean()

@with_setup(init, clean)
def test_bad_file():
    conf_file = "dqconfig.ini"
    data_file = "data/test_datax.h5"
    # the file.verify will exit with -1
    try:
        file.verify(conf_file, data_file)
    except:
        pass
    assert res.is_text_in_file(logfile, 'parameter error: file data/test_datax.h5 does not exist')
    clean()

@with_setup(init, clean)
def test_tags_missing_tags():
    schema_file = "schemas/tags.json"
    conf_file = "dqconfig.ini"
    find = 'hdf_structure'
    replace = 'hdf_tags'
    mod.replace_text_in_file(conf_file, find, replace)
    data_file = "data/test_data.h5"
    file.verify(conf_file, data_file)
    assert res.is_text_in_file(logfile, '/exchange/missing')
    assert res.is_text_in_file(logfile, '/exchange/missing1')
    clean()

@with_setup(init, clean)
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
    assert not res.is_text_in_file(logfile, 'not found')
    clean()

@with_setup(init, clean)
def test_struct_missing_tags_attrib():
    schema_file = "schemas/tags.json"
    conf_file = "dqconfig.ini"
    data_file = "data/test_data.h5"
    file.verify(conf_file, data_file)
    assert res.is_text_in_file(logfile, '/exchange/missing')
    assert res.is_text_in_file(logfile, '/exchange/missing1')
    assert res.is_text_in_file(logfile, 'should be axes:theta_dark:y:x')
    assert res.is_text_in_file(logfile, 'should be axes:theta_white:y:x')
    assert res.is_text_in_file(logfile, 'attributes are missing in tag /exchange/theta')
    clean()

@with_setup(init, clean)
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
    assert os.stat(logfile).st_size == 0
    clean()

# def run_tests():
#     test_conf_error_no_schema()
#     test_no_schema()
#     test_conf_error_no_type()
#     test_bad_type()
#     test_bad_file()
#     test_tags_missing_tags()
#     test_tags_no_missing_tags()
#     test_struct_missing_tags_attrib()
#     test_struct_no_missing()

#run_tests()
