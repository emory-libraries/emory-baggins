'''
Bagging logic for LSDI digitized book content.

'''

import argparse

from baggins.digwf import Client


class LsdiBagger(object):

    def get_options(self):
        parser = argparse.ArgumentParser(
            description='Generate bagit bags from LSDI digitized book content')
        parser.add_argument('item_ids', metavar='ID', nargs='*',
                            help='Digitization Workflow Item ID')
        parser.add_argument('file', metavar='FILE',
                            help='Digitization Workflow File With Item IDs')
        self.options = parser.parse_args()
        if not self.options.item_ids or not self.options.file:
            print 'Please specify item ids or a file for items to process'
            parser.print_help()
            exit()

        if self.options.file:
            self.options.item_ids = self.load_item_ids()

    def run(self):
        self.get_options()
        self.process_items()


    def process_items(self):
        # TODO: get url from a config file
        digwf_api = Client('http://domokun.library.emory.edu:3000/digwf_api/')
        # digwf_api = Client('')


        for item_id in self.options.item_ids:
            result = digwf_api.get_items(item_id=item_id)
            if result.count == 1:
                item = result.items[0]
                print 'Found item %s (pid %s, control key %s)' % \
                    (item_id, item.pid or '-', item.control_key)
            elif result.count == 0:
                print 'No item found for item id %s' % item_id
            else:
                # shouldn't get more than one match when looking up by
                # item id, but just in case
                print 'Error! DigWF returned %d matches for item id %s' % \
                    (result.count, item_id)

    def load_item_ids(self):
        with open(self.options.file) as f:
            list_of_ids = [x.strip('\n') for x in f.readlines()]
            all_int = [s for s in list_of_ids if s.isdigit()]
            if not all_int:
                print 'All item ids should be numeric values. Check your file.'
                exit()

        return list_of_ids

        


