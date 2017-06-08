from dquality.realtime.feed import Feed
import dquality.realtime.adapter as adapter
import dquality.common.constants as const
from epics import caget

class FeedDecorator(Feed):
    def __init__(self, decor):
        Feed.__init__(self)
        try:
            self.acq_time_pv = decor[const.QUALITYCHECK_RATE_SAT]
        except:
            self.acq_time_pv = None


    def get_packed_data(self, data, data_type):
        if self.acq_time_pv is None:
            return adapter.pack_data(data, data_type)
        else:
            acq_time = caget(self.acq_time_pv)
            return adapter.pack_data_with_decor(data, data_type, acq_time)


