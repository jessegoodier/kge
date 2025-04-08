import unittest
from unittest.mock import patch, MagicMock
from kge.cli.main import get_events_for_pod, get_all_events, get_k8s_client

class TestCLI(unittest.TestCase):
    @patch('kge.cli.main.get_k8s_client')
    def test_get_events_for_pod(self, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = mock_v1
        
        # Mock the list_namespaced_event response
        mock_event = MagicMock()
        mock_event.type = 'Normal'
        mock_event.last_timestamp = '2023-01-01T00:00:00Z'
        mock_event.reason = 'Created'
        mock_event.message = 'Test message'
        mock_v1.list_namespaced_event.return_value.items = [mock_event]
        
        result = get_events_for_pod('default', 'test-pod')
        
        # Verify the field selector
        mock_v1.list_namespaced_event.assert_called_once()
        call_args = mock_v1.list_namespaced_event.call_args[1]
        self.assertEqual(call_args['field_selector'], 'involvedObject.name=test-pod')
        
        # Verify the output format
        self.assertIn('Normal', result)
        self.assertIn('Created', result)
        self.assertIn('Test message', result)

    @patch('kge.cli.main.get_k8s_client')
    def test_get_all_events(self, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = mock_v1
        
        # Mock the list_namespaced_event response
        mock_event = MagicMock()
        mock_event.type = 'Normal'
        mock_event.last_timestamp = '2023-01-01T00:00:00Z'
        mock_event.reason = 'Created'
        mock_event.message = 'Test message'
        mock_v1.list_namespaced_event.return_value.items = [mock_event]
        
        result = get_all_events('default')
        
        # Verify the field selector is None for all events
        mock_v1.list_namespaced_event.assert_called_once()
        call_args = mock_v1.list_namespaced_event.call_args[1]
        self.assertIsNone(call_args.get('field_selector'))
        
        # Verify the output format
        self.assertIn('Normal', result)
        self.assertIn('Created', result)
        self.assertIn('Test message', result)

    @patch('kge.cli.main.get_k8s_client')
    def test_get_events_for_pod_non_normal(self, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = mock_v1
        
        # Mock the list_namespaced_event response
        mock_event = MagicMock()
        mock_event.type = 'Warning'
        mock_event.last_timestamp = '2023-01-01T00:00:00Z'
        mock_event.reason = 'Failed'
        mock_event.message = 'Test message'
        mock_v1.list_namespaced_event.return_value.items = [mock_event]
        
        result = get_events_for_pod('default', 'test-pod', non_normal=True)
        
        # Verify the field selector includes non-normal filter
        mock_v1.list_namespaced_event.assert_called_once()
        call_args = mock_v1.list_namespaced_event.call_args[1]
        self.assertIn('type!=Normal', call_args['field_selector'])
        
        # Verify the output format
        self.assertIn('Warning', result)
        self.assertIn('Failed', result)
        self.assertIn('Test message', result)

    @patch('kge.cli.main.get_k8s_client')
    def test_get_all_events_non_normal(self, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = mock_v1
        
        # Mock the list_namespaced_event response
        mock_event = MagicMock()
        mock_event.type = 'Warning'
        mock_event.last_timestamp = '2023-01-01T00:00:00Z'
        mock_event.reason = 'Failed'
        mock_event.message = 'Test message'
        mock_v1.list_namespaced_event.return_value.items = [mock_event]
        
        result = get_all_events('default', non_normal=True)
        
        # Verify the field selector includes non-normal filter
        mock_v1.list_namespaced_event.assert_called_once()
        call_args = mock_v1.list_namespaced_event.call_args[1]
        self.assertEqual(call_args['field_selector'], 'type!=Normal')
        
        # Verify the output format
        self.assertIn('Warning', result)
        self.assertIn('Failed', result)
        self.assertIn('Test message', result)

    def test_get_k8s_client(self):
        with patch('kge.cli.main.config.load_kube_config') as mock_load_config:
            with patch('kge.cli.main.client.CoreV1Api') as mock_api:
                mock_load_config.return_value = None
                mock_api.return_value = 'mock_client'
                
                result = get_k8s_client()
                
                mock_load_config.assert_called_once()
                mock_api.assert_called_once()
                self.assertEqual(result, 'mock_client')

    @patch('kge.cli.main.get_k8s_client')
    def test_get_events_for_pod_with_namespace(self, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = mock_v1
        
        # Mock the list_namespaced_event response
        mock_event = MagicMock()
        mock_event.type = 'Normal'
        mock_event.last_timestamp = '2023-01-01T00:00:00Z'
        mock_event.reason = 'Created'
        mock_event.message = 'Test message'
        mock_v1.list_namespaced_event.return_value.items = [mock_event]
        
        result = get_events_for_pod('custom-namespace', 'test-pod')
        
        # Verify the namespace is passed correctly
        mock_v1.list_namespaced_event.assert_called_once()
        call_args = mock_v1.list_namespaced_event.call_args
        self.assertEqual(call_args[0][0], 'custom-namespace')  # First positional arg is namespace
        self.assertEqual(call_args[1]['field_selector'], 'involvedObject.name=test-pod')

    @patch('kge.cli.main.get_k8s_client')
    def test_get_all_events_with_namespace(self, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = mock_v1
        
        # Mock the list_namespaced_event response
        mock_event = MagicMock()
        mock_event.type = 'Normal'
        mock_event.last_timestamp = '2023-01-01T00:00:00Z'
        mock_event.reason = 'Created'
        mock_event.message = 'Test message'
        mock_v1.list_namespaced_event.return_value.items = [mock_event]
        
        result = get_all_events('custom-namespace')
        
        # Verify the namespace is passed correctly
        mock_v1.list_namespaced_event.assert_called_once()
        call_args = mock_v1.list_namespaced_event.call_args
        self.assertEqual(call_args[0][0], 'custom-namespace')  # First positional arg is namespace
        self.assertIsNone(call_args[1].get('field_selector'))

    @patch('kge.cli.main.get_k8s_client')
    def test_get_events_for_pod_with_namespace_and_exceptions(self, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = mock_v1
        
        # Mock the list_namespaced_event response
        mock_event = MagicMock()
        mock_event.type = 'Warning'
        mock_event.last_timestamp = '2023-01-01T00:00:00Z'
        mock_event.reason = 'Failed'
        mock_event.message = 'Test message'
        mock_v1.list_namespaced_event.return_value.items = [mock_event]
        
        result = get_events_for_pod('custom-namespace', 'test-pod', non_normal=True)
        
        # Verify both namespace and exceptions filter are passed correctly
        mock_v1.list_namespaced_event.assert_called_once()
        call_args = mock_v1.list_namespaced_event.call_args
        self.assertEqual(call_args[0][0], 'custom-namespace')  # First positional arg is namespace
        self.assertIn('type!=Normal', call_args[1]['field_selector'])
        self.assertIn('involvedObject.name=test-pod', call_args[1]['field_selector'])

    @patch('kge.cli.main.get_k8s_client')
    def test_get_all_events_with_namespace_and_exceptions(self, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = mock_v1
        
        # Mock the list_namespaced_event response
        mock_event = MagicMock()
        mock_event.type = 'Warning'
        mock_event.last_timestamp = '2023-01-01T00:00:00Z'
        mock_event.reason = 'Failed'
        mock_event.message = 'Test message'
        mock_v1.list_namespaced_event.return_value.items = [mock_event]
        
        result = get_all_events('custom-namespace', non_normal=True)
        
        # Verify both namespace and exceptions filter are passed correctly
        mock_v1.list_namespaced_event.assert_called_once()
        call_args = mock_v1.list_namespaced_event.call_args
        self.assertEqual(call_args[0][0], 'custom-namespace')  # First positional arg is namespace
        self.assertEqual(call_args[1]['field_selector'], 'type!=Normal')

if __name__ == '__main__':
    unittest.main() 