import shutil
import os

def clean():
    schemas = "schemas"
    if os.path.isdir(schemas):
        shutil.rmtree(schemas)

    config = "dqconfig.ini"
    if os.path.isfile(config):
        os.remove(config)

    logfile = "default.log"
    open(logfile, 'w').close()
