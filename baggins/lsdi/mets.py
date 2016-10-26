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
    ROOT_NAMESPACES = {
        'xlink' : "http://www.w3.org/1999/xlink",
        'mets': 'http://www.loc.gov/METS/'
    }

    id = StringField('@ID')
    admid = StringField('@ADMID')
    mimetype = StringField('@MIMETYPE')
    loctype = StringField('mets:FLocat/@LOCTYPE')
    href = StringField('mets:FLocat/@xlink:href')

class METSMap(xmlmap.XmlObject):
    ROOT_NAME = 'div'
    ROOT_NAMESPACES = {
        'xlink' : "http://www.w3.org/1999/xlink",
        'mets': 'http://www.loc.gov/METS/'
    }

    dmdid = StringField('@DMDID')
    label = StringField('@LABEL')
    map_type = StringField('@TYPE')
    order = StringField('mets:div/@ORDER')
    page_type = StringField('mets:div/@TYPE')
    fileid = StringField('mets:div/fptr/@FILEID')

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
    XSD_SCHEMA = 'http://www.loc.gov/standards/mets/version191/mets.xsd'
    ROOT_NAME = 'mets'
    ROOT_NAMESPACES = {'mets': 'http://www.loc.gov/METS/'}

    #x = NodeListField('mets:fileSec/mets:fileGrp', METSFile)
    tiffs = NodeListField('mets:fileSec/mets:fileGrp[@ID="TIFF"]/mets:file', METSFile)
    txts = NodeListField('mets:fileSec/mets:fileGrp[@ID="TXT"]/mets:file', METSFile)
    jpgs = NodeListField('mets:fileSec/mets:fileGrp[@ID="JPEG"]/mets:file', METSFile)
    jp2s = NodeListField('mets:fileSec/mets:fileGrp[@ID="JP2000"]/mets:file', METSFile)
    altos = NodeListField('mets:fileSec/mets:fileGrp[@ID="ALTO"]/mets:file', METSFile)
    pdfs = NodeListField('mets:fileSec/mets:fileGrp[@ID="PDF"]/mets:file', METSFile)
    structmap = NodeListField('mets:structMap[@TYPE="physical"]/mets:div', METSMap)
    techmd = NodeListField('mets:amdSec/mets:techMD[starts-with(@ID, "AMD_TECHMD_TIF") or starts-with(@ID, "AMD_TECHMD_JPG") or starts-with(@ID, "AMD_TECHMD_JP2")]', METStechMD)

