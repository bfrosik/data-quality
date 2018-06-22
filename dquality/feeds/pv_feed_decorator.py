from dquality.feeds.pv_feed import Feed
import dquality.feeds.adapter as adapter
from epics import caget

class FeedDecorator(Feed):
    def __init__(self, decor):
        Feed.__init__(self)
        self.decor_map = {}
        for entry in decor:
            self.decor_map[entry] = decor[entry]


    def get_packed_data(self, data, data_type):
        args = {}
        for entry in self.decor_map:
            if entry == 'file_name':
                full_name = caget(self.decor_map[entry], as_string=True)
                rev_full_name = full_name[::-1]
                ind = rev_full_name.find('/')
                rev_name = rev_full_name[0:ind]
                file_name = rev_name[::-1]
                # for test
                #file_name = 'file'+str(caget('BBF1:cam1:ArrayCounter_RBV'))
                args[entry] = file_name
            else:
                args[entry] = caget(self.decor_map[entry])

        return adapter.pack_data(data, data_type, **args)


