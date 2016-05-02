import threading
import os
import test.test_utils.set_config as set
import test.test_utils.cleanup as clean
import test.test_utils.modify_settings as mod
import test.test_utils.verify_results as res

import dquality.monitor as monitor

clean.close()
set.init()

def test_conf_error_no_dir():
    file = set.get_file("dqconfig.ini")
    find = 'directory'
    replace = 'directoryx'
    mod.replace_text_in_file(file, find, replace)
    # thie monitor will exit with -1
    monitor.verify('data_white', 1)

def ver_conf_error_no_dir():
    logfile = os.getcwd() +'/logs/data_quality.log'
    file = set.get_file(logfile)
    print res.is_text_in_file(file, 'config error: directory to monitor not configured')

tt = threading.Thread(target=test_conf_error_no_dir, args = () )
tt.start()

tv = threading.Thread(target=ver_conf_error_no_dir, args = () )
tv.start()
