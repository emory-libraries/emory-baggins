'''
Client and :class:`~eulxml.xmlmap.XmlObject` classes to interact with
the Digitization Workflow API in order to retrieve information about
Large Scale Digitization Initiative (LSDI) content.

.. Note::

    DigWF is a legacy application (no longer in use) that contains
    data about existing Emory Readux volumes.  The DigWF API was used
    to import cover images and selected page images.
'''

from eulxml import xmlmap
from eulxml.xmlmap.core import StringField, IntegerField, NodeListField




# METS XML
class METSFile(xmlmap.XmlObject):
    ROOT_NAME = 'file'
    ROOT_NS = "http://www.loc.gov/METS/"
    ROOT_NAMESPACES = {
        'mets': ROOT_NS,
        'xlink' : "http://www.w3.org/1999/xlink",
    }

    id = StringField('@ID')
    admid = StringField('@ADMID')
    mimetype = StringField('@MIMETYPE')
    loctype = StringField('mets:FLocat/@LOCTYPE')
    href = StringField('mets:FLocat/@xlink:href')

class METSMap(xmlmap.XmlObject):
    ROOT_NAME = 'div'
    ROOT_NS = "http://www.loc.gov/METS/"
    ROOT_NAMESPACES = {
        'mets': ROOT_NS,
        'xlink' : "http://www.w3.org/1999/xlink",
    }

    order = StringField('@ORDER')
    page_type = StringField('@TYPE')
    tif = StringField('mets:fptr[1]/@FILEID')
    pos = StringField('mets:fptr[2]/@FILEID')
    txt = StringField('mets:fptr[3]/@FILEID')

#TODO make schemas and namespaces local
class METStechMD(xmlmap.XmlObject):
    ROOT_NAME = 'techMD'
    ROOT_NAMESPACES = {
        'mix': 'http://www.loc.gov/mix/v20',
        'mets': 'http://www.loc.gov/METS/'
    }

    id = StringField('@ID')
    href = StringField('mets:mdWrap/mets:xmlData/mix:mix/mix:BasicDigitalObjectInformation/mix:ObjectIdentifier/mix:objectIdentifierValue')
    size = IntegerField('mets:mdWrap/mets:xmlData/mix:mix/mix:BasicDigitalObjectInformation/mix:fileSize')
    mimetype = StringField('mets:mdWrap/mets:xmlData/mix:mix/mix:BasicDigitalObjectInformation/mix:FormatDesignation/mix:formatName')
    checksum = StringField('mets:mdWrap/mets:xmlData/mix:mix/mix:BasicDigitalObjectInformation/mix:Fixity/mix:messageDigest')

class Mets(xmlmap.XmlObject):
    # XSD_SCHEMA = "http://www.loc.gov/standards/mets/mets.xsd"
    # xmlschema = xmlmap.loadSchema(XSD_SCHEMA)
    ROOT_NAME = 'mets'
    ROOT_NS = "http://www.loc.gov/METS/"
    XSD_SCHEMA = "http://www.loc.gov/standards/mets/mets.xsd"
    xmlschema = xmlmap.loadSchema(XSD_SCHEMA)
    ROOT_NAMESPACES = {
        'mets': ROOT_NS,
        'xlink' : "http://www.w3.org/1999/xlink",
        'xsi': "http://www.w3.org/2001/XMLSchema-instance",
        'dc': "http://purl.org/dc/elements/1.1/",
        'premis' : "http://purl.org/dc/elements/1.1/premis",
        'mix' : "http://purl.org/dc/elements/1.1/mix",

    }

    dmd = xmlmap.NodeField('mets:dmdSec[@ID="DMD1"]',"self")
    tiffs = NodeListField('mets:fileSec/mets:fileGrp[@ID="TIFF"]/mets:file', METSFile)
    txts = NodeListField('mets:fileSec/mets:fileGrp[@ID="TXT"]/mets:file', METSFile)
    jpgs = NodeListField('mets:fileSec/mets:fileGrp[@ID="JPEG"]/mets:file', METSFile)
    jp2s = NodeListField('mets:fileSec/mets:fileGrp[@ID="JP2000"]/mets:file', METSFile)
    pos = NodeListField('mets:fileSec/mets:fileGrp[@ID="ALTO"]/mets:file', METSFile)
    pdfs = NodeListField('mets:fileSec/mets:fileGrp[@ID="PDF"]/mets:file', METSFile)
    afrs = NodeListField('mets:fileSec/mets:fileGrp[@ID="AFR"]/mets:file', METSFile)
    structmap = NodeListField('mets:structMap[@TYPE="physical"]/mets:div[@DMDID="DMD1"][@LABEL=""][@TYPE="volume"]/mets:div', METSMap)
    techmd = NodeListField('mets:amdSec/mets:techMD[starts-with(@ID, "AMD_TECHMD_TIF") or starts-with(@ID, "AMD_TECHMD_JPG") or starts-with(@ID, "AMD_TECHMD_JP2")]', METStechMD)

