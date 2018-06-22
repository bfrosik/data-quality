from multiprocessing import Process
from dquality.feeds.zmq_sender import receive_send_zmq
import dquality.common.containers as containers
import dquality.common.constants as const
import dquality.common.utilities as utils


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['start_process',
           'parse_config',
           'pack_data']



def start_process(dataq, logger, *args):
    """
    This function parses parameters and starts process consuming frames from feed.

    This function parses the positional parameters. Then it starts a client process, passing in a queue as first
    parameter, followed by the parsed parameters. The function of the client process must be included in imports.

    Parameters
    ----------
    dataq : multiprocessing.Queue
        a queue used to transfer data from feed to client process

    logger : Logger
        an instance of Logger, used by the application

    *args : list
        a list of posisional parameters required by the client process

    Returns
    -------
    none
    """
    zmq_port = args[0]

    p = Process(target=receive_send_zmq, args=(dataq, zmq_port))
    p.start()


def pack_data(slice, type):
    """
    This function packs a single image data into a specific container.

    Parameters
    ----------
    slice : nparray
        image data

    type : str
       data type, as 'data', 'data_white', or 'data_dark'

    """
    if slice is not None:
        return containers.Data(const.DATA_STATUS_DATA, slice, type)
    elif type == 'missing':
        return containers.Data(const.DATA_STATUS_MISSING)
    else:
        return containers.Data(const.DATA_STATUS_END)

