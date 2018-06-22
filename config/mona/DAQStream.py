#!/home/beams/USER2BMB/Apps/BlueSky/bin/python

import argparse
import sys
import numpy as np
import zmq
import TraceSerializer
import time
import sys
import os
import pvaccess

sys.path.append(os.path.join(os.path.dirname(__file__), './local'))
import flatbuffers


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Data Acquisition Process')
    parser.add_argument("--image_pv", default="2bmbPG3:Pva1:Image",
                        help="EPICS PVA image PV name. Default to lyra point grey.")
    #arguments for zmq feed
    parser.add_argument("--feed_socket", default=5577,
                        help="A socket the data is received. Default to 5577.")
    parser.add_argument("--feed_host", default="localhost",
                        help="A host sending data. Default to localhost.")

    parser.add_argument('--bind_address_publisher', default="tcp://*:5560",
                        help='Address to bind publisher.')
    parser.add_argument('--publisher_hwm', type=int, default=10 * 1024,
                        help='Sets high water mark value for publisher.')
    parser.add_argument('--synchronize_subscribers', action='store_true',
                        help='Waits for all subscribers to join.')
    parser.add_argument('--subscriber_count', type=int,
                        help='Number of expected subscribers.')
    parser.add_argument('--bind_address_rep', default=None,
                        help='Address to bind REP socket (for synchronization)')

    parser.add_argument('--daq_mod', type=int, default=2,
                        help='Data acqusition mod (0=detector; 1=simulate; 2=test)')
    parser.add_argument('--simulation_file', default="../data/hornby_4_x1_conv.h5",
                        help='File name for mock data acquisition. '
                             'Default to shale data.')
    parser.add_argument('--beg_sinogram', type=int, default=0,
                        help='Starting sinogram for reconstruction.')
    parser.add_argument('--num_sinograms', type=int, default=0,
                        help='Number of sinograms to reconstruct.')
    parser.add_argument('--num_sinogram_columns', type=int, default=2048,
                        help='Number of columns per sinogram.')
    parser.add_argument('--num_sinogram_projections', type=int, default=1440,
                        help='Number of projections per sinogram.')
    return parser.parse_args()


def synchronize_subs(context, subscriber_count, bind_address_rep):
    print("Synching")
    # Socket to receive signals
    sync_socket = context.socket(zmq.REP)
    sync_socket.bind(bind_address_rep)

    # Get synchronization from subscribers
    counter = 0
    while counter < subscriber_count:
        # wait for synchronization request
        msg = sync_socket.recv()
        # send synchronization reply
        sync_socket.send(b'')
        counter += 1
        print("Joined subscriber: {}/{}".format(counter, subscriber_count))


def setup_simulation_data(input_f, beg_sinogram=0, num_sinograms=0):
    import h5py as h5
    ifptr = h5.File(input_f, 'r')
    # idata = np.array(ifptr['exchange/data'], dtype=np.float32)
    # itheta = np.array(ifptr['exchange/theta'], dtype=np.float32)
    # if num_sinograms>0:
    #    if (beg_sinogram<0) or (beg_sinogram+num_sinograms>idata.shape[1]):
    #      raise Exception("Exceeds the sinogram boundary: {} vs. {}".format(
    #                          beg_sinogram+num_sinograms, idata.shape[1]))
    #    idata = idata[:, beg_sinogram:beg_sinogram+num_sinograms, :]
    if num_sinograms > 0:
        idata = np.array(ifptr['exchange/data'][:, beg_sinogram:beg_sinogram + num_sinograms, :])
    else:
        idata = idata[:, beg_sinogram:beg_sinogram + num_sinograms, :]
    itheta = np.array(ifptr['exchange/theta'])
    ifptr.close()
    return idata, itheta


def test_daq(publisher_socket, builder,
             rotation_step=0.25, num_sinograms=0,
             num_sinogram_columns=2048, seq=0,
             num_sinogram_projections=1440):
    print("Sending projections")
    if num_sinograms < 1: num_sinograms = 2048
    # Randomly generate image data
    dims = (num_sinograms, num_sinogram_columns)
    image = np.random.randint(2, size=dims, dtype=np.uint16)

    for uniqueId in range(num_sinogram_projections):
        builder.Reset()
        serializer = TraceSerializer.ImageSerializer(builder)
        serialized_data = serializer.serialize(image=image, uniqueId=uniqueId + 7,
                                               rotation_step=rotation_step, seq=seq)
        seq += 1
        publisher_socket.send(serialized_data)

    return seq


