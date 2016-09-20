import os
import requests
from mock import patch
from eulxml.xmlmap import load_xmlobject_from_file

from baggins import digwf


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')
print 'fixture dir = ', FIXTURE_DIR


class TestDigwfClient:

    item_response = os.path.join(FIXTURE_DIR, 'digwf_getitems_3031.xml')
    empty_response = os.path.join(FIXTURE_DIR, 'digwf_getitems_nomatch.xml')

    def test_init(self):
        api_url = 'http://my.domain.com/digwf_api'
        digwf_client = digwf.Client(api_url)
        assert digwf_client.base_url == api_url
        digwf_client = digwf.Client('%s/' % api_url)
        assert digwf_client.base_url == api_url

    def test_get_items(self):
        api_url = 'http://my.domain.com/digwf_api'
        digwf_client = digwf.Client(api_url)

        # valid result
        with open(self.item_response, 'r') as itemresult:
            itemresult_content = itemresult.read()

        with patch('baggins.digwf.requests') as mockrequests:
            item_id = 3031
            mockrequests.codes.ok = requests.codes.ok
            mockrequests.get.return_value.status_code = requests.codes.ok
            # simulate valid return with fixture data
            mockrequests.get.return_value.content = itemresult_content
            result = digwf_client.get_items(item_id=item_id)
            assert isinstance(result, digwf.Items)

            expected_url = '%s/getItems' % api_url
            mockrequests.get.assert_called_with(
                expected_url, params={'item_id': item_id})

    def test_items_xml(self):
        # basic inspection of sample result / xml mapping
        response = load_xmlobject_from_file(self.item_response, digwf.Items)
        assert response.count == 1
        assert len(response.items) == 1
        assert isinstance(response.items[0], digwf.Item)

        item = response.items[0]
        assert item.pid == '7svgb'
        assert item.item_id == '3031'
        assert item.control_key == 'ocm08951025'
        assert item.display_image_path == '/mnt/lsdi/diesel/lts_new/ocm08951025-3031/ocm08951025/Output'
        assert item.ocr_file_path == '/mnt/lsdi/diesel/lts_new/ocm08951025-3031/ocm08951025/Output'
        assert item.pdf == '/mnt/lsdi/diesel/lts_new/ocm08951025-3031/ocm08951025/Output/Output.pdf'

        response = load_xmlobject_from_file(self.empty_response, digwf.Items)
        assert response.count == 0



