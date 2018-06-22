#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) 2016, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2016. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# #########################################################################

"""
Please make sure the installation :ref:`pre-requisite-reference-label` are met.

This module feeds data coming from ZeroMQ server to a process using queue. The parsing of the message is customized
for the BlueSky use case. Other cases may be added later.
The data, which represents a frame captured by detector, is received in two parts. The first part is received as json
stream and contains data attributes, such shape, type, theta and counter associated with this frame.
The second part is frame in bytes.
The frame array along with the received attributes is packed into Python object and sent to process defined in adapter
over queue.

This module requires configuration file with the following parameters:
'zmq_rcv_port' - the ZeroMQ port
"""

from multiprocessing import Queue, Process
import numpy as np
import zmq
import time
import sys
import json
import dquality.common.utilities as utils
import dquality.common.constants as const
import dquality.clients.feedback as fb
import dquality.common.containers as containers
import dquality.handler as handler


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['zmq_rec.zmq_rec',
           'zmq_rec.destroy',
           'init',
           'receive_zmq_send']


class zmq_rec():
    """
    This class represents ZeroMQ connection.
    """
    def __init__(self, host=None, port=None):
        """
        Constructor

        This constructor creates zmq Context and socket for the zmq.PAIR.
        It initiate connect to the server given by host and port.

        Parameters
        ----------
        host : str
            server host name

        port : str
            serving port

        """
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.connect("tcp://" + host +":%s" % port)


    def destroy(self):
        """
        Destroys Context. This also closes socket associated with the context.
        """
        self.context.destroy()


def init(config):
    """
    This function initializes variables according to configuration.

    It gets values from the configuration file, evaluates and processes the values. If mandatory parameter is missing,
    the script logs an error and exits.

    Parameters
    ----------
    config : str
        configuration file name, including path

    Returns
    -------
    logger : Logger
        logger instance

    limits : dictionary
        a dictionary containing limit values read from the configured 'limit' file

    quality_checks : dict
        a dictionary containing quality check functions ids

    feedback : list
        a list of strings defining real time feedback of quality checks errors. Currently supporting 'PV', 'log', and
        'console'

    report_type : int
        report type; currently supporting 'none', 'error', and 'full'

    consumers : dict
        a dictionary parsed from json file representing consumers

    zmq_host : str
        ZeroMQ server host name

    zmq_rcv_port : str
        ZeroMQ port

    detector : str
        detector name, only needed if feedback contains pv

    """

    conf = utils.get_config(config)
    if conf is None:
        print ('configuration file is missing')
        exit(-1)

    logger = utils.get_logger(__name__, conf)

    limitsfile = utils.get_file(conf, 'limits', logger)
    if limitsfile is None:
        sys.exit(-1)

    with open(limitsfile) as limits_file:
        limits = json.loads(limits_file.read())

    qcfile = utils.get_file(conf, 'quality_checks', logger)
    if qcfile is None:
        sys.exit(-1)

    with open(qcfile) as qc_file:
        dict = json.loads(qc_file.read())
    #quality_checks = utils.get_quality_checks(dict)
    quality_checks = dict

    try:
        feedback = conf['feedback_type']
    except KeyError:
        feedback = None

    try:
        report_type = conf['report_type']
    except KeyError:
        report_type = const.REPORT_FULL

    try:
        zmq_host = conf['zmq_host']
    except:
        zmq_host = 'localhost'

    try:
        zmq_rcv_port = conf['zmq_rcv_port']
    except:
        zmq_rcv_port = None
        print ('configuration error: zmq_rcv_port not configured')

    try:
        detector = conf['detector']
    except KeyError:
        print ('configuration error: detector parameter not configured.')
        return None

    try:
        consumers = conf['zmq_snd_port']
    except KeyError:
        consumers = None

    return logger, limits, quality_checks, feedback, report_type, consumers, zmq_host, zmq_rcv_port, detector


def receive_zmq_send(dataq, zmq_host, zmq_rcv_port):
    """
    This function receives data from socket and enqueues it into a queue until the end is detected.

    Parameters
    ----------
    dataq : Queue
        a queue passing data received from ZeroMQ server to another process

    zmq_host : str
        ZeroMQ server host name

    zmq_rcv_port : str
        ZeroMQ port

    Returns
    -------
    none
    """

    conn = zmq_rec(zmq_host, zmq_rcv_port)
    socket = conn.socket
    interrupted = False
    while not interrupted:
        msg = socket.recv_json()
        key = msg.get("key")
        if key == "end":
            data = containers.Data(const.DATA_STATUS_END)
            dataq.put(data)
            interrupted = True
            conn.destroy()
        elif key == "image":
            msg["receiving_timestamp"] = time.time()
            dtype = msg["dtype"]
            shape = msg["shape"]
            image_number = msg['image_number']
            #image_timestamp = msg['image_timestamp']
            theta = msg['rotation']

            image = np.frombuffer(socket.recv(), dtype=dtype).reshape(shape)

            data = containers.Data(const.DATA_STATUS_DATA, image, 'data')
            data.theta = theta
            data.image_number = image_number
            dataq.put(data)


def verify(config):
    """
    This function starts real time verification process according to the given configuration.

    This function reads configuration and initiates variables accordingly.
    It starts the handler process that verifies data and starts a process receiving the data from ZeroMQ server.

    Parameters
    ----------
    conf : str
        configuration file name, including path

    Returns
    -------
    none

    """
    logger, limits, quality_checks, feedback, report_type, consumers, zmq_host, zmq_rcv_port, detector = init(config)

    feedback_obj = fb.Feedback(feedback)
    if const.FEEDBACK_LOG in feedback:
        feedback_obj.set_logger(logger)

    if const.FEEDBACK_PV in feedback:
        feedback_pvs = utils.get_feedback_pvs(quality_checks)
        feedback_obj.set_feedback_pv(feedback_pvs, detector)

    dataq = Queue()
    p = Process(target=handler.handle_data, args=(dataq, limits, None, quality_checks, None, consumers, feedback_obj))
    p.start()

    receive_zmq_send(dataq, zmq_host, zmq_rcv_port)
