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
Module to share a Globus Personal shared folder with a user by sending an e-mail.
"""

import os
import sys
import string
import argparse
import platform
import unicodedata
import ConfigParser

from os.path import expanduser
from distutils.dir_util import mkpath
from validate_email import validate_email

__author__ = "Francesco De Carlo"
__copyright__ = "Copyright (c) 2015, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'

def clean_folder_name(directory):

    valid_folder_name_chars = "-_"+ os.sep + "%s%s" % (string.ascii_letters, string.digits)
    cleaned_folder_name = unicodedata.normalize('NFKD', directory.decode('utf-8', 'ignore')).encode('ASCII', 'ignore')
    
    return ''.join(c for c in cleaned_folder_name if c in valid_folder_name_chars)


def try_email(email):

    try: 
        if validate_email(email):
            return True
    except: 
        pass # or raise
    else: 
        print "e-mail address in not valid"
        return False

def try_folder(directory):

    try:
        home = expanduser("~")
        globus = os.path.join(home, 'globus.ini')
        cf = ConfigParser.ConfigParser()
        cf.read(globus)
        personal_folder = cf.get('globus connect personal', 'folder')  
        if os.path.isdir(personal_folder + directory):
            print personal_folder + directory + " exists"
            return True
        else:
            print directory + " does not exist under " + personal_folder
            a = raw_input('Would you like to create ' + directory + ' ? ').lower()
            if a.startswith('y'): 
                mkpath(personal_folder + directory)
                print("Great!")
                return True
            else:
                print ("Sorry for asking...")
                return False
    except: 
        pass # or raise
    else: 
        return False

def try_platform():
    home = expanduser("~")
    globus = os.path.join(home, 'globus.ini')
    cf = ConfigParser.ConfigParser()
    cf.read(globus)
    personal_host = cf.get('globus connect personal', 'host') 

    try: 
        if (platform.node().split('.')[0] == personal_host):
            return True
    except: 
        pass # or raise
    else: 
        print "WARNING: This command only runs on", personal_host
        return False

def main(argv):
    home = expanduser("~")
    globus = os.path.join(home, 'globus.ini')
    cf = ConfigParser.ConfigParser()
    cf.read(globus)

    globus_address = cf.get('settings', 'cli_address')
    globus_user = cf.get('settings', 'cli_user')
    globus_ssh = "ssh " + globus_user + globus_address

    user = cf.get('globus connect personal', 'user') 
    share = cf.get('globus connect personal', 'share')

    personal_folder = cf.get('globus connect personal', 'folder')  

    parser = argparse.ArgumentParser()
    parser.add_argument("folder", help="new or existing folder under " + personal_folder)
    parser.add_argument("email", help="user e-mail address")
    args = parser.parse_args()

    try: 
        args.folder = args.folder[0].strip(os.sep) + args.folder[1:] # will remove the front slash if it is there.
        folder = os.path.normpath(clean_folder_name(args.folder)) + os.sep # will add the trailing slash if it's not already there.
        if (try_platform() and try_email(args.email) and try_folder(folder)):
            # ready for new CLI release
            #globus_add = "acl-add " + user + share + os.sep + folder  + " --perm r --identityusername " + args.email + " --notify-email=" + args.email + " --notify-message=" + '"Here are your data from the TXM"' 
            globus_add = "acl-add " + user + share + os.sep + folder  + " --perm r --email " + args.email
            #print globus_add        
            cmd = globus_ssh + " " + globus_add
            print cmd
            #os.system(cmd)

    except: pass

if __name__ == "__main__":
   main(sys.argv[1:])
   
