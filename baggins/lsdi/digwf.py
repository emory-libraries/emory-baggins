'''
Client and :class:`~eulxml.xmlmap.XmlObject` classes to interact with
the Digitization Workflow API in order to retrieve information about
Large Scale Digitization Initiative (LSDI) content.

.. Note::

    DigWF is a legacy application (no longer in use) that contains
    data about existing Emory Readux volumes.  The DigWF API was used
    to import cover images and selected page images.
'''

from cached_property import cached_property
from eulxml import xmlmap
import requests
from pymarc import MARCReader
import pymarc


class Client(object):
    """A simple client to query the Digitization Workflow REST(ish)
    API for information about files associated with LSDI/DigWF items.

    :param baseurl: base url of the api for the DigWF REST service., e.g.
                    ``http://my.domain.com/digwf_api/``
    """

    def __init__(self, url):
        self.base_url = url.rstrip('/')

    def get_items(self, **kwargs):
        '''Query the DigWF API getItems method.  If no search terms
        are specified, getItems returns any items that are in the
        **Ready for Repository** state.  Any keyword arguments will be
        passed to getItems as query arguments.  Currently supports:

          * control_key (e.g., ocm or ocn number) - may match more
            than one item
          * item_id - the item id for the record in the DigWF
          * pid - the noid portion of the pid/ARK for the item

        :returns: :class:`Items`
        '''
        url = '%s/getItems' % self.base_url
        r = requests.get(url, params=kwargs)
        if r.status_code == requests.codes.ok:
            return xmlmap.load_xmlobject_from_string(r.content, Items)
        else:
            # raise the error so it can be caught downstream
            r.raise_for_status()


class Item(xmlmap.XmlObject):
    ''':class:`~eulxml.xmlmap.XmlObject` to read Item information returned
    by the DigWF API.

    (Not all fields provided by DigWF are mapped here; only those
    currently in use.)
    '''

    #: pid (noid portion of the ARK or Fedora pid)
    pid = xmlmap.StringField('@pid')
    #: item_id within the DigWF
    item_id = xmlmap.StringField('@id')
    #: control key (e.g., ocm or ocn number in euclid; unique per book,
    #: not per volume)
    control_key = xmlmap.StringField('@control_key')
    #: display image path
    display_image_path = xmlmap.StringField('display_images_path')
    #: display images count
    display_image_count = xmlmap.IntegerField('display_images_path/@count')
    #: path to OCR files (text & word position)
    ocr_file_path = xmlmap.StringField('ocr_files_path')
    #: ocr file count
    ocr_file_count = xmlmap.IntegerField('ocr_files_path/@count')

    #: path to PDF file
    pdf = xmlmap.StringField('pdf_file')
    #: path to ABBYY FineReader XML file
    ocr_file = xmlmap.StringField('ocr_file')
    #: path to marc xml file
    marc_path = xmlmap.StringField('marc_file')

    #: collection id
    collection_id = xmlmap.IntegerField('collection/@id')
    #: collection name
    collection_name = xmlmap.StringField('collection')

    # NOTE: these mappings are incomplete, and only include what was pused
    # for readux page ingest; we will likely need to add more mappings

    @cached_property
    def marc(self):
        # use pymarc to read the marcxml to make fields available
        with open(self.marc_path, 'r') as marcdata:
            return pymarc.parse_xml_to_array(marcdata)[0]


class Items(xmlmap.XmlObject):
    ''':class:`~eulxml.xmlmap.XmlObject` for the response returned by getItems.
    Has a count of the number of items found, and a list of :class:`Item`
    objects with details about each item.'''
    _count = xmlmap.IntegerField('@count')
    'number of items in the result'
    items = xmlmap.NodeListField('item', Item)
    'List of items as instances of :class:`~readux.books.digwf.Item`'

    @property
    def count(self):
        # in an empty result set, count is not set; return 0 to simplify
        # code logic where results are checked
        return self._count or 0

