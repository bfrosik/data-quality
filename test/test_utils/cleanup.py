import shutil
import os
import os.path as path

def close():
    home = path.expanduser("~")
    schemas = path.join(home, 'dqschemas')
    schemas_bak = path.join(home, 'dqschemas_bak')
    if path.isdir(schemas):
        shutil.rmtree(schemas)
    if path.isdir(schemas_bak):
        shutil.move(schemas_bak, schemas)

    config = path.join(home, 'dqconfig.ini')
    config_bak = path.join(home, 'dqconfig_bak.ini')
    if path.isfile(config):
        os.remove(config)

    if path.isfile(config_bak):
        shutil.move(config_bak, config)
