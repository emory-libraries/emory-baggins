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
        parser.add_argument('file', metavar='FILE', nargs='*',
                            help='Digitization Workflow File With Item IDs')
        self.options = parser.parse_args()
        if not self.options.item_ids or not self.options.file:
            print 'Please specify one or more item ids for items to process'
            parser.print_help()
            exit()

    def run(self):
        self.get_options()
        self.process_items()


    def process_items(self):
        # TODO: get url from a config file
        digwf_api = Client('http://domokun.library.emory.edu:3000/digwf_api/')
        # digwf_api = Client('')
        if self.options.item_ids:
            item_ids = self.options.item_ids
        else:
            item_ids = self.load_item_ids()

        for item_id in item_ids:
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
        list_of_ids = []
        with open(self.options.file) as f:
            for line in f:
                file_list = [int(element.strip()) for element in line.split(',')]
                list_of_ids.append(file_list)

        return list_of_ids


