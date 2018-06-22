from multiprocessing import Queue, Process
import numpy as np
import zmq
import time
import sys
import json

#This module is for testing onle, acts as a zmq consumer

class zmq_rec():
    """
    This class represents ZeroMQ connection.
    """
    def __init__(self, host=None, port=None):
        """
        Constructor

        This constructor creates zmq Context and socket for the zmq.PAIR.
        It initiate connect to the server given by host and port.

        Parameters
        ----------
        host : str
            server host name

        port : str
            serving port

        """
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.connect("tcp://" + host +":%s" % port)

    def destroy(self):
        """
        Destroys Context. This also closes socket associated with the context.
        """
        self.context.destroy()


def receive_zmq_send(zmq_host, zmq_rcv_port):
    """
    This function receives data from socket and enqueues it into a queue until the end is detected.

    Parameters
    ----------
    dataq : Queue
        a queue passing data received from ZeroMQ server to another process

    zmq_host : str
        ZeroMQ server host name

    zmq_rcv_port : str
        ZeroMQ port

    Returns
    -------
    none
    """

    conn = zmq_rec(zmq_host, zmq_rcv_port)
    socket = conn.socket
    interrupted = False
    while not interrupted:
        print ('waiting')
        msg = socket.recv_json()
        key = msg.get("key")
        if key == "end":
            print ('end of data, closing connection')
            interrupted = True
            conn.destroy()
        elif key == "image":
            print('got msg')
            msg["receiving_timestamp"] = time.time()
            dtype = msg["dtype"]
            shape = msg["shape"]
            image_number = msg['image_number']
            #image_timestamp = msg['image_timestamp']
            theta = msg['theta']
            ver_result = msg['ver']

            image = np.frombuffer(socket.recv(), dtype=dtype).reshape(shape)
            print ('theta, index', theta, image_number, ver_result)
           # print ('received data, index, theta, ver_result', data.shape, image_number, theta, ver_result)
        else:
            pass

    print("Connection ended")

if __name__ == "__main__":
    receive_zmq_send('localhost', 5577)

