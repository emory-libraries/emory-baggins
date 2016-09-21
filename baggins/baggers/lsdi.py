'''
Bagging logic for LSDI digitized book content.

'''

import argparse
from ConfigParser import ConfigParser, NoOptionError, NoSectionError
import os
import requests

from baggins.digwf import Client


class LsdiBagger(object):

    #: parsed argument and configuration options
    options = None

    def get_options(self):
        parser = argparse.ArgumentParser(
            description='Generate bagit bags from LSDI digitized book content')
        parser.add_argument('item_ids', metavar='Item ID', nargs='*',
                            help='Digitization Workflow Item ID')

        # config file options
        cfg_args = parser.add_argument_group('Config file options')
        cfg_args.add_argument(
            '--generate-config', '-g', default=False, dest='gen_config',
            help='''Create a sample config file at the specified location''')
        cfg_args.add_argument('--config', '-c', default='$HOME/.lsdi-bagger',
                              help='Load the specified config file')

        # parse command line arguments
        self.options = parser.parse_args()

        # if requested, generate an empty config file that can be filled in
        if self.options.gen_config:
            self.generate_configfile()
            return

        # check that we have something to process
        if not self.options.item_ids:
            print 'Please specify one or more item ids for items to process'
            parser.print_help()
            exit()

        # load config file
        self.load_configfile()

    def run(self):
        self.get_options()
        self.process_items()

    def process_items(self):
        digwf_api = Client(self.options.digwf_url)
        for item_id in self.options.item_ids:
            try:
                result = digwf_api.get_items(item_id=item_id)
            except requests.exceptions.HTTPError as err:
                print 'Error querying API for %s: %s' % (item_id, err)
                continue

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

    # config file section headings
    digwf_cfg = 'Digitization Workflow'

    def setup_configparser(self):
        # define a config file parser with options for required
        # configurations needed by this script
        config = ConfigParser()
        # digwf
        config.add_section(self.digwf_cfg)
        config.set(self.digwf_cfg, 'url', 'http://server:port/digwf_api/')
        # eventually we will have more config options here...
        return config

    def generate_configfile(self):
        # generate an empty config file that with appropriate values
        config = self.setup_configparser()
        with open(self.options.gen_config, 'w') as cfgfile:
            config.write(cfgfile)
        print 'Config file created at %s' % self.options.gen_config

    def load_configfile(self):
        # load config file
        cfg = ConfigParser()
        configfile_path = self.options.config.replace('$HOME',
                                                      os.environ['HOME'])
        try:
            with open(configfile_path) as cfgfile:
                cfg.readfp(cfgfile)
        except IOError:
            print 'Unable to load config file at %s' % configfile_path
            print 'Please generate or specify a config file.'
            exit()

        # add need configs to options object
        try:
            self.options.digwf_url = cfg.get(self.digwf_cfg, 'url')
        except (NoOptionError, NoSectionError):
            pass

        if not getattr(self.options, 'digwf_url', None):
            print 'Error: Digitization Workflow URL not configured'
            exit()
