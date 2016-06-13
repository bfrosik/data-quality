import sys
import os
import argparse
import dquality.doc.demo.monitor_check as monitor

def main(arg):

    parser = argparse.ArgumentParser()
    parser.add_argument("instrument", help="the detector indicator, can be nanotomo or microtomo")
    parser.add_argument("fname", help="folder name to monitor for files")
    parser.add_argument("type", help="data type to be verified (i.e. data_dark, data_white, or data)")
    parser.add_argument("numfiles", help="number of files to monitor for")
    parser.add_argument("repbyfile", help="boolean value defining how the bad indexes should be reported.")

    args = parser.parse_args()
    instrument = args.instrument
    fname = args.fname
    dtype = args.type
    num_files = args.numfiles
    by_file = args.repbyfile

    conf = os.path.join("/home/beams/USR32IDC/.dquality/b32id/", instrument)

    args = ['dquality', conf, fname, dtype, num_files, by_file]
    bad_indexes = monitor.main(args)
    return bad_indexes


if __name__ == "__main__":
    main(sys.argv[1:])

