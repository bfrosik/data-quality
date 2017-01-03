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

This module verifies that each of the PVs listed in the configuration
file exist and their values are set within the predefined range.

The results will be reported in a file (printed on screen for now).
An error will be reported back to UI via PV.

"""

import sys
import json
from epics import PV
import dquality.common.utilities as utils
from dquality.common.utilities import lt, le, eq, ge, gt


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['init',
           'verify',
           'read',
           'state']

def init(config):
    """
    This function initializes global variables. It gets values from the configuration file, evaluates and processes
    the values. If mandatory file or directory is missing, the script logs an error and exits.

    Parameters
    ----------
    config : str
        configuration file name, including path

    Returns
    -------
    logger : Logger
        logger instance

    pvs : dictionary
        a dictionary containing pvs values and attributes read from the configured 'pv_file' file

    """
    conf = utils.get_config(config)
    if conf is None:
        print ('configuration file is missing')
        exit(-1)

    logger = utils.get_logger(__name__, conf)

    pvfile = utils.get_file(conf, 'pv_file', logger)
    if pvfile is None:
        sys.exit(-1)

    with open(pvfile) as file:
        pvs = json.loads(file.read())['required_pvs']

    return logger, pvs


def read(pv_str):
    """
    This function returns a Process Variable (PV) value or None if the
    PV does not exist.

    Parameters
    ----------
    value : str
        name of the PV

    Returns
    -------
    PV value
    """
    pv = PV(pv_str).get()

    return pv


def state(value, limit):
    """
    This function takes boolean "*value*" parameter and string "limit"
    parameter that can be either "*True*" or "*False*". The limit is
    converted to string and compared with the value. The function
    returns True if the boolean values are equal, False otherwise.

    Parameters
    ----------
    value : numeric
        value

    limit : str
        limit value

    Returns
    -------
    boolean
    """
    if limit == 'True':
        return True
    else:
        return False


def verify(conf):
    """
    This function reads the :download:`schemas/pvs.json <../../../config/default/schemas/pvs.json>`
    as set in the :download:`dqconfig.ini <../../../config/default/dqconfig.ini>` file.
    This file contains dictionary with keys of mandatory process variables.
    The values is a dictionary of attributes, each attribute being either
    description, or a verification operation. The verification operation
    attribute has an operation as a key, and the value is the limit of the PV.
    The allowed keys are:

    - "*less_than*" - the PV value must be less than attribute value
    - "*less_or_equal*" - the PV value must be less than or equal attribute value
    - "*equal*" - the PV value must be equal to attribute value
    - "*greater_or_equal*" - the PV value must be greater than or equal attribute value
    - "*greater_than*" - the PV value must be greater than attribute value
    - "*state*" - to support boolean PVs. The defined value must be "True" or "False".

    Any missing PV (i.e. it can't be read) is an error that is reported
    (printed for now). Any PV value that is out of limit is an error that
    is reported (printed for now). The function returns True if no
    error was found and False otherwise.

    Parameters
    ----------
    conf : str
        configuration file name, including path

    Returns
    -------
    boolean
    """

    logger, required_pvs = init(conf)

    logger.info('verifying process variables')
    function_mapper = {
        'less_than': lt,
        'less_or_equal': le,
        'equal': eq,
        'greater_or_equal': ge,
        'greater_than': gt,
        'state': state}

    res = True

    for pv in required_pvs:
        # possible the read pv needs try statement
        pv_value = read(pv)

        if pv_value is None:
            res = False
            logger.warning('PV ' + pv + ' cannot be read.')
        else:
            pv_attr = required_pvs[pv]
            for attr in pv_attr:
                if attr == 'description':
                    descriprtion = pv_attr['description']
                else:
                    if not function_mapper[attr](pv_value, pv_attr[attr]):
                        res = False
                        logger.warning('PV ' +
                                       pv + ' has value out of range. ' +
                                       'The value is ' +
                                       str(pv_value) + ' but should be ' +
                                       attr + ' ' +
                                       str(pv_attr[attr]))
    if res:
        logger.info('All PVs listed in pvs.json exist and meet conditions')
    return res
