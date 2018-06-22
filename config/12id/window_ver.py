import sys
import os
from os.path import expanduser
from configobj import ConfigObj
import json
import epics
from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal, pyqtSlot
import zmq


default_det = "S12-PILATUS1"
default_cntl_port = 5511
default_cntl_host = 'localhost'
ui = "verui.ui"


class zmq_consumer():
    def __init__(self, host = default_cntl_host, port=default_cntl_port):
        context = zmq.Context()
        self.socket = context.socket(zmq.PAIR)
        self.socket.connect("tcp://" + host + ":%s" % port)


class Window(QtGui.QMainWindow):
    statusBarSignal = pyqtSignal(str, str)

    def __init__(self):
        super(Window, self).__init__()
        # set parameters from config file
        self.detector = default_det
        self.conf_map, self.quality_checks = self.get_ver_params()

        self.ui = uic.loadUi(ui)
        self.ui.show()

        self.show_limits()
        self.ui.det_name.setText(self.detector)

        self.ui.det_name.returnPressed.connect(lambda: self.set_detector())

        self.ui.frame_sum_ll.returnPressed.connect(lambda: self.set_limit(self.ui.frame_sum_ll, 'sum','low_limit'))
        self.ui.frame_sum_hl.returnPressed.connect(lambda: self.set_limit(self.ui.frame_sum_hl, 'sum','high_limit'))
        self.ui.point_sat_hl.returnPressed.connect(lambda: self.set_limit(self.ui.point_sat_hl, 'point_sat','high_limit'))
        self.ui.frame_sat_pts_hl.returnPressed.connect(lambda: self.set_limit(self.ui.frame_sat_pts_hl, 'frame_sat_pts','high_limit'))
        self.ui.point_sat_rate_hl.returnPressed.connect(lambda: self.set_limit(self.ui.point_sat_rate_hl, 'point_sat_rate','high_limit'))
        self.ui.frame_sat_pts_rate_hl.returnPressed.connect(lambda: self.set_limit(self.ui.frame_sat_pts_rate_hl, 'frame_sat_cnt_rate','high_limit'))

        self.setEpicsQualityFeedbackUpdate()

        self.verifier_on = 0
        self.ui.actionStart_verifier.triggered.connect(self.start_verifier)
        self.ui.actionStop_verifier.triggered.connect(self.stop_verifier)

        self.statusBarSignal.connect(self.onVerifierPVchange)
        self.zmq_menu = zmq_consumer()
        self.ui.statusBar.showMessage("verifier off")

        self.list_cnt = 0


    def start_verifier(self):
        socket = self.zmq_menu.socket
        socket.send_json(
            dict(
                key="start_ver",
                detector=self.detector
            )
        )
        self.verifier_on = 1
        self.set_status_color('yellow')
        msg = 'not acquireing'

        self.ui.statusBar.showMessage(msg)


    def stop_verifier(self):
        socket = self.zmq_menu.socket
        socket.send_json(
            dict(
                key="stop_ver"
            )
        )
        self.verifier_on = 0
        self.set_status_color('none')
        msg = 'off'

        self.ui.statusBar.showMessage(msg)


    def set_detector(self):
        restart = False
        if self.verifier_on == 1:
            self.stop_verifier()
            restart = True

        self.detector = str(self.ui.det_name.text())
        self.conf_map, self.quality_checks = self.get_ver_params()
        self.show_limits()

        if restart:
            self.start_verifier()


    def show_limits(self):
        try:
            self.limits_file = self.conf_map['limits']
        except KeyError:
            self.limits_file = None

        with open(self.limits_file) as limitsfile:
            self.limits = json.loads(limitsfile.read())['data']
            self.ui.frame_sum_ll.setText(str(self.limits['sum']['low_limit']))
            self.ui.frame_sum_hl.setText(str(self.limits['sum']['high_limit']))
            self.ui.point_sat_hl.setText(str(self.limits['point_sat']['high_limit']))
            self.ui.frame_sat_pts_hl.setText(str(self.limits['frame_sat_pts']['high_limit']))
            self.ui.point_sat_rate_hl.setText(str(self.limits['point_sat_rate']['high_limit']))
            self.ui.frame_sat_pts_rate_hl.setText(str(self.limits['frame_sat_cnt_rate']['high_limit']))
        limitsfile.close()


    def set_limit(self, le_limit, key1, key2):
        restart = False
        if self.verifier_on == 1:
            self.stop_verifier()
            restart = True

        limit_val = int(le_limit.text())
        self.limits[key1][key2] = limit_val
        data_limits = {}
        data_limits['data'] = self.limits
        with open(self.limits_file, 'w') as limitsfile:
            json.dump(data_limits, limitsfile)
        limitsfile.close()

        if restart:
            self.start_verifier()


    def setEpicsQualityFeedbackUpdate(self):
        try:
            self.acquire = epics.PV(self.detector + ':cam1:Acquire', callback=self.epicsCallbackFunc)
            self.status = epics.PV(self.detector + ':STAT', callback=self.epicsCallbackFunc)
        except:
            self.ui.statusBar.showMessage('verifier off')


    def epicsCallbackFunc(self, pvname, char_value, **kws):
        self.statusBarSignal.emit(pvname, char_value)


    @pyqtSlot(str, str)
    def onVerifierPVchange(self, pvname, char_value):
        if not pvname is None:
            if "STAT" in pvname:
                msg = epics.caget(self.detector+':STAT', as_string=True)
                if msg is None:
                    return
                failed = False
                if msg.endswith('status'):
                    pass
                elif msg.endswith('pass'):
                    self.set_status_color('green')
                else:
                    failed = True
                    self.set_status_color('red')
                self.ui.statusBar.showMessage(msg)
                if failed:
                    list_item = msg
                    if self.list_cnt <= 4:
                        self.ui.list_failed.insertItem(0, list_item)
                        self.list_cnt = self.list_cnt + 1
                    else:
                        self.ui.list_failed.takeItem(4)
                        self.ui.list_failed.insertItem(0, list_item)
            elif "Acquire" in pvname:
                if self.verifier_on is 1:
                    if int(float(char_value)) is 0:
                        self.set_status_color('yellow')
                        msg = 'not acquireing'
                        self.ui.statusBar.showMessage(msg)
        else:
            self.ui.statusBar.showMessage("ver pv name not defined")


    def set_status_color(self, color):
        if color is 'red':
            self.ui.statusBar.setStyleSheet(
                "QStatusBar{padding-left:8px;background:rgba(255,0,0,120);color:black;font-weight:bold;}")
        elif color is 'green':
            self.ui.statusBar.setStyleSheet(
                "QStatusBar{padding-left:8px;background:rgba(0,255,0,120);color:black;font-weight:bold;}")
        elif color is 'yellow':
            self.ui.statusBar.setStyleSheet(
                "QStatusBar{padding-left:8px;background:rgba(255,255,0,120);color:black;font-weight:bold;}")
        elif color is 'none':
            self.ui.statusBar.setStyleSheet(
                "QStatusBar{padding-left:8px;background:rgba(0,0,0,0);color:black;font-weight:bold;}")


    def get_ver_params(self):
        home = expanduser("~")
        conf = os.path.join(home, '.dquality', self.detector)
        if os.path.isdir(conf):
            config = os.path.join(conf, 'dqconfig.ini')
        if not os.path.isfile(config):
            return None
        conf_map = ConfigObj(config)
        try:
            qcfile = conf_map['quality_checks']
        except KeyError:
            qcfile = None
        with open(qcfile) as qc_file:
            quality_checks = json.loads(qc_file.read())
        qc_file.close()
        return conf_map, quality_checks


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    a = Window()
    socket = a.zmq_menu.socket
    #sys.exit(app.exec_())
    # stop verifier on exit
    res = app.exec_()
    socket.send_json(
        dict(
            key="stop_ver"
        )
    )
    socket.close()
    sys.exit(res)
