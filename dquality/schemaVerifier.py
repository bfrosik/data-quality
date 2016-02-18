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
This file contains verification functions related to the file structure.
It reads configuration parameters "schema_type" and 'schema' to determine first which kind of file verification is requested, and a schema that defines mandatory parameters.
If any of the parameters is not configured, it is assumed no file structure verification is requested.

"""

import h5py
import xml.etree.ElementTree as et
from configobj import ConfigObj

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['verify_schema_hd5',
           'verify_schema']

config = ConfigObj('config.ini')

def verify_schema_hd5(file, schema):
    """
    This method is used when a file of hd5 type is given. 
    All tags from the hd5 file are added in the filetags list.
    Then the schema is evaluated for tags. With each tag discovered it checks whether there is matching tag in the filetags list.
    If a tag is missing, the function exits with False.
    Otherwise, it will return True.
     
    Parameters
    ----------
    file : str
        File Name including path
    
    schema : str
        Schema file name

    Returns
    -------
    True if verified
    False if not verified
        
    """

    class Result:
        def __init__(self):
            self.result = True
        def missing_tag(self):
            self.result = False
        def is_verified(self):
            return self.result

    result = Result()
    filetags = []

    def func(name, dset):
        if isinstance(dset, h5py.Dataset):
            filetags.append(dset.name)

    file_h5 = h5py.File(file, 'r')
    file_h5.visititems(func)

    def children(root, path):
        for child in root:
            if result.is_verified():
                if child.tag == 'folder':
                    children(child, path+child.attrib['name']+'/')
                else:
                    tag = path+child.text
                    if tag not in filetags:
                        print ('tag ' + tag + ' not found')
                        result.missing_tag()

    tree = et.parse(schema)
    root = tree.getroot()
    children(root, '/')
    return result.is_verified()

def verify_schema(file):
    """
    This method reads configuration parameter 'schema-type'. If not configured, the function returns True, 
    as no verification is needed.
    In case the type is set, the follow up logic determines, what type of verification should be applied.
    Currently, the HD5 type is supported.
    The function then reads the schema file from config. If not configured, the function returns True, as 
    no verification is needed.
    Otherwise, it will call the appropriate verification function and will return the result.
     
    Parameters
    ----------
    file : str
        File Name including path
    
    Returns
    -------
    True if verified
    False if not verified
        
    """

    try:
        type = config['schema_type']
        if type == 'hd5':
            try:
                schema = config['schema']
                return verify_schema_hd5(file, schema)
            except KeyError:
                return True
            except:
                print ('configuration error: schema file ' + schema + ' does not exist')
                return False


    except KeyError:
        return True