def simulate_daq(publisher_socket, builder, input_f,
                 beg_sinogram=0, num_sinograms=0, seq=0):
    # Read image data and theta values
    idata, itheta = setup_simulation_data(input_f, beg_sinogram, num_sinograms)

    print(idata.shape, len(itheta), idata.size)
    for uniqueId, projId, rotation in zip(range(idata.shape[0]), range(idata.shape[0]), itheta):
        builder.Reset()
        proj = idata[projId]
        serializer = TraceSerializer.ImageSerializer(builder)
        serialized_data = serializer.serialize(image=proj, uniqueId=uniqueId,
                                               rotation=rotation, seq=seq)
        seq += 1
        publisher_socket.send(serialized_data)

    return seq


class TImageTransfer:
    def __init__(self, publisher_socket, pv_image, builder,
                 beg_sinogram=0, num_sinograms=0, seq=0):
        self.publisher_socket = publisher_socket
        self.pv_image = pv_image
        self.builder = builder
        self.beg_sinogram = beg_sinogram
        self.num_sinograms = num_sinograms
        self.seq = seq
        self.pv_channel = None

    def __enter__(self):
        self.pv_channel = pvaccess.Channel(self.pv_image)
        x, y = self.pv_channel.get('field()')['dimension']
        self.dims = (y['size'], x['size'])
        labels = [item["name"] for item in self.pv_channel.get('field()')["attribute"]]
        self.theta_key = labels.index("SampleRotary")
        self.scan_delta_key = labels.index("ScanDelta")
        self.start_position_key = labels.index("StartPos")
        print(self.dims)
        if self.num_sinograms > 0:
            if (self.beg_sinogram < 0) or (self.beg_sinogram + self.num_sinograms > self.dims[0]):
                raise Exception("Exceeds the sinogram boundary: {} vs. {}".format(
                    self.beg_sinogram + self.num_sinograms, self.dims[0]))
            self.beg_index = self.beg_sinogram * self.dims[1]
            self.end_index = self.beg_sinogram * self.dims[1] + self.num_sinograms * self.dims[1]
        self.pv_channel.subscribe('push_image_data', self.push_image_data)

        return self

    def start_monitor(self, smon="value,attribute,uniqueId"):
        self.pv_channel.startMonitor(smon)
        while True: time.sleep(60)  # Forever monitor

    def push_image_data(self, data):
        img = np.frombuffer(data['value'][0]['ushortValue'], dtype=np.uint16)
        uniqueId = data['uniqueId']
        # scanDelta = data['ScanDelta']
        # scanDelta = data['StartPos']
        # scanDelta = data['SaveDest']
        # theta = (uniqueID%360)*scanDelta
        # theta = (uniqueId%(360/0.24))*0.24
        # theta = data["attribute"][theta_key]["value"][0]["value"]
        scan_delta = data["attribute"][self.scan_delta_key]["value"][0]["value"]
        start_position = data["attribute"][self.start_position_key]["value"][0]["value"]
        theta = (start_position + uniqueId * scan_delta) % 360.0
        print(uniqueId, theta)
        if self.num_sinograms != 0:
            img = img[self.beg_index: self.end_index]
            img = img.reshape((self.num_sinograms, self.dims[1]))
        else:
            img = img.reshape(self.dims)

        self.builder.Reset()
        serializer = TraceSerializer.ImageSerializer(self.builder)
        serialized_data = serializer.serialize(image=img, uniqueId=uniqueId,
                                               rotation=theta, seq=self.seq)
        self.publisher_socket.send(serialized_data)
        self.seq += 1

    def __exit__(self, exc_type, exc_value, traceback):
        print("\nTrying to gracefully terminate...")
        self.pv_channel.stopMonitor()
        self.pv_channel.unsubscribe('push_image_data')

        print("Send terminate signal...")
        self.publisher_socket.send("end_data".encode())
        print("Done sending...")
        if exc_type is not None:
            print("{} {} {}".format(exc_type, exc_value, traceback))
            return False
        return self


