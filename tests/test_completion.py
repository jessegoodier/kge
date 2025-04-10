import unittest
from unittest.mock import patch, MagicMock
import sys
from kge.cli.main import list_pods_for_completion, list_namespaces_for_completion, get_namespaces

class TestCompletion(unittest.TestCase):
    def setUp(self):
        # Mock the Kubernetes client
        self.mock_v1 = MagicMock()
        self.mock_apps_v1 = MagicMock()
        
        # Mock the config
        self.patcher_config = patch('kge.cli.main.config')
        self.mock_config = self.patcher_config.start()
        self.mock_config.load_kube_config.return_value = None
        self.mock_config.list_kube_config_contexts.return_value = [None, {'context': {'namespace': 'default'}}]

        # Mock the client
        self.patcher_client = patch('kge.cli.main.client')
        self.mock_client = self.patcher_client.start()
        self.mock_client.CoreV1Api.return_value = self.mock_v1
        self.mock_client.AppsV1Api.return_value = self.mock_apps_v1

    def tearDown(self):
        self.patcher_config.stop()
        self.patcher_client.stop()

    def test_list_namespaces_for_completion(self):
        # Mock the namespace list
        mock_namespace = MagicMock()
        mock_namespace.metadata.name = 'test-namespace'
        self.mock_v1.list_namespace.return_value.items = [mock_namespace]

        # Mock print and handle sys.exit
        with patch('builtins.print') as mock_print:
            with self.assertRaises(SystemExit) as cm:
                list_namespaces_for_completion()
            self.assertEqual(cm.exception.code, 0)
            mock_print.assert_called_once_with('test-namespace')

    def test_list_pods_for_completion_default_namespace(self):
        # Mock the pod list
        mock_pod = MagicMock()
        mock_pod.metadata.name = 'test-pod'
        self.mock_v1.list_namespaced_pod.return_value.items = [mock_pod]

        # Mock the replicaset list
        mock_rs = MagicMock()
        mock_rs.metadata.name = 'test-rs'
        mock_rs.status.conditions = [MagicMock(type='ReplicaFailure')]
        self.mock_apps_v1.list_namespaced_replica_set.return_value.items = [mock_rs]

        # Mock print and handle sys.exit
        with patch('builtins.print') as mock_print:
            with self.assertRaises(SystemExit) as cm:
                list_pods_for_completion()
            self.assertEqual(cm.exception.code, 0)
            mock_print.assert_called_once_with('test-pod test-rs')

    def test_list_pods_for_completion_specific_namespace(self):
        # Mock the pod list
        mock_pod = MagicMock()
        mock_pod.metadata.name = 'test-pod'
        self.mock_v1.list_namespaced_pod.return_value.items = [mock_pod]

        # Mock the replicaset list
        mock_rs = MagicMock()
        mock_rs.metadata.name = 'test-rs'
        mock_rs.status.conditions = [MagicMock(type='ReplicaFailure')]
        self.mock_apps_v1.list_namespaced_replica_set.return_value.items = [mock_rs]

        # Mock command line arguments and print
        with patch('sys.argv', ['kge', '--complete-pod', '-n', 'test-namespace']):
            with patch('builtins.print') as mock_print:
                with self.assertRaises(SystemExit) as cm:
                    list_pods_for_completion()
                self.assertEqual(cm.exception.code, 0)
                mock_print.assert_called_once_with('test-pod test-rs')
                # Verify the correct namespace was used
                self.mock_v1.list_namespaced_pod.assert_called_once_with('test-namespace')
                self.mock_apps_v1.list_namespaced_replica_set.assert_called_once_with('test-namespace')

    def test_get_namespaces(self):
        # Mock the namespace list
        mock_namespace = MagicMock()
        mock_namespace.metadata.name = 'test-namespace'
        self.mock_v1.list_namespace.return_value.items = [mock_namespace]

        namespaces = get_namespaces()
        self.assertEqual(namespaces, ['test-namespace'])

if __name__ == '__main__':
    unittest.main() 