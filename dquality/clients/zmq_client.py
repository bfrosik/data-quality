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

This module feeds data to ZeroMQ connection.

The data, which represents a frame captured by detector, is sent in two parts. The first part is a json
stream and contains data attributes, such shape, type, theta and counter associated with this frame.
The second part is frame in bytes.

This module requires configuration file with the following parameters:
'zmq_snd_port' - the ZeroMQ port the messages will be sent
"""

import zmq
import dquality.common.constants as const


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['zmq_sen.zmq_sen',
           'zmq_sen.send_to_zmq']


class zmq_sen():
    """
    This class represents ZeroMQ server.
    """
    def __init__(self, port=None):
        """
        Constructor

        This constructor creates zmq Context and socket for the zmq.PAIR.
        It binds with the port and will accept one connection.

        Parameters
        ----------
        port : str
            serving port

        """
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.bind("tcp://*:%s" % port)


    def send_to_zmq(self, data):
        """
        This sends out received data to an established connection.

        Parameters
        ----------
        data : Data object
            a Data instance containing frame attributes and frame data

        Returns
        -------
        none
        """
        if data.status == const.DATA_STATUS_END:
            self.socket.send_json(
                dict(
                    key="end",
                    document="... end of transmission ...",
                ))
            self.context.destroy()
        if data.status == const.DATA_STATUS_DIM:
            self.socket.send_json(
                dict(
                    key="dim",
                    dim_x=data.dim_x,
                    dim_y=data.dim_y,
                ))
        else:
            slice = data.slice
            self.socket.send_json(
                dict(
                    key="image",
                    dtype=str(slice.dtype),
                    shape=slice.shape,
                    ver=data.ver,
                    image_number=data.image_number,
                    theta= data.theta,
                    # image_timestamp=image_time,
                    # sending_timestamp=time.time(),
                    # rotation=_cache_["rotation"],
                    # rotation_timestamp=rotation_time,
                    document="... see next message ...",

                ), zmq.SNDMORE
            )
            # binary image is not serializable in JSON, send separately
            self.socket.send(slice.flatten())
