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

logfile = os.path.join(os.getcwd(),"default.log")
config = os.path.join(os.getcwd(),"test/dqconfig.ini")
config_test = os.path.join(os.getcwd(),"test/dqconfig_test.ini")
schemas = os.path.join(os.getcwd(),"test/schemas")
schemas_test = os.path.join(os.getcwd(),"test/schemas_test")
tags = os.path.join(schemas,"tags.json")
tags_test = os.path.join(schemas_test,"tags.json")

def print_log():
    f = open(logfile, 'r')
    print (f.read())
    
def init():
    shutil.copyfile(config_test, config)
    if not os.path.isdir(schemas):
        shutil.copytree(schemas_test, schemas)
    else:
        shutil.copyfile(tags_test, tags)


def clean():
    os.remove(tags)
    os.remove(config)
    open(logfile, 'w').close()


def test_conf_error_no_schema():
    shutil.copyfile(config_test, config)
    shutil.copytree(schemas_test, schemas)

    find = 'schema'
    replace = 'schemax'
    mod.replace_text_in_file(config, find, replace)
    # the file.verify will exit with -1
    try:
        file.verify(config, None)
    except:
        pass
    assert res.is_text_in_file(logfile, 'configuration error: schema is not configured')

    os.remove(tags)

    if os.path.isfile(config):
        os.remove(config)

    open(logfile, 'w').close()


#@with_setup(init, clean)
def test_no_schema():
    init()
    find = 'tags'
    replace = 'tagsx'
    mod.replace_text_in_file(config, find, replace)
    # the file.verify will exit with -1
    try:
        file.verify(config, None)
    except:
        pass
    assert res.is_text_in_file(logfile, 'configuration error: file schemas/tagsx.json does not exist')
    clean()

@with_setup(init, clean)
def test_conf_error_no_type():
    find = 'verification_type'
    replace = 'verification_typex'
    mod.replace_text_in_file(config, find, replace)
    # the file.verify will exit with -1
    try:
        file.verify(config, None)
    except:
        pass
    print_log()
    assert res.is_text_in_file(logfile, 'config error: verification type not configured')

    
@with_setup(init, clean)
def test_bad_type():
    find = 'hdf_structure'
    replace = 'hdf_structurex'
    mod.replace_text_in_file(config, find, replace)
    # the file.verify will exit with -1
    try:
        file.verify(config, None)
    except:
        pass
    assert res.is_text_in_file(logfile, 'configured verification type hdf_structurex is not supported')
    print_log()


@with_setup(init, clean)
def test_bad_file():
    data_file = "data/test_datax.h5"
    # the file.verify will exit with -1
    try:
        file.verify(config, data_file)
    except:
        pass
    assert res.is_text_in_file(logfile, 'parameter error: file data/test_datax.h5 does not exist')
    print_log()


@with_setup(init, clean)
def test_tags_missing_tags():
    schema_file = os.path.join(os.getcwd(),"test/schemas/tags.json")
    find = 'hdf_structure'
    replace = 'hdf_tags'
    mod.replace_text_in_file(config, find, replace)
    data_file = os.path.join(os.getcwd(),"test/data/test_data.h5")
    file.verify(config, data_file)
    assert res.is_text_in_file(logfile, '/exchange/missing')
    assert res.is_text_in_file(logfile, '/exchange/missing1')
    print_log()


@with_setup(init, clean)
def test_tags_no_missing_tags():
    schema_file = os.path.join(os.getcwd(),"test/schemas/tags.json")
    find = 'hdf_structure'
    replace = 'hdf_tags'
    mod.replace_text_in_file(config, find, replace)
    match = 'missing'
    mod.delete_line_in_file(schema_file, match)
    data_file = os.path.join(os.getcwd(),"test/data/test_data.h5")
    file.verify(config, data_file)
    assert not res.is_text_in_file(logfile, 'not found')
    print_log()


@with_setup(init, clean)
def test_struct_missing_tags_attrib():
    schema_file = os.path.join(os.getcwd(),"test/schemas/tags.json")
    data_file = os.path.join(os.getcwd(),"test/data/test_data.h5")
    file.verify(config, data_file)
    assert res.is_text_in_file(logfile, '/exchange/missing')
    assert res.is_text_in_file(logfile, '/exchange/missing1')
    assert res.is_text_in_file(logfile, 'should be axes:theta_dark:y:x')
    assert res.is_text_in_file(logfile, 'should be axes:theta_white:y:x')
    assert res.is_text_in_file(logfile, 'attributes are missing in tag /exchange/theta')
    print_log()


@with_setup(init, clean)
def test_struct_no_missing():
    schema_file = os.path.join(os.getcwd(),"test/schemas/tags.json")
    match = 'missing'
    mod.delete_line_in_file(schema_file, match)
    match = 'axes'
    mod.delete_line_in_file(schema_file, match)
    match = 'degrees'
    mod.delete_line_in_file(schema_file, match)
    data_file = os.path.join(os.getcwd(),"test/data/test_data.h5")
    file.verify(config, data_file)
    assert os.stat(logfile).st_size == 0
    print_log()


test_no_schema()
