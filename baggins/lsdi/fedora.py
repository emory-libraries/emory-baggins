from eulfedora.models import DigitalObject, Relation
from eulfedora.rdfns import relsext
from cached_property import cached_property

# minimual book/volume fedora objects for looking up identifiers
# and relationships


class ArkDigitalObject(DigitalObject):
    # base class with ark lookup

    @cached_property
    def ark_uri(self):
        # fully resolvable ark
        for identifier in self.dc.content.identifier_list:
            if 'ark:/' in identifier:
                return str(identifier)

    @cached_property
    def ark(self):
        # just ark id, starting with ark:
        if self.ark_uri:
            return self.ark_uri[self.ark_uri.find('ark:/'):]


class Collection(ArkDigitalObject):
    pass


class Book(ArkDigitalObject):
    '''Mimimal digitized Book object.
    '''
    #: content model for books
    BOOK_CONTENT_MODEL = 'info:fedora/emory-control:ScannedBook-1.0'
    CONTENT_MODELS = [BOOK_CONTENT_MODEL]

    #: :class:`~readux.collection.models.Collection` this book belongs to,
    #: via fedora rels-ext isMemberOfcollection
    collection = Relation(relsext.isMemberOfCollection, type=Collection)


class Volume(ArkDigitalObject):
    '''Minimal object for ScannedVolume-1.0`.

    ScannedVolume-1.0 objects include an Abbyy FineReader OCR XML datastream
    with the OCR content for the entire volume.
    '''

    #: volume content model
    VOLUME_CONTENT_MODEL = 'info:fedora/emory-control:ScannedVolume-1.0'
    CONTENT_MODELS = [VOLUME_CONTENT_MODEL]

    #: :class:`Book` this volume is associated with, via isConstituentOf
    book = Relation(relsext.isConstituentOf, type=Book)
