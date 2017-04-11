QUALITYCHECK_MEAN = 1
QUALITYCHECK_STD = 2
QUALITYCHECK_SAT = 3
STAT_START = 100
STAT_MEAN = 100
ACC_SAT = 101

QUALITYERROR_LOW = -1
QUALITYERROR_HIGH = -2
NO_ERROR = 0

FILE_TYPE_HDF = 'FILE_TYPE_HDF'
FILE_TYPE_GE = 'FILE_TYPE_GE'

REPORT_NONE = 'none'
REPORT_ERRORS = 'errors'
REPORT_FULL = 'full'

FEEDBACK_CONSOLE = 'console'
FEEDBACK_LOG = 'log'
FEEDBACK_PV = 'pv'

DATA_STATUS_DATA = 0
DATA_STATUS_MISSING = 1
DATA_STATUS_END = 2

mapper = {
    'QUALITYCHECK_MEAN' : 1,
    'QUALITYCHECK_STD' : 2,
    'QUALITYCHECK_SAT' : 3,
    'STAT_START' : 100,
    'STAT_MEAN' : 100,
    'ACC_SAT' : 101,

    'QUALITYERROR_LOW' : -1,
    'QUALITYERROR_HIGH' : -2,
    'NO_ERROR' : 0,
}

def shared(name):
    return mapper[name]

def check_tostring(qualitycheck):
    qc_map = {1:'mean',
              2:'st_dev',
              3:'saturation',
              100:'stat_mean',
              101:'acc_sat'}
    return qc_map[qualitycheck]
