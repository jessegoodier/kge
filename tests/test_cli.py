import unittest
from unittest.mock import patch, MagicMock
from kge.cli.main import (
    get_events_for_pod, 
    get_all_events, 
    get_k8s_client,
    get_k8s_apps_client,
    get_failed_replicasets,
    get_pods,
    get_current_namespace,
    list_pods_for_completion,
    CACHE_DURATION,
    pod_cache,
    replicaset_cache
)

class TestCLI(unittest.TestCase):
    def setUp(self):
        # Clear caches before each test
        pod_cache.clear()
        replicaset_cache.clear()

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

    def test_get_k8s_apps_client(self):
        with patch('kge.cli.main.config.load_kube_config') as mock_load_config:
            with patch('kge.cli.main.client.AppsV1Api') as mock_api:
                mock_load_config.return_value = None
                mock_api.return_value = 'mock_apps_client'
                
                result = get_k8s_apps_client()
                
                mock_load_config.assert_called_once()
                mock_api.assert_called_once()
                self.assertEqual(result, 'mock_apps_client')

    @patch('kge.cli.main.get_k8s_apps_client')
    def test_get_failed_replicasets(self, mock_get_apps_client):
        mock_v1 = MagicMock()
        mock_get_apps_client.return_value = mock_v1
        
        # Mock the list_namespaced_replica_set response
        mock_rs = MagicMock()
        mock_rs.metadata.name = 'test-rs'
        mock_condition = MagicMock()
        mock_condition.type = 'ReplicaFailure'
        mock_rs.status.conditions = [mock_condition]
        mock_v1.list_namespaced_replica_set.return_value.items = [mock_rs]
        
        result = get_failed_replicasets('default')
        
        # Verify the API call
        mock_v1.list_namespaced_replica_set.assert_called_once_with('default')
        
        # Verify the result
        self.assertEqual(result, ['test-rs'])

    @patch('kge.cli.main.get_k8s_client')
    def test_get_pods_with_caching(self, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = mock_v1
        
        # Mock the list_namespaced_pod response
        mock_pod = MagicMock()
        mock_pod.metadata.name = 'test-pod'
        mock_v1.list_namespaced_pod.return_value.items = [mock_pod]
        
        # First call should hit the API
        result1 = get_pods('default')
        mock_v1.list_namespaced_pod.assert_called_once()
        
        # Reset mock call count
        mock_v1.list_namespaced_pod.reset_mock()
        
        # Second call within cache duration should use cache
        result2 = get_pods('default')
        mock_v1.list_namespaced_pod.assert_not_called()
        
        # Verify results are the same
        self.assertEqual(result1, result2)
        self.assertEqual(result1, ['test-pod'])

    def test_get_current_namespace_with_caching(self):
        with patch('kge.cli.main.config.list_kube_config_contexts') as mock_list_contexts:
            # First call
            mock_list_contexts.return_value = [None, {'context': {'namespace': 'test-ns'}}]
            result1 = get_current_namespace()
            mock_list_contexts.assert_called_once()
            
            # Reset mock call count
            mock_list_contexts.reset_mock()
            
            # Second call should use cache
            result2 = get_current_namespace()
            mock_list_contexts.assert_not_called()
            
            # Verify results are the same
            self.assertEqual(result1, result2)
            self.assertEqual(result1, 'test-ns')

    @patch('kge.cli.main.get_pods')
    @patch('kge.cli.main.get_failed_replicasets')
    @patch('kge.cli.main.get_current_namespace')
    def test_list_pods_for_completion(self, mock_get_namespace, mock_get_failed_rs, mock_get_pods):
        mock_get_namespace.return_value = 'default'
        mock_get_pods.return_value = ['pod1', 'pod2']
        mock_get_failed_rs.return_value = ['rs1', 'rs2']
        
        with patch('kge.cli.main.sys.exit') as mock_exit:
            with patch('kge.cli.main.print') as mock_print:
                list_pods_for_completion()
                
                # Verify the output
                mock_print.assert_called_once_with('pod1 pod2 rs1 rs2')
                mock_exit.assert_called_once_with(0)

    @patch('kge.cli.main.get_k8s_apps_client')
    @patch('kge.cli.main.time.time')
    def test_get_failed_replicasets_with_caching(self, mock_time, mock_get_apps_client):
        mock_v1 = MagicMock()
        mock_get_apps_client.return_value = mock_v1
        mock_time.return_value = 0  # Set initial time
        
        # Mock the list_namespaced_replica_set response
        mock_rs = MagicMock()
        mock_rs.metadata.name = 'test-rs'
        mock_condition = MagicMock()
        mock_condition.type = 'ReplicaFailure'
        mock_rs.status.conditions = [mock_condition]
        mock_v1.list_namespaced_replica_set.return_value.items = [mock_rs]
        
        # First call should hit the API
        result1 = get_failed_replicasets('default')
        mock_v1.list_namespaced_replica_set.assert_called_once()
        
        # Reset mock call count
        mock_v1.list_namespaced_replica_set.reset_mock()
        
        # Second call within cache duration should use cache
        mock_time.return_value = CACHE_DURATION - 1  # Still within cache duration
        result2 = get_failed_replicasets('default')
        mock_v1.list_namespaced_replica_set.assert_not_called()
        
        # Verify results are the same
        self.assertEqual(result1, result2)
        self.assertEqual(result1, ['test-rs'])

    @patch('kge.cli.main.get_k8s_apps_client')
    @patch('kge.cli.main.time.time')
    def test_get_failed_replicasets_cache_expiry(self, mock_time, mock_get_apps_client):
        mock_v1 = MagicMock()
        mock_get_apps_client.return_value = mock_v1
        mock_time.return_value = 0  # Set initial time
        
        # Mock the list_namespaced_replica_set response
        mock_rs = MagicMock()
        mock_rs.metadata.name = 'test-rs'
        mock_condition = MagicMock()
        mock_condition.type = 'ReplicaFailure'
        mock_rs.status.conditions = [mock_condition]
        mock_v1.list_namespaced_replica_set.return_value.items = [mock_rs]
        
        # First call
        result1 = get_failed_replicasets('default')
        mock_v1.list_namespaced_replica_set.assert_called_once()
        
        # Reset mock call count
        mock_v1.list_namespaced_replica_set.reset_mock()
        
        # Simulate cache expiry by setting time beyond cache duration
        mock_time.return_value = CACHE_DURATION + 1
        
        # Second call should hit API again due to cache expiry
        result2 = get_failed_replicasets('default')
        mock_v1.list_namespaced_replica_set.assert_called_once()
        
        # Verify results are the same
        self.assertEqual(result1, result2)
        self.assertEqual(result1, ['test-rs'])

    @patch('kge.cli.main.get_k8s_apps_client')
    @patch('kge.cli.main.time.time')
    def test_get_failed_replicasets_error_handling(self, mock_time, mock_get_apps_client):
        mock_v1 = MagicMock()
        mock_get_apps_client.return_value = mock_v1
        mock_time.return_value = 0  # Set initial time
        
        # Mock API error
        mock_v1.list_namespaced_replica_set.side_effect = Exception("API Error")
        
        # Should return empty list on error
        result = get_failed_replicasets('default')
        self.assertEqual(result, [])

    @patch('kge.cli.main.get_k8s_apps_client')
    @patch('kge.cli.main.time.time')
    def test_get_failed_replicasets_no_failures(self, mock_time, mock_get_apps_client):
        mock_v1 = MagicMock()
        mock_get_apps_client.return_value = mock_v1
        mock_time.return_value = 0  # Set initial time
        
        # Mock empty response
        mock_v1.list_namespaced_replica_set.return_value.items = []
        
        # Should return empty list when no failed replicasets
        result = get_failed_replicasets('default')
        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main() 