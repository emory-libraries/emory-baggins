from mock import patch

from baggins.lsdi.collections import CollectionSources


class TestCollectionSources:

    def test_load_info(self):

        CollectionSources.load_info()
        # check for a few expected values from the fixturre
        assert 1 in CollectionSources.info
        assert 19 in CollectionSources.info

        assert CollectionSources.info[1]['name'] == 'Methodism'
        assert CollectionSources.info[1]['organization'] == \
            'Pitts Theology Library'
        assert CollectionSources.info[1]['address'] == \
            "531 Dickey Drive, Suite 560 Atlanta, GA 30322"

        # csv should not be called once info is set
        with patch('baggins.lsdi.collections.csv') as mockcsv:
            CollectionSources.load_info()
            mockcsv.DictReader.assert_not_called()

    def test_collection_source_info(self):
        # known id
        info = CollectionSources.info_by_id(15)
        assert info['name'] == 'Emory Yearbooks'
        assert info['organization'] == \
            'Stuart A. Rose Manuscript, Archives and Rare Book Library'
        assert info['address'] == \
            '540 Asbury Circle, Atlanta, GA 30322'

        # unknown id should return unknown
        info = CollectionSources.info_by_id(356)
        assert info['organization'] == 'undetermined'
        assert info['address'] == 'not known'
