'''
Bagging logic for LSDI digitized book content.

'''

import argparse
from optparse import OptionParser
from ConfigParser import ConfigParser, NoOptionError, NoSectionError
import glob
import os
import requests
import yaml
import sys
import re

from lxml import etree
from eulfedora.server import Repository
from baggins.lsdi.collections import CollectionSources
from baggins.lsdi.digwf import Client
from baggins.lsdi.fedora import Volume
from baggins.baggers import bag
from baggins.lsdi.mets import Mets, METSFile, METSMap

sys.tracebacklimit = 0


class LsdiBaggee(bag.Baggee):
    '''Bag object extending base baggee class, for creating lsdi
    bags according to emory bagit specification.
    '''

    def __init__(self, item, repo=None):
        self.item = item
        self.repo = repo

    def object_id(self):
        '''Object id for bag name; use pid/ark if available; otherwise, use
        digwf control key (OCLC #)'''
        return self.item.pid or self.item.control_key

    def object_title(self):
        '''Object title for bag name: use title from MARC xml'''
        return self.item.marc.title()

    def bag_info(self):
        # look up source organization info by item's collection id
        source_info = CollectionSources.info_by_id(self.item.collection_id)
        return {
            'Source-Organization': source_info['organization'],
            'Organization-Address': source_info['address'],
            'External-Description': self.external_description()
            # more to be added later...
        }

    def external_description(self):
        source_obj = CollectionSources.info_by_id(self.item.collection_id)
        volume = self.item.volume
        if volume:
            volume = self.item.volume + ". "
        else:
            volume = ''

        if self.item.marc['245']['a']:
           field_245a = self.item.marc['245']['a'] + ": "
        else:
            field_245a = ''
        if self.item.marc['245']['b']:
           field_245b = self.item.marc['245']['b'] + " "
        else:
            field_245b = ''

        if self.item.marc['245']['c']:
           field_245c = self.item.marc['245']['c'] + " "
        else:
            field_245c = ''

        field_260 = self.item.marc['260'].get_subfields('a', 'a', 'b', 'c')
        field_sum = (' ').join(field_260)

        desc = field_245a + field_245b + field_245c + volume + field_sum
        return desc


    def descriptive_metadata(self):
        '''List of descriptive metadata files to be included in the bag.
        Currently only includes MARC XML.'''
        return [self.item.marc_path]

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

    def relationship_metadata_info(self):
        rel_info = {
            'DigWF Collection': {
                'id': self.item.collection_id,
                'name': str(self.item.collection_name)
            }
        }
        # if item has a pid, look up related objects in fedora
        if self.item.pid:
            vol = self.repo.get_object('emory:%s' % self.item.pid, type=Volume)
            if not vol.exists:
                print "volume %s doesn't exist or Fedora connection failed" % vol.pid

            if vol.exists:
                # parent book info
                if vol.book.exists:
                    # NOTE: using str to avoid unicode weirdness in yaml output
                    book_info = {'pid': str(vol.book.pid),
                                 'name': str(vol.book.label)}
                    # include ark if available
                    if vol.book.ark_uri:
                        book_info.update({
                            'ark_uri': vol.book.ark_uri,
                            'ark': vol.book.ark
                        })
                    rel_info['Fedora Book'] = book_info
                # collection
                if vol.book.collection.exists:
                    coll_info = {'pid': str(vol.book.collection.pid),
                                 'name': str(vol.book.collection.label)}
                    # include ark if available (but probably not available)
                    if vol.book.collection.ark_uri:
                        coll_info.update({
                            'ark_uri': vol.book.collection.ark_uri,
                            'ark': vol.book.collection.ark
                        })
                    rel_info['Fedora Collection'] = coll_info

        return rel_info

    def mets_metadata_info(self):
        #list all files in the bag in mets format and for struct map for it
        mets = Mets()
        mets.create_dmd()
        data_files = sorted(self.data_files())
        tif_idx = 0
        pos_idx = 0
        txt_idx = 0
        all_idx = 0
        for idx, file in enumerate(data_files):
            file_name = os.path.split(file)
            filename, file_extension = os.path.splitext(file_name[1])
            split_str = filename.split("_")
            split_char = re.split('(\d+)',split_str[-1])
            if file_extension == ".TIF" or file_extension == ".tif":
                tif_idx += 1
                tif_file = METSFile(id="TIF%s" % str(tif_idx).zfill(4), mimetype="image/tiff", loctype="URL", href=file_name[1])
                mets.tiffs.append(tif_file)
            if file_extension == ".jpg":
                jpg_file = METSFile(id="JPG%s" % split_str[-1], mimetype="image/jpg", loctype="URL", href=file_name[1])
                mets.jpgs.append(jpg_file)
            if file_extension == ".jp2s":
                jp2_file = METSFile(id="JP2%s" % split_str[-1], mimetype="image/jp2", loctype="URL", href=file_name[1])
                mets.jp2s.append(jp2_file)
            if file_extension == ".txt":
                txt_idx += 1
                txt_file = METSFile(id="TXT%s" % str(txt_idx).zfill(4), mimetype="plain/text", loctype="URL", href=file_name[1])
                mets.txts.append(txt_file)
            if file_extension == ".pdf":
                pdf_file = METSFile(id="PDF%s" % split_str[-1], mimetype="application/pdf", loctype="URL", href=file_name[1])
                mets.pdfs.append(pdf_file)
            if file_extension == ".pos":
                pos_idx +=1
                pos_file = METSFile(id="POS%s" % str(pos_idx).zfill(4), mimetype="text/plain", loctype="URL", href=file_name[1])
                mets.pos.append(pos_file)
            if file_extension == ".xml":
                afr_file = METSFile(id="AFR%s" % split_str[-1], mimetype="text/xml", loctype="URL", href=file_name[1])
                mets.afrs.append(afr_file)
            
            if split_str[-1].isdigit():
                matching = [s for s in data_files if filename in s]
                if len(matching) == 3 and file_extension != '.pos' and file_extension != '.txt':
                    all_idx += 1
                    pid_struct = METSMap(order=all_idx, page_type='page', tif="TIF"+str(all_idx).zfill(4), pos="POS"+str(all_idx).zfill(4))
                    pid_struct.txt = "TXT"+str(all_idx).zfill(4)
                    mets.structmap.append(pid_struct)
                else:
                    print 'Error! Some files are missing in the volume %s' % matching

        root = etree.fromstring(mets.serialize(pretty=True))
        root.attrib['{http://www.w3.org/2001/XMLSchema-instance}schemaLocation']= "http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/mets.xsd"
        return etree.tostring(root, pretty_print=True)

    def add_relationship_metadata(self, bagdir):
        # override default implementation, since we don't just want to
        # copy existig content in, but need to output content
        rel_dir = super(LsdiBaggee, self).add_relationship_metadata(bagdir)
        rel_file = os.path.join(rel_dir, 'machine-relationship.txt')
        with open(rel_file, 'w') as outfile:
            yaml.dump(self.relationship_metadata_info(), outfile,
                      default_flow_style=False)
        rel_file2 = os.path.join(rel_dir, 'human-relationship.txt')
        with open(rel_file2, 'w') as f1:
            f1.write("This directory contains information regarding external object relationships.\n"
                     "The provided metadata includes identifiers and information about parent collection"
                     " information from Fedora and other volumes in a multi-volume set.")

    def add_descriptive_metadata(self, bagdir):
        # override default implementation, since we don't just want to
        # copy existig content in, but need to output content
        rel_dir = super(LsdiBaggee, self).add_descriptive_metadata(bagdir)
        rel_file = os.path.join(rel_dir, 'human-descriptive.txt')
        with open(rel_file, 'w') as f1:
            f1.write("TThis folder contains Descriptive metadata. Machine readable versions include available MARCXML (see _MRC.xml) and may also include additional Dublin Core records (see _DC.xml).\n\n"
                     "The MARCXML record was generated from the original Sirsi Unicorn (legacy system) catalog record and may have been modified outside the catalog as part of the repository ingest workflow.\n\n"
                     "Dublin Core records are derived from the MARCXML records via XSLT.")
    
    def add_identity_metadata(self, bagdir):
        # override default implementation, since we don't just want to
        # copy existig content in, but need to output content
        rel_dir = super(LsdiBaggee, self).add_identity_metadata(bagdir)
        rel_file = os.path.join(rel_dir, 'human-identifier.txt')
        with open(rel_file, 'w') as f1:
            f1.write("Bag includes all/any available identifiers such as:\n\n"
                     "PID (Persistent identifier or PURL from pid.emory.edu)\n"
                     "ARK (ARK identifier from pid.emory.edu)\n"
                     "include both versions of ARK\n"
                     "OCLC # (first matching from MARC 035$a('OCoLC'))\n"
                     "LOCAL CALL # (MARC 786$o if exists)\n"
                     "Digitization Workflow Application ID number\n"
                     "BARCODE # (from Workflow App Items Table)")
    


    def add_content_metadata(self, bagdir):
        # override default implementation, since we don't just want to
        # copy existig content in, but need to output content
        rel_dir = super(LsdiBaggee, self).add_content_metadata(bagdir)
        rel_file = os.path.join(rel_dir, '%s.mets.xml' % self.item.pid)
        print self.mets_metadata_info()
        with open(rel_file, 'w') as outfile:
            outfile.write(self.mets_metadata_info())
        rel_file2 = os.path.join(rel_dir, 'human-content.txt')
        with open(rel_file2, 'w') as f1:
            f1.write("This folder contains relevant information describing the content model "
                     "(i.e. a description of how the digitized book should be put together structurally,"
                     " how the files map to the real object, etc.). The machine readable file is encoded as METS.")

    def add_technical_metadata(self, bagdir):
        # override default implementation, since we don't just want to
        # copy existig content in, but need to output content
        rel_dir = super(LsdiBaggee, self).add_technical_metadata(bagdir)
        rel_file = os.path.join(rel_dir, 'human-technical.txt')
        with open(rel_file, 'w') as f1:
            f1.write("This directory should contain technical metadata"
                     "(relevant technical/characterization files for the object,"
                     "such as FITS, MediaInfo, MIX, etc).\n\n" 
                     "POS files in the bag are ascii text and contain Windows-style"
                     " (CR/LF) line feeds that may need to be converted prior to any digital repository"
                     " ingest.\n\nWe identified no other viable technical metadata"
                     " for the existing source data files and will not attempt to generate"
                     " new characterization data during the initial LSDI Bags generation.")

    def add_audit_metadata(self, bagdir):
        # override default implementation, since we don't just want to
        # copy existig content in, but need to output content
        rel_dir = super(LsdiBaggee, self).add_audit_metadata(bagdir)
        rel_file = os.path.join(rel_dir, 'human-audit.txt')
        with open(rel_file, 'w') as f1:
            f1.write("This directory contains metadata for audits/events "
                     "tied to the object (e.g. PREMIS events; event logs; etc.)\n" 
                     "Data sources: includes all available DigWF workflow data (locally developed database).")

    
    def add_rights_metadata(self, bagdir):
        # override default implementation, since we don't just want to
        # copy existig content in, but need to output content
        rel_dir = super(LsdiBaggee, self).add_rights_metadata(bagdir)
        rel_file = os.path.join(rel_dir, 'human-rights.txt')
        with open(rel_file, 'w') as f1:
            f1.write("Rights statements for this volume are available in the descriptive metadata source (MARCXML) in Notes fields: 583; 590\n\n"
                     "583 values are based on 008. The following subfields are included:\n"
                     "$x public domain based on staff manually checking the place and date of publication in physical volume.\n"
                     "$a indicates if we digitized the volume\n"
                     "$c indicates the date we digitized the volume\n"
                     "$3 Volume/enumeration note\n"
                     "$2\n"
                     "$5 Institution code for the volume digitized\n\n"
                     "590 values are a statement/note.\n\n"
                     "Additional rights-related workflow instances exist in the DigWF workflow "
                     "item_states table (where workflow_step_id=24, indicating that the Public Domain check passed)."
                     "  'Place and date of publication as recorded in the MARC record was verified"
                     " to be consistent with the Public Domain by the Digitization Workflow Application at [timestamp]'."
                     " Please refer to the /metadata/audit directory for more detail.")



    # def add_rights_metadata(self, bagdir):
    #     # override default implementation, since we don't just want to
    #     # copy existig content in, but need to output content
    #     rel_dir = super(LsdiBaggee, self).add_rights_metadata(bagdir)
    #     rel_file = os.path.join(rel_dir, 'human-rights.txt')
    #     with open(rel_file, 'w') as f1:
    #         for f in self.item.marc['583'].get_subfields('x', 'a', 'c', '2','3', '5'):
    #             f1.write(f + "\n")
    #         for f in self.item.marc['590'].get_subfields('a'):
    #             f1.write(f + "\n")
            



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

        parser.add_argument('-f', '--file', metavar='FILE',
                            help='Digitization Workflow File With Item IDs')

        parser.add_argument("-v", "--verbose",
                  action="store_true", dest="verbose",
                  help="print status messages to stdout and traceback")

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

        # if requested, generate an empty config file that can be filled in
        # and then quit
        if self.options.gen_config:
            print 'Generating an empty config file'
            self.generate_configfile()
            exit()

        if self.options.verbose:
            sys.tracebacklimit = 5
            

        if self.options.file:
            self.options.item_ids = self.load_ids_from_file()

        if not self.options.item_ids:
            print 'Please specify items to process'
            parser.print_help()
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
        repo = Repository(self.options.fedora_url)

        for item_id in self.options.item_ids:
            try:
                result = digwf_api.get_items(item_id=item_id)
            except requests.exceptions.HTTPError as err:
                print 'Domokun Connection Error! Unable to query DigWF REST API for %s: %s' % (item_id, err)
                continue

            try:
                r = requests.head(self.options.fedora_url)
                # prints the int of the status code.
            except requests.ConnectionError:
                print 'Fedora Connection Error! Unable to query Fedora REST API'
                continue


            if result.count == 1:
                item = result.items[0]
                print 'Found item %s (pid %s, control key %s, marc %s)' % \
                    (item_id, item.pid or '-', item.control_key,
                     item.marc_path)
                try:
                    repo.get_object(pid=item.pid)
                except requests.exceptions.HTTPError as err:
                    print 'Fedora Connection Error! Unable to query Fedora REST API for %s: %s' % (item.pid, err)
                    continue


            elif result.count == 0:
                print 'No item found for this item id %s' % item_id
                continue
            else:
                # shouldn't get more than one match when looking up by
                # item id, but just in case
                print 'Error! DigWF returned %d matches for this item id %s' % \
                    (result.count, item_id)

                continue

            # returns a bagit bag object.
            newbag = LsdiBaggee(item, repo).create_bag(self.options.output)

            # generate source organization summary for this bag
            # self.load_source_summary(newbag)

            print 'Bag created at %s' % newbag

    # config file section headings
    digwf_cfg = 'Digitization Workflow'
    filepaths_cfg = 'File Paths'
    fedora_cfg = 'Fedora'

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
        # fedora
        config.add_section(self.fedora_cfg)
        config.set(self.fedora_cfg, 'url', 'http://fedora.server:8080/fedora/')
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

        # - fedora url is required
        try:
            self.options.fedora_url = cfg.get(self.fedora_cfg, 'url')
        except (NoOptionError, NoSectionError):
            pass

        if not getattr(self.options, 'fedora_url', None):
            print 'Error: Fedora URL not configured'
            exit()

        # output could be specified via command line or config file;
        # command line flag overrules config
        if cfg.has_option(self.filepaths_cfg, 'output') and \
           not self.options.output:
            self.options.output = cfg.get(self.filepaths_cfg, 'output')

    def load_ids_from_file(self):
        try:
            with open(self.options.file) as f:
                return [x.strip('\n') for x in f.readlines()]
        except Exception:
            print "Unable to load specified id file"








