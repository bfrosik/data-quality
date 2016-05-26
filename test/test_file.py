import os
import test.test_utils.modify_settings as mod
import test.test_utils.verify_results as res

import dquality.file as file
import shutil

logfile = os.path.join(os.getcwd(),"default.log")
config_test = os.path.join(os.getcwd(),"test/dqconfig_test.ini")
schemas_test = os.path.join(os.getcwd(),"test/schemas_test")
tags_test = os.path.join(schemas_test,"tags.json")
data_file = os.path.join(os.getcwd(),"test/data/test_data.h5")
id = 0


def print_log():
    f = open(logfile, 'r')
    print (f.read())

def init():
    id += 1
    config = 'test/conf' + id
    config =  os.path.join(os.getcwd(),config)
    shutil.copyfile(config_test, config)
    tags = 'test/tags' + id
    tags = os.path.join(os.getcwd(), tags)
    shutil.copyfile(tags_test, tags)
    return config, tags


def clean():
    open(logfile, 'w').close()


def test_conf_error_no_schema():
    config, tags = init()
    find = 'schema'
    replace = 'schemax'
    mod.replace_text_in_file(config, find, replace)
    # the file.verify will exit with -1
    try:
        file.verify(config, None)
    except:
        pass
    assert res.is_text_in_file(logfile, 'configuration error: schema is not configured')

    clean()


def test_no_schema():
    config, tags = init()
    find = 'tags'
    replace = 'tagsx'
    mod.replace_text_in_file(config, find, replace)
    # the file.verify will exit with -1
    try:
        file.verify(config, None)
    except:
        pass

    assert res.is_text_in_file(logfile, 'configuration error: file test/schemas/tagsx.json does not exist')
    clean()


def test_conf_error_no_type():
    config, tags = init()
    find = 'verification_type'
    replace = 'verification_typex'
    mod.replace_text_in_file(config, find, replace)
    # the file.verify will exit with -1
    try:
        file.verify(config, None)
    except:
        pass

    assert res.is_text_in_file(logfile, 'config error: verification type not configured')
    clean()


def test_bad_type():
    config, tags = init()
    find = 'hdf_structure'
    replace = 'hdf_structurex'
    mod.replace_text_in_file(config, find, replace)
    # the file.verify will exit with -1
    try:
        file.verify(config, None)
    except:
        pass
    assert res.is_text_in_file(logfile, 'configured verification type hdf_structurex is not supported')
    clean()


def test_bad_file():
    config, tags = init()
    data_file = "data/test_datax.h5"
    # the file.verify will exit with -1
    try:
        file.verify(config, data_file)
    except:
        pass
    assert res.is_text_in_file(logfile, 'parameter error: file data/test_datax.h5 does not exist')
    clean()

def test_tags_missing_tags():
    config, tags = init()
    find = 'hdf_structure'
    replace = 'hdf_tags'
    mod.replace_text_in_file(config, find, replace)
    file.verify(config, data_file)
    assert res.is_text_in_file(logfile, '/exchange/missing')
    assert res.is_text_in_file(logfile, '/exchange/missing1')
    clean()


def test_tags_no_missing_tags():
    config, tags = init()
    find = 'hdf_structure'
    replace = 'hdf_tags'
    mod.replace_text_in_file(config, find, replace)
    match = 'missing'
    mod.delete_line_in_file(tags, match)
    file.verify(config, data_file)
    assert not res.is_text_in_file(logfile, 'not found')
    clean()


def test_struct_missing_tags_attrib():
    config, tags = init()
    file.verify(config, data_file)
    assert res.is_text_in_file(logfile, '/exchange/missing')
    assert res.is_text_in_file(logfile, '/exchange/missing1')
    assert res.is_text_in_file(logfile, 'should be axes:theta_dark:y:x')
    assert res.is_text_in_file(logfile, 'should be axes:theta_white:y:x')
    assert res.is_text_in_file(logfile, 'attributes are missing in tag /exchange/theta')
    clean()


def test_struct_no_missing():
    config, tags = init()
    match = 'missing'
    mod.delete_line_in_file(tags, match)
    match = 'axes'
    mod.delete_line_in_file(tags, match)
    match = 'degrees'
    mod.delete_line_in_file(tags, match)
    file.verify(config, data_file)
    assert os.stat(logfile).st_size == 0
    clean

