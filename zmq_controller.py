import zmq
import os
import signal
import sys
from os.path import expanduser
import dquality.real_time_pv as real
import dquality.common.constants as const
import threading
import time


class zmq_server():
    """
    This class represents ZeroMQ connection.
    """

    def __init__(self, port=const.ZMQ_CONTROLLER_PORT):
        """
        Constructor

        This constructor creates zmq Context and socket for the server in zmq.PAIR.
        It initiate binds and listens for a connection.

        Parameters
        ----------
        port : str
            serving port

        """

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.bind("tcp://*:%s" % port)
        self.ver = None
        self.interrupted = False


    def destroy(self):
        """
        Destroys Context. This also closes socket associated with the context.
        """
        self.interrupted = True
        self.socket.close()
        self.context.destroy()


def receive(conn):
    """
    This function receives data from socket and enqueues it into a queue until the end is detected.

    Parameters
    ----------
    conn : zmq_server
        a zmq_server instance

    Returns
    -------
    none
    """
    while not conn.interrupted:
        msg = conn.socket.recv_json()
        key = msg.get("key")
        if key == "start_ver":
            detector = msg["detector"]
            home = expanduser("~")
            conf = os.path.join(home, '.dquality', detector)
            if os.path.isdir(conf):
                config = os.path.join(conf, 'dqconfig.ini')
            if not os.path.isfile(config):
                print ('missing configuration file')
            else:
                conn.ver = real.RT()
                th = threading.Thread(target=conn.ver.verify, args=(config,))
                th.start()

        elif key == "stop_ver":
            # print('stopping ver')
            if not conn.ver is None:
                conn.ver.finish()
            conn.ver = None

        else:
            pass

    print("Connection ended")

if __name__ == "__main__":
    def signal_handler(signal, frame):
        if not conn.ver is None:
            conn.ver.finish()
            time.sleep(1)
        conn.destroy()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    conn = zmq_server(const.ZMQ_CONTROLLER_PORT)
    receive(conn)

