QUALITYCHECK_MEAN = 1
QUALITYCHECK_STD = 2
QUALITYCHECK_SAT = 3
QUALITYCHECK_SUM = 4
QUALITYCHECK_FRAME_SAT = 5
QUALITYCHECK_RATE_SAT = 6
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
    'QUALITYCHECK_SUM' : 4,
    'QUALITYCHECK_FRAME_SAT' : 5,
    'QUALITYCHECK_RATE_SAT' : 6,
    'STAT_START' : 100,
    'STAT_MEAN' : 100,
    'ACC_SAT' : 101,

    'QUALITYERROR_LOW' : -1,
    'QUALITYERROR_HIGH' : -2,
    'NO_ERROR' : 0,
}

def get_id(name):
    return mapper[name]

def to_string(qualitycheck):
    qc_map = {1:'mean',
              2:'st_dev',
              3:'saturation',
              4:'sum',
              5:'frame_sat',
              6:'rate_sat',
              100:'stat_mean',
              101:'acc_sat'}
    return qc_map[qualitycheck]
