import csv
import os

from baggins import PACKAGE_DIR


# some lsdi bagging content needs to reference fixture content
# that will be provided
FIXTURE_DIR = os.path.join(PACKAGE_DIR, 'lsdi', 'content')

FIXTURES = {
    # tab-separated lookup for collection source org info
    'collection-source': os.path.join(FIXTURE_DIR, 'collection_sourceorg.tsv')
}


class CollectionSources(object):

    info = {}

    unknown = {'organization': 'undetermined', 'address': 'not known'}

    @classmethod
    def load_info(cls):
        # initialize lookup info dictionary from TSV file first time only
        if not cls.info:
            with open(FIXTURES['collection-source'], 'r') as inputfile:
                reader = csv.DictReader(inputfile, dialect='excel', delimiter='\t')
                for row in reader:
                    cls.info[int(row['collection id'])] = {
                        'name': row['collection name'],
                        'organization': row['source organization'],
                        'address': row['source organization address']
                    }

    @classmethod
    def info_by_id(cls, collection_id):
        # ensure lookup is int to int
        collection_id = int(collection_id)
        if not cls.info:
            cls.load_info()
        # return collction info if present for this id, otherwise unknown
        return cls.info.get(collection_id, cls.unknown)
