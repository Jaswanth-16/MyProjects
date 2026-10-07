"""SDK boundary tests run when the optional Azure dependencies are installed."""

from types import SimpleNamespace
import unittest
from unittest.mock import Mock

try:
    import function_app
    from azure.core import MatchConditions
    from azure.core.exceptions import ResourceModifiedError
except ImportError:
    function_app = None

from transitpulse.cloud import ConcurrentPublishError


@unittest.skipIf(function_app is None, 'optional Azure SDK is not installed')
class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.container = Mock()
        self.blob = self.container.get_blob_client.return_value
        self.store = function_app.AzureBlobStore(self.container)

    def test_read_is_bound_to_the_inspected_etag(self):
        self.blob.get_blob_properties.return_value = SimpleNamespace(size=3, etag='v1')
        self.blob.download_blob.return_value.readall.return_value = b'abc'
        self.assertEqual(self.store.read('input', 3), (b'abc', 'v1'))
        self.blob.download_blob.assert_called_once_with(etag='v1', match_condition=MatchConditions.IfNotModified)

    def test_oversized_input_is_rejected_before_download(self):
        self.blob.get_blob_properties.return_value = SimpleNamespace(size=4, etag='v1')
        with self.assertRaises(ValueError):
            self.store.read('input', 3)
        self.blob.download_blob.assert_not_called()

    def test_snapshot_publish_sends_etag_precondition(self):
        self.store.compare_and_swap('state/HEAD.json', b'{}', 'v1')
        kwargs = self.blob.upload_blob.call_args.kwargs
        self.assertEqual(kwargs['etag'], 'v1')
        self.assertEqual(kwargs['match_condition'], MatchConditions.IfNotModified)

    def test_provider_precondition_failure_becomes_retryable_conflict(self):
        self.blob.upload_blob.side_effect = ResourceModifiedError('precondition failed')
        with self.assertRaises(ConcurrentPublishError):
            self.store.compare_and_swap('state/HEAD.json', b'{}', 'v1')

    def test_function_is_discoverable_with_authenticated_post_route(self):
        functions = function_app.app.get_functions()
        self.assertEqual(len(functions), 1)
        bindings = functions[0].get_bindings_dict()['bindings']
        trigger = next(b for b in bindings if b['type'] == 'httpTrigger')
        self.assertEqual(trigger['route'], 'process')
        self.assertEqual(trigger['authLevel'], function_app.func.AuthLevel.FUNCTION)


if __name__ == '__main__':
    unittest.main()
