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

This module verifies a given file according to schema configuration and
starts new processes, each process performing specific quality calculations.

The results will be reported in a file (printed on screen for now)

"""

from multiprocessing import Queue, Process
from dquality.common.utilities import get_data
import dquality.handler as handler
from dquality.handler import Data
from configobj import ConfigObj
from os.path import expanduser
import os
import json
import sys

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['process_data']

home = expanduser("~")
config = os.path.join(home, 'dqconfig.ini')
conf = ConfigObj(config)

try:
    file = os.path.join(home, conf['file'])
    all_data = get_data(file)
except KeyError:
    print('config error: neither directory or file configured')
    sys.exit(-1)

try:
    limitsfile = os.path.join(home, conf['limits'])
    with open(limitsfile) as limits_file:
        limits = json.loads(limits_file.read())['limits']

except KeyError:
    print('config error: dependencies not configured')
    sys.exit(-1)

def process_data(dataq, data_type):
    """
    This method creates and starts a new handler process. The handler is initialized with data queue,
    dictionary of limits values keyed with data type, and the data type. The data type can
    be 'data_dark', 'data_white' or 'data'.
    After starting the process the function puts into data queue slice by slice, untils all data is
    queued. As the last element it enqueues end of data marker.

    Parameters
    ----------
    dataq : Queue
        data queue

    data_type : str
        string indicating what type of data is processed.

    Returns
    -------
    None
    """
    p = Process(target=handler.handle_data, args=(dataq, limits, data_type, ))
    p.start()
    data = all_data['/exchange/'+data_type]
    for i in range(0,data.shape[0]-1):
        dataq.put(Data(data[i],None))
    dataq.put('all_data')

def verify():
    """
    This invokes sequentially data verification process for data_dark, data_white, and data.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    #process data_dark
    process_data(Queue(),'data_dark')
    #process data_white
    process_data(Queue(),'data_white')
    #process data and theta
    process_data(Queue(),'data')
