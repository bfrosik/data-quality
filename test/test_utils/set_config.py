import shutil

def init():
    print 'in init'
    config = "dqconfig.ini"
    config_test = "dqconfig_test.ini"
    shutil.copyfile(config_test, config)

    schemas = "schemas"
    schemas_test = "schemas_test"
    shutil.copytree(schemas_test, schemas)