class zmq_feed():
    """
    This class represents ZeroMQ connection.
    """
    def __init__(self, publisher_socket, feed_socket, feed_host, builder,
                 beg_sinogram=0, num_sinograms=0, seq=0):
        self.publisher_socket = publisher_socket
        self.builder = builder
        self.beg_sinogram = beg_sinogram
        self.num_sinograms = num_sinograms
        self.seq = seq

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.connect("tcp://" + feed_host +":%s" % feed_socket)

    def destroy(self):
        """
        Destroys Context. This also closes socket associated with the context.
        """
        self.context.destroy()


    def receive_zmq_send(self, zmq_host, zmq_rcv_port):
        """
        This function receives data from socket and sends it to publisher.
        """

        interrupted = False
        while not interrupted:
            print ('waiting')
            msg = self.socket.recv_json()
            key = msg.get("key")
            if key == "end":
                print ('end of data, closing connection')
                interrupted = True
                self.destroy()
            elif key == "dim":
                print('initializing dims')
                self.dims = (msg["dim_x"], msg["dim_y"])
                if self.num_sinograms > 0:
                    if (self.beg_sinogram < 0) or (self.beg_sinogram + self.num_sinograms > self.dims[0]):
                        raise Exception("Exceeds the sinogram boundary: {} vs. {}".format(
                            self.beg_sinogram + self.num_sinograms, self.dims[0]))
                    self.beg_index = self.beg_sinogram * self.dims[1]
                    self.end_index = self.beg_sinogram * self.dims[1] + self.num_sinograms * self.dims[1]
            elif key == "image":
                print('got msg')
                msg["receiving_timestamp"] = time.time()
                dtype = msg["dtype"]
                uniqueId = msg['image_number']
                theta = msg['theta']
                ver_result = msg['ver']


                img = np.frombuffer(self.socket.recv(), dtype=dtype)

                if self.num_sinograms != 0:
                    img = img[self.beg_index: self.end_index]
                    img = img.reshape((self.num_sinograms, self.dims[1]))
                else:
                    img = img.reshape(self.dims)

                self.builder.Reset()
                serializer = TraceSerializer.ImageSerializer(self.builder)
                serialized_data = serializer.serialize(image=img, uniqueId=uniqueId,
                                                       rotation=theta, seq=self.seq)
                self.publisher_socket.send(serialized_data)
                self.seq += 1

            else:
                pass

        print("Connection ended")

def main():
    args = parse_arguments()

    # Setup serializer
    builder = flatbuffers.Builder(0)

    # Setup zmq context
    context = zmq.Context()

    # Publisher setup
    publisher_socket = context.socket(zmq.PUB)
    publisher_socket.set_hwm(args.publisher_hwm)
    publisher_socket.bind(args.bind_address_publisher)

    # 1. Synchronize/handshake with remote
    if args.synchronize_subscribers:
        synchronize_subs(context, args.subscriber_count, args.bind_address_rep)

    # 2. Transfer data
    time0 = time.time()
    if args.daq_mod == 0:  # Read data from PV
        with TImageTransfer(publisher_socket=publisher_socket,
                            pv_image=args.image_pv, builder=builder,
                            beg_sinogram=args.beg_sinogram,
                            num_sinograms=args.num_sinograms, seq=0) as tdet:
            tdet.start_monitor()  # Infinite loop

    elif args.daq_mod == 1:  # Simulate data acquisition with a file
        simulate_daq(publisher_socket=publisher_socket,
                     input_f=args.simulation_file, builder=builder,
                     beg_sinogram=args.beg_sinogram, num_sinograms=args.num_sinograms)
    elif args.daq_mod == 2:  # Test data acquisition
        test_daq(publisher_socket=publisher_socket, builder=builder,
                 num_sinograms=args.num_sinograms,  # Y
                 num_sinogram_columns=args.num_sinogram_columns,  # X
                 num_sinogram_projections=args.num_sinogram_projections)  # Z
    elif args.daq_mod == 3:  # receive data over zmq connection
        with zmq_feed(publisher_socket=publisher_socket,
                      feed_socket=args.feed_socket, feed_host=args.feed_host, builder=builder,
                      beg_sinogram=args.beg_sinogram,
                      num_sinograms=args.num_sinograms, seq=0) as zfeed:
            zfeed.receive_zmq_send()
    else:
        print("Unknown mode: {}".format(args.daq_mod));

    publisher_socket.send("end_data".encode())
    time1 = time.time()
    print("Done sending; Total time={}".format(time1 - time0))


if __name__ == '__main__':
    main()