import sys
import os
import argparse
import dquality.doc.demo.dquality_check as dquality

def main(arg):

    parser = argparse.ArgumentParser()
    parser.add_argument("instrument", help="the detector indicator, can be nanotomo or microtomo")
    parser.add_argument("fname", help="file name to do the tag dependencies checks on")

    args = parser.parse_args()
    instrument = args.instrument
    fname = args.fname

    conf = os.path.join("/home/beams/USR32IDC/.dquality/b32id/", instrument)

    args = ['dquality', conf, fname]
    bad_indexes = dquality.main(args)
    return bad_indexes


if __name__ == "__main__":
    main(sys.argv[1:])


