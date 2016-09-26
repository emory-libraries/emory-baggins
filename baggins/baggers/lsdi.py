'''
Bagging logic for LSDI digitized book content.

'''

import argparse
import bagit
from ConfigParser import ConfigParser, NoOptionError, NoSectionError
import glob
import os
import requests
import shutil

from baggins.digwf import Client
from baggins.baggers import bag


class LsdiBaggee(bag.Baggee):
    '''Bag object extending base baggee class, for creating lsdi
    bags according to emory bagit specification.
    '''

    def __init__(self, item):
        self.item = item

    def object_id(self):
        '''Object id for bag name; use pid/ark if available; otherwise, use
        digwf control key (OCLC #)'''
        return self.item.pid or self.item.control_key

    def object_title(self):
        '''Object title for bag name: use title from MARC xml'''
        return self.item.marc.title()


    def data_files(self):
        '''List of data files to be included in the bag.  PDF, OCR xml,
        page images, and page text/position files.'''
        return [self.item.pdf, self.item.ocr_file] + self.image_files() \
            + self.page_text_files()

    def image_files(self):
        '''Find image files based on display image path returned from the
        DigWF API.  Looks for TIFFs, then JP2s, thn JPG files.  Raises an error
        if the number of images found doesn't match the expected count in the
        item information returned by the DigWF APi.
        '''
        image_path = self.item.display_image_path
        # first, look for TIFFs
        images = glob.glob('%s/*.tif' % image_path)
        # tif variant - in some cases, extension is upper case
        if not len(images):
            images = glob.glob('%s/*.TIF' % image_path)
        # if no TIFFs were found, look for JP2s
        if not len(images):
            images = glob.glob(os.path.join(image_path, '*.jp2'))
        # if neither jp2s nor tiffs were found, look for jpgs
        if not len(images):
            images = glob.glob('%s/*.jpg' % image_path)

        # if images were not found, error
        if not len(images):
            raise Exception('Display images not found for %s at %s' %
                            (self.item.item_id, image_path))
        # if wrong number of images were found, error
        if len(images) != self.item.display_image_count:
            raise Exception('Found %d images for %s instead of expected %d' %
                            (len(images), self.item.item_id,
                            self.item.display_image_count))
        return images

    def page_text_files(self):
        '''Find text and position files based on ocr file path returned from the
        DigWF API.  Raises an error if the number of text files or the number
        of position files found doesn't match the expected count in the
        item information returned by the DigWF APi.
        '''
        ocr_path = self.item.ocr_file_path
        # plain text files generated from ocr
        text_files = glob.glob('%s/*.txt' % ocr_path)
        # position files generated from ocr process
        pos_files = glob.glob('%s/*.pos' % ocr_path)
        if len(text_files) != self.item.ocr_file_count:
            raise Exception('Found %d text files for %s instead of expected %d',
                            len(text_files), self.item.item_id,
                            self.item.ocr_file_count)
        if len(pos_files) != self.item.ocr_file_count:
            raise Exception('Found %d position files for %s instead of expected %d',
                            len(pos_files), self.item.item_id,
                            self.item.ocr_file_count)
        return text_files + pos_files


