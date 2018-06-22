import dquality.feeds.zmq_receiver as rec

def run_recev(config):
    rec.verify(config)

if __name__ == "__main__":
    run_recev('test/dqconfig.ini')