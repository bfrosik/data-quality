#!/bin/bash

cd $1
export EPICS_CA_ADDR_LIST="164.54.11.255:fffffc00"
export EPICS_CA_AUTO_ADDR_LIST="NO"
python server_verifier.py $2 $3 $4 $5 $6