class LsdiBagger(object):
    '''Logic for the lsdi-bagger script.  Handles argument parsing, config file
    generation and loading, and processing items.
    '''

    #: parsed argument and configuration options
    options = argparse.Namespace()   # start with an empty args namespace

    def get_options(self):
        parser = argparse.ArgumentParser(
            description='Generate bagit bags from LSDI digitized book content')
        parser.add_argument('item_ids', metavar='ITEM_IDS', nargs='*',
                            help='Digitization Workflow Item ID')

        parser.add_argument('-f', '-file', metavar='FILE',
                            help='Digitization Workflow File With Item IDs')


        parser.add_argument('-o', '--output', metavar='OUTPUT_DIR',
                            help='Directory for generated bag content')

        # config file options
        cfg_args = parser.add_argument_group('Config file options')
        cfg_args.add_argument(
            '--generate-config', '-g', dest='gen_config',
            help='''Create a sample config file at the specified location,
            including any options passed.''')
        cfg_args.add_argument('--config', '-c', default='$HOME/.lsdi-bagger',
                              help='Load the specified config file (default: %(default)s)')

        # parse command line arguments
        self.options = parser.parse_args()

        if not self.options.item_ids or not self.options.file:
            print 'Please specify item ids or a file for items to process'
            parser.print_help()
            exit()

        if self.options.file:
            self.options.item_ids = self.load_item_ids()

        # if requested, generate an empty config file that can be filled in
        # and then quit
        if self.options.gen_config:
            self.generate_configfile()
            exit()

        # load config file
        self.load_configfile()

        # output directory is required (config file or flag)
        if not self.options.output:
            print 'Please specify output directory'
            parser.print_help()
            exit()

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
                print 'Found item %s (pid %s, control key %s, marc %s)' % \
                    (item_id, item.pid or '-', item.control_key,
                     item.marc_path)
            elif result.count == 0:
                print 'No item found for item id %s' % item_id
                continue
            else:
                # shouldn't get more than one match when looking up by
                # item id, but just in case
                print 'Error! DigWF returned %d matches for item id %s' % \
                    (result.count, item_id)

                continue

            # returns a bagit bag object.
            newbag = LsdiBaggee(item).create_bag(self.options.output)

            # generate source organization summaary for this bag
            # self.load_source_summary(newbag)

            print 'Bag created at %s' % newbag

    # config file section headings
    digwf_cfg = 'Digitization Workflow'
    filepaths_cfg = 'File Paths'

    def setup_configparser(self):
        # define a config file parser with options for required
        # configurations needed by this script
        config = ConfigParser()
        # digwf
        config.add_section(self.digwf_cfg)
        config.set(self.digwf_cfg, 'url', 'http://server:port/digwf_api/')
        # file paths
        config.add_section(self.filepaths_cfg)
        config.set(self.filepaths_cfg, 'output', self.options.output or '')
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

        # add needed configs to options object
        # - digwf url is required
        try:
            self.options.digwf_url = cfg.get(self.digwf_cfg, 'url')
        except (NoOptionError, NoSectionError):
            pass

        if not getattr(self.options, 'digwf_url', None):
            print 'Error: Digitization Workflow URL not configured'
            exit()

        # output could be specified via command line or config file;
        # command line flag overrules config
        if cfg.has_option(self.filepaths_cfg, 'output') and \
           not self.options.output:
            self.options.output = cfg.get(self.filepaths_cfg, 'output')

    def load_item_ids(self):
        try:
            with open(self.options.file) as f:
                list_of_ids = [x.strip('\n') for x in f.readlines()]
            return list_of_ids
        except IOError:
            print "Unable to load specified csv file"


    # def load_source_summary(self, bag):
    #     summary_path = self.generate_bag_info_file()
    #     summary_list = []
    #     with open(summary_path, 'w') as summaryfile:
    #         summary_list[0] = "Source-Organization: " + bag.source_organization()
    #         summary_list[1] = "Organization-Address" + bag.organization_address()
    #         summary_list[2] = "Contact-Name: " + bag.contact_name()
    #         summary_list[3] = "Contact-Phone: " + bag.contact_phone()
    #         summary_list[4] = "Contact-Email: " + bag.contact_email()
    #         summary_list[5] = "External-Description: " + bag.external_description()
    #         summary_list[6] = "Bagging-Date: " + bag.bagging_date()
    #         summary_list[7] = "External-Identifier: " + bag.external_identifier()
    #         summary_list[8] = "Bag-Size: " + bag.bag_size()
    #         summary_list[9] = "Bag-Group-Identifier: " + bag.bag_group_identifier()

    #     for summary_item in summary_list:
    #         summaryfile.write(summary_item)




    # def generate_bag_info_file(self):
    #     # generate an empty summary file
    #     summary_path = os.environ['HOME'] + '/bag-info.txt'
    #     with open(summary_path, 'w') as summaryfile:
    #         config.write(summaryfile)
    #     print 'Bag info file created at %s' % summary_path
    #     return summary_path








