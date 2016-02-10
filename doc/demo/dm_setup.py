#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) 2015, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2015. UChicago Argonne, LLC. This software was produced       #
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
Module containing an example on how to use DMagic to setup an experiment for 
automatic data distribution to users via Globus sharing the personal and the
remote endpoints.

"""

import pytz
import datetime
import sys

# set ~/globus.ini and ~/scheduling.ini to match your configuration
import dmagic.scheduling as sch
import dmagic.globus as gb

# pring the current Globus settings
gb.dm_settings()

# set the experiment date 
# now = datetime.date.today()

now = datetime.datetime(2014, 10, 18, 10, 10, 30).replace(tzinfo=pytz.timezone('US/Central'))
print "\n\nToday's date: ", now

# find the experiment starting date
exp_start = sch.find_experiment_start(now)
print "Experiment starting date/time: ", exp_start

# create a unique experiment ID using GUP and beamtime request (BR) numbers as: 
# g + GUP# + r + BR#
#exp_id = sch.create_experiment_id(now)
             
# create an experiment ID using the PI last name: 
exp_id = sch.find_pi_last_name(now)

print "Experiment ID: ", exp_id

# create a directory to store the raw data as: 
# \local_folder\YYYY-MM\gGUP#rBR#\  or
# \local_folder\YYYY-MM\PI_last_name\  
directory = gb.dm_create_directory(exp_start, exp_id)

# find the user running now
users = sch.find_users(now)

# print user information
sch.print_users(users)

# share the data directory in the personal end point with the users. 
# users will receive an e-mail with a drop-box style link to access the data
cmd = gb.dm_share(directory, users, 'personal')
for share in cmd: 
    print share
    #os.system(share)

# upload the raw data to the remote Globus server set in globus.ini (i.e. petrel)
# upload creates a folder YYYY-MM then copy the raw data from the Globus Personal
# endpoint to the remote Globus server
cmd1, cmd2 = gb.dm_upload(directory)
print cmd1
print cmd2
#os.system(cmd1)
#os.system(cmd2)

# share the raw data directory on the Globus server with the users. 
# users will receive an e-mail with a drop-box style link to access the data
cmd = gb.dm_share(directory, users, 'remote')
for share in cmd: 
    print share
    #os.system(share)


