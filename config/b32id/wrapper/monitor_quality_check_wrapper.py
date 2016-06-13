import sys
import os
import argparse
import dquality.doc.demo.monitor_quality_check as monitor

def main(arg):

    parser = argparse.ArgumentParser()
    parser.add_argument("instrument", help="the detector indicator, can be nanotomo or microtomo")
    parser.add_argument("fname", help="folder name to monitor for files")
    parser.add_argument("numfiles", help="number of files to monitor for")

    args = parser.parse_args()
    instrument = args.instrument
    fname = args.fname
    num_files = args.numfiles

    conf = os.path.join("/home/beams/USR32IDC/.dquality/b32id/", instrument)

    args = ['monitor', conf, fname, num_files]
    bad_indexes = monitor.main(args)
    return bad_indexes


if __name__ == "__main__":
    main(sys.argv[1:])


