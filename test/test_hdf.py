import os
import time
import shutil
import test.test_utils.modify_settings as mod
import test.test_utils.verify_results as res

import dquality.hdf as hdf

logfile = os.path.join(os.getcwd(),"default.log")
config_test = os.path.join(os.getcwd(),"test/dqconfig_test.ini")
schemas_test = os.path.join(os.getcwd(),"test/schemas_test")
tags_test = os.path.join(schemas_test,"tags.json")
data_file = os.path.join(os.getcwd(),"test/data/test_data.h5")
schemas = os.path.join(os.getcwd(),"test/schemas")

def print_log():
    f = open(logfile, 'r')
    print (f.read())

def init(id):
    config = 'test/conf' + id + '.ini'
    config =  os.path.join(os.getcwd(),config)
    shutil.copyfile(config_test, config)
    find = 'tags'
    replace = 'tags'+ id
    mod.replace_text_in_file(config, find, replace)
    if not os.path.isdir(schemas):
        shutil.copytree(schemas_test, schemas)
    tags = 'test/schemas/tags' + id + '.json'
    tags = os.path.join(os.getcwd(), tags)
    shutil.copyfile(tags_test, tags)
    return config, tags


def clean():
    open(logfile, 'w').close()


def test_conf_error_no_schema():
    config, tags = init('a')
    find = 'schema'
    replace = 'schemax'
    mod.replace_text_in_file(config, find, replace)
    # the file.verify will exit with -1
    try:
        hdf.verify(config, None)
    except:
        pass
    time.sleep(1)
    assert res.is_text_in_file(logfile, 'configuration error: schema is not configured')
    clean()


def test_no_schema():
    config, tags = init('b')
    find = 'tags'
    replace = 'tagsx'
    mod.replace_text_in_file(config, find, replace)
    # the file.verify will exit with -1
    try:
        hdf.verify(config, None)
    except:
        pass
    time.sleep(1)
    assert res.is_text_in_file(logfile, 'configuration error: file test/schemas/tagsxb.json does not exist')
    clean()


def test_conf_error_no_type():
    config, tags = init('c')
    find = 'verification_type'
    replace = 'verification_typex'
    mod.replace_text_in_file(config, find, replace)
    # the file.verify will exit with -1
    try:
        hdf.verify(config, None)
    except:
        pass
    time.sleep(1)
    assert res.is_text_in_file(logfile, 'config error: verification type not configured')
    clean()


def test_bad_type():
    config, tags = init('d')
    find = 'hdf_structure'
    replace = 'hdf_structurex'
    mod.replace_text_in_file(config, find, replace)
    # the file.verify will exit with -1
    try:
        hdf.verify(config, None)
    except:
        pass
    time.sleep(1)
    assert res.is_text_in_file(logfile, 'configured verification type hdf_structurex is not supported')
    clean()


def test_bad_file():
    config, tags = init('e')
    data_file = "data/test_datax.h5"
    # the file.verify will exit with -1
    try:
        hdf.verify(config, data_file)
    except:
        pass
    time.sleep(1)
    assert res.is_text_in_file(logfile, 'parameter error: file data/test_datax.h5 does not exist')
    clean()

def test_tags_missing_tags():
    config, tags = init('f')
    find = 'hdf_structure'
    replace = 'hdf_tags'
    mod.replace_text_in_file(config, find, replace)
    hdf.verify(config, data_file)
    time.sleep(1)
    assert res.is_text_in_file(logfile, '/exchange/missing')
    assert res.is_text_in_file(logfile, '/exchange/missing1')
    clean()


def test_tags_no_missing_tags():
    config, tags = init('g')
    find = 'hdf_structure'
    replace = 'hdf_tags'
    mod.replace_text_in_file(config, find, replace)
    match = 'missing'
    mod.delete_line_in_file(tags, match)
    time.sleep(1)
    assert (hdf.verify(config, data_file))
    assert res.is_text_in_file(logfile, 'All required tags exist')
    clean()


def test_struct_missing_tags_attrib():
    config, tags = init('h')
    hdf.verify(config, data_file)
    time.sleep(1)
    assert res.is_text_in_file(logfile, '/exchange/missing')
    assert res.is_text_in_file(logfile, '/exchange/missing1')
    assert res.is_text_in_file(logfile, 'should be axes:theta_dark:y:x')
    assert res.is_text_in_file(logfile, 'should be axes:theta_white:y:x')
    assert res.is_text_in_file(logfile, 'attributes are missing in tag /exchange/theta')
    clean()


def test_struct_no_missing():
    config, tags = init('i')
    match = 'missing'
    mod.delete_line_in_file(tags, match)
    match = 'axes'
    mod.delete_line_in_file(tags, match)
    match = 'degrees'
    mod.delete_line_in_file(tags, match)
    assert (hdf.verify(config, data_file))
    time.sleep(1)
    assert res.is_text_in_file(logfile, 'All required tags exist and meet conditions')
    clean

