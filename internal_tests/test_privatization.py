import unittest
import time

from openprocurement_client.resources.lots import LotsClient
from openprocurement_client.resources.assets import AssetsClient


from openregistry.lots.loki.tests.json_data import (
    test_loki_lot_data,
    auction_english_data,
    auction_second_english_data,
)

from openregistry.assets.bounce.tests.json_data import (
    test_asset_bounce_data
)

# Config for an clients
config = {
    "url": "http://127.0.0.1:6543",
    "version": 2.5,
    "token": "broker",
}

test_loki_lot_data['mode'] = 'test'
test_asset_bounce_data['mode'] = 'test'

# Asset bounce data
test_asset_bounce_data['assetHolder'] = {
    'name': 'Just assetHolder',
    'identifier': {
        'scheme': 'UA-EDR',
        'legalName': 'Just a legal name',
        'id': '11111-4',
        'uri': 'https://127.0.0.1:6543'
    }
}

test_lot_data = {
    'data': test_loki_lot_data
}

test_asset_data = {
    'data': test_asset_bounce_data
}


class LotStatusFlowTest(unittest.TestCase):
    def setUp(self):
        self.lots_client = LotsClient(
            key=config['token'],
            host_url=config['url'],
            api_version=config['version']
        )
        self.assets_client = AssetsClient(
            key=config['token'],
            host_url=config['url'],
            api_version=config['version']
        )

    def change_status(self, client, _id, status, token):
        test_data = client.patch_resource_item(
            _id, {'data': {'status': status}}, token
        )
        self.assertEqual(test_data.data.status, status)

    def test_lots_assets_flow(self):
        # Create Asset
        asset = self.assets_client.create_resource_item(test_asset_data)
        self.assertEqual(asset.data.status, 'draft')

        test_lot_data['data']['assets'] = [asset.data.id]
        lot = self.lots_client.create_resource_item(test_lot_data)
        self.assertEqual(lot.data.status, 'draft')

        test_auctions = lot.data.auctions
        test_auction_one = test_auctions[0]
        test_auction_two = test_auctions[1]

        self.lots_client.patch_resource_item_subitem(
            resource_item_id=lot.data.id,
            patch_data={'data': auction_english_data},
            subitem_name='auctions',
            subitem_id=test_auction_one.id,
            access_token=lot.access.token
        )

        self.lots_client.patch_resource_item_subitem(
            resource_item_id=lot.data.id,
            patch_data={'data': auction_second_english_data},
            subitem_name='auctions',
            subitem_id=test_auction_two.id,
            access_token=lot.access.token
        )

        self.change_status(self.assets_client, asset.data.id, 'pending', asset.access.token)

        self.change_status(self.lots_client, lot.data.id, 'composing', lot.access.token)

        self.change_status(self.lots_client, lot.data.id, 'verification', lot.access.token)

        for _ in range(50):
            print 'Waiting for an concierge changes'
            test_lot = self.lots_client.get_lot(lot.data.id)
            if test_lot.data.status == 'pending':
                break
            time.sleep(15)


if __name__ == '__main__':
    unittest.main()
