import shutil
import os.path as path

def init():
    home = path.expanduser("~")
    config = path.join(home, 'dqconfig.ini')
    config_bak = path.join(home, 'dqconfig_bak.ini')
    if path.isfile(config):
        shutil.move(config, config_bak)

    test_config = 'dqconfig.ini'
    shutil.copyfile(test_config, config)

    schemas = path.join(home, 'dqschemas')
    schemas_bak = path.join(home, 'dqschemas_bak')
    if path.isdir(schemas):
        shutil.move(schemas, schemas_bak)

    test_schemas = 'schemas'
    shutil.copytree(test_schemas, schemas)

def get_file(filename):
    home = path.expanduser("~")
    return path.join(home, filename)

