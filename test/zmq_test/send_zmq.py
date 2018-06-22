import dquality.common.utilities as utils
from dquality.feeds.feed import Feed

def init(config):
    conf = utils.get_config(config)
    if conf is None:
        print ('configuration file is missing')
        exit(-1)

    logger = utils.get_logger(__name__, conf)
    try:
        zmq_port = conf['zmq_rcv_port']
    except:
        zmq_port = None
        print ('configuration error: zmq_port not configured')

    try:
        detector = conf['detector']
    except KeyError:
        print ('configuration error: detector parameter not configured.')
        return None
    try:
        detector_basic = conf['detector_basic']
    except KeyError:
        print ('configuration error: detector_basic parameter not configured.')
        return None
    try:
        detector_image = conf['detector_image']
    except KeyError:
        print ('configuration error: detector_image parameter not configured.')
        return None

    try:
        no_frames = conf['no_frames']
    except KeyError:
        print ('no_frames parameter not configured.')
        return None

    return detector, detector_basic, detector_image, logger, zmq_port, no_frames

def run_sender(config):
    detector, detector_basic, detector_image, logger, zmq_port, no_frames = init(config)

    args = zmq_port, zmq_port
    feed = Feed()
    ack = feed.feed_data(int(no_frames), detector, detector_basic, detector_image, logger, None, *args)

    print ('done')

if __name__ == "__main__":
    run_sender('test/dqconfig.ini')