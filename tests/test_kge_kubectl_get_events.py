import unittest
from unittest.mock import patch, MagicMock
import warnings
from kge.cli.main import (
    get_events_for_pod,
    get_all_events,
    get_k8s_client,
    get_k8s_apps_client,
    get_failures,
    get_pods,
    get_current_namespace,
    list_pods_for_completion,
    CACHE_DURATION,
    pod_cache,
    failures_cache,
    load_k8s_config,
)

# Filter out the deprecation warning from kubernetes client
warnings.filterwarnings("ignore", category=DeprecationWarning, module="kubernetes.client.rest")

class TestCLI(unittest.TestCase):
    def setUp(self):
        # Clear caches before each test
        pod_cache.clear()
        failures_cache.clear()
        get_current_namespace.cache_clear()
        load_k8s_config.cache_clear()
        get_k8s_client.cache_clear()

    def _mock_k8s_response(self, mock_v1):
        """Helper method to mock Kubernetes API response headers to avoid deprecation warnings."""
        mock_response = MagicMock()
        mock_response.headers = {"key": "value"}
        mock_v1.api_client.rest_client.pool_manager.connection_from_url.return_value.urlopen.return_value = mock_response
        return mock_v1

    @patch("kge.cli.main.get_k8s_client")
    def test_get_events_for_pod(self, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = self._mock_k8s_response(mock_v1)

        # Mock the list_namespaced_event response
        mock_event = MagicMock()
        mock_event.type = "Normal"
        mock_event.last_timestamp = "2023-01-01T00:00:00Z"
        mock_event.reason = "Created"
        mock_event.message = "Test message"
        mock_v1.list_namespaced_event.return_value.items = [mock_event]

        result = get_events_for_pod("default", "test-pod")

        # Verify the field selector
        mock_v1.list_namespaced_event.assert_called_once()
        call_args = mock_v1.list_namespaced_event.call_args[1]
        self.assertEqual(call_args["field_selector"], "involvedObject.name=test-pod")

        # Verify the output format
        self.assertIn("Normal", result)
        self.assertIn("Created", result)
        self.assertIn("Test message", result)
        # Verify relative timestamp is shown by default
        self.assertIn("ago", result)

    @patch("kge.cli.main.get_k8s_client")
    def test_get_events_for_pod_with_timestamps(self, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = self._mock_k8s_response(mock_v1)

        # Mock the list_namespaced_event response
        mock_event = MagicMock()
        mock_event.type = "Normal"
        mock_event.last_timestamp = "2023-01-01T00:00:00Z"
        mock_event.reason = "Created"
        mock_event.message = "Test message"
        mock_v1.list_namespaced_event.return_value.items = [mock_event]

        result = get_events_for_pod("default", "test-pod", show_timestamps=True)

        # Verify the field selector
        mock_v1.list_namespaced_event.assert_called_once()
        call_args = mock_v1.list_namespaced_event.call_args[1]
        self.assertEqual(call_args["field_selector"], "involvedObject.name=test-pod")

        # Verify the output format
        self.assertIn("Normal", result)
        self.assertIn("Created", result)
        self.assertIn("Test message", result)
        # Verify absolute timestamp is shown
        self.assertIn("2023-01-01T00:00:00Z", result)

    @patch("kge.cli.main.get_k8s_client")
    def test_get_all_events(self, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = self._mock_k8s_response(mock_v1)

        # Mock the list_namespaced_event response
        mock_event = MagicMock()
        mock_event.type = "Normal"
        mock_event.last_timestamp = "2023-01-01T00:00:00Z"
        mock_event.reason = "Created"
        mock_event.message = "Test message"
        mock_v1.list_namespaced_event.return_value.items = [mock_event]

        result = get_all_events("default")

        # Verify the field selector is None for all events
        mock_v1.list_namespaced_event.assert_called_once()
        call_args = mock_v1.list_namespaced_event.call_args[1]
        self.assertIsNone(call_args.get("field_selector"))

        # Verify the output format
        self.assertIn("Normal", result)
        self.assertIn("Created", result)
        self.assertIn("Test message", result)

    @patch("kge.cli.main.get_k8s_client")
    def test_get_events_for_pod_non_normal(self, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = self._mock_k8s_response(mock_v1)

        # Mock the list_namespaced_event response
        mock_event = MagicMock()
        mock_event.type = "Warning"
        mock_event.last_timestamp = "2023-01-01T00:00:00Z"
        mock_event.reason = "Failed"
        mock_event.message = "Test message"
        mock_v1.list_namespaced_event.return_value.items = [mock_event]

        result = get_events_for_pod("default", "test-pod", non_normal=True)

        # Verify the field selector includes non-normal filter
        mock_v1.list_namespaced_event.assert_called_once()
        call_args = mock_v1.list_namespaced_event.call_args[1]
        self.assertIn("type!=Normal", call_args["field_selector"])

        # Verify the output format
        self.assertIn("Warning", result)
        self.assertIn("Failed", result)
        self.assertIn("Test message", result)

    @patch("kge.cli.main.get_k8s_client")
    def test_get_all_events_non_normal(self, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = self._mock_k8s_response(mock_v1)

        # Mock the list_namespaced_event response
        mock_event = MagicMock()
        mock_event.type = "Warning"
        mock_event.last_timestamp = "2023-01-01T00:00:00Z"
        mock_event.reason = "Failed"
        mock_event.message = "Test message"
        mock_v1.list_namespaced_event.return_value.items = [mock_event]

        result = get_all_events("default", non_normal=True)

        # Verify the field selector includes non-normal filter
        mock_v1.list_namespaced_event.assert_called_once()
        call_args = mock_v1.list_namespaced_event.call_args[1]
        self.assertEqual(call_args["field_selector"], "type!=Normal")

        # Verify the output format
        self.assertIn("Warning", result)
        self.assertIn("Failed", result)
        self.assertIn("Test message", result)

    def test_get_k8s_client(self):
        with patch("kge.cli.main.config.load_kube_config") as mock_load_config:
            with patch("kge.cli.main.client.CoreV1Api") as mock_api:
                mock_load_config.return_value = None
                mock_api.return_value = "mock_client"

                result = get_k8s_client()

                mock_load_config.assert_called_once()
                mock_api.assert_called_once()
                self.assertEqual(result, "mock_client")

    @patch("kge.cli.main.get_k8s_client")
    def test_get_events_for_pod_with_namespace(self, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = self._mock_k8s_response(mock_v1)

        # Mock the list_namespaced_event response
        mock_event = MagicMock()
        mock_event.type = "Normal"
        mock_event.last_timestamp = "2023-01-01T00:00:00Z"
        mock_event.reason = "Created"
        mock_event.message = "Test message"
        mock_v1.list_namespaced_event.return_value.items = [mock_event]

        result = get_events_for_pod("custom-namespace", "test-pod")

        # Verify the namespace is passed correctly
        mock_v1.list_namespaced_event.assert_called_once()
        call_args = mock_v1.list_namespaced_event.call_args
        self.assertEqual(
            call_args[0][0], "custom-namespace"
        )  # First positional arg is namespace
        self.assertEqual(call_args[1]["field_selector"], "involvedObject.name=test-pod")

    @patch("kge.cli.main.get_k8s_client")
    def test_get_all_events_with_namespace(self, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = self._mock_k8s_response(mock_v1)

        # Mock the list_namespaced_event response
        mock_event = MagicMock()
        mock_event.type = "Normal"
        mock_event.last_timestamp = "2023-01-01T00:00:00Z"
        mock_event.reason = "Created"
        mock_event.message = "Test message"
        mock_v1.list_namespaced_event.return_value.items = [mock_event]

        result = get_all_events("custom-namespace")

        # Verify the namespace is passed correctly
        mock_v1.list_namespaced_event.assert_called_once()
        call_args = mock_v1.list_namespaced_event.call_args
        self.assertEqual(
            call_args[0][0], "custom-namespace"
        )  # First positional arg is namespace
        self.assertIsNone(call_args[1].get("field_selector"))

    @patch("kge.cli.main.get_k8s_client")
    def test_get_events_for_pod_with_namespace_and_exceptions(self, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = self._mock_k8s_response(mock_v1)

        # Mock the list_namespaced_event response
        mock_event = MagicMock()
        mock_event.type = "Warning"
        mock_event.last_timestamp = "2023-01-01T00:00:00Z"
        mock_event.reason = "Failed"
        mock_event.message = "Test message"
        mock_v1.list_namespaced_event.return_value.items = [mock_event]

        result = get_events_for_pod("custom-namespace", "test-pod", non_normal=True)

        # Verify both namespace and exceptions filter are passed correctly
        mock_v1.list_namespaced_event.assert_called_once()
        call_args = mock_v1.list_namespaced_event.call_args
        self.assertEqual(
            call_args[0][0], "custom-namespace"
        )  # First positional arg is namespace
        self.assertIn("type!=Normal", call_args[1]["field_selector"])
        self.assertIn("involvedObject.name=test-pod", call_args[1]["field_selector"])

    @patch("kge.cli.main.get_k8s_client")
    def test_get_all_events_with_namespace_and_exceptions(self, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = self._mock_k8s_response(mock_v1)

        # Mock the list_namespaced_event response
        mock_event = MagicMock()
        mock_event.type = "Warning"
        mock_event.last_timestamp = "2023-01-01T00:00:00Z"
        mock_event.reason = "Failed"
        mock_event.message = "Test message"
        mock_v1.list_namespaced_event.return_value.items = [mock_event]

        result = get_all_events("custom-namespace", non_normal=True)

        # Verify both namespace and exceptions filter are passed correctly
        mock_v1.list_namespaced_event.assert_called_once()
        call_args = mock_v1.list_namespaced_event.call_args
        self.assertEqual(
            call_args[0][0], "custom-namespace"
        )  # First positional arg is namespace
        self.assertEqual(call_args[1]["field_selector"], "type!=Normal")

    def test_get_k8s_apps_client(self):
        with patch("kge.cli.main.config.load_kube_config") as mock_load_config:
            with patch("kge.cli.main.client.AppsV1Api") as mock_api:
                mock_load_config.return_value = None
                mock_api.return_value = "mock_apps_client"

                result = get_k8s_apps_client()

                mock_load_config.assert_called_once()
                mock_api.assert_called_once()
                self.assertEqual(result, "mock_apps_client")

    @patch("kge.cli.main.get_k8s_client")
    @patch("kge.cli.main.time.time")
    def test_get_failures_with_caching(self, mock_time, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = self._mock_k8s_response(mock_v1)

        mock_time.return_value = 0  # Set initial time

        # Mock the list_namespaced_event response
        mock_event = MagicMock()
        mock_event.involved_object.name = "test-rs"
        mock_v1.list_namespaced_event.return_value.items = [mock_event]

        # First call should hit the API
        result1 = get_failures("default")
        mock_v1.list_namespaced_event.assert_called_once()

        # Reset mock call count
        mock_v1.list_namespaced_event.reset_mock()

        # Second call within cache duration should use cache
        mock_time.return_value = CACHE_DURATION - 1  # Still within cache duration
        result2 = get_failures("default")
        mock_v1.list_namespaced_event.assert_not_called()

        # Verify results are the same
        self.assertEqual(result1, result2)

    @patch("kge.cli.main.get_k8s_client")
    @patch("kge.cli.main.time.time")
    def test_get_failures_cache_expiry(self, mock_time, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = self._mock_k8s_response(mock_v1)
        mock_time.return_value = 0  # Set initial time

        # Mock the list_namespaced_event response
        mock_event = MagicMock()
        mock_event.involved_object.name = "test-rs"
        mock_v1.list_namespaced_event.return_value.items = [mock_event]

        # First call
        result1 = get_failures("default")
        mock_v1.list_namespaced_event.assert_called_once()

        # Reset mock call count
        mock_v1.list_namespaced_event.reset_mock()

        # Simulate cache expiry by setting time beyond cache duration
        mock_time.return_value = CACHE_DURATION + 1

        # Second call should hit API again due to cache expiry
        result2 = get_failures("default")
        mock_v1.list_namespaced_event.assert_called_once()

        # Verify results are the same
        self.assertEqual(result1, result2)

    @patch("kge.cli.main.get_k8s_client")
    @patch("kge.cli.main.time.time")
    def test_get_failures_error_handling(
        self, mock_time, mock_get_client
    ):
        mock_v1 = MagicMock()
        mock_get_client.return_value = self._mock_k8s_response(mock_v1)
        mock_time.return_value = 0  # Set initial time

        # Mock API error
        mock_v1.list_namespaced_event.side_effect = Exception("API Error")

        # Should return empty list on error
        result = get_failures("default")
        self.assertEqual(result, [])

    @patch("kge.cli.main.get_k8s_client")
    @patch("kge.cli.main.time.time")
    def test_get_failures_no_failures(self, mock_time, mock_get_client):
        mock_v1 = MagicMock()
        mock_get_client.return_value = self._mock_k8s_response(mock_v1)
        mock_time.return_value = 0  # Set initial time

        # Mock empty response
        mock_v1.list_namespaced_event.return_value.items = []

        # Should return empty list when no failures
        result = get_failures("default")
        self.assertEqual(result, [])

    @patch("kge.cli.main.get_pods")
    @patch("kge.cli.main.get_failures")
    @patch("kge.cli.main.get_current_namespace")
    def test_list_pods_for_completion(
        self, mock_get_namespace, mock_get_failures, mock_get_pods
    ):
        mock_get_namespace.return_value = "default"
        mock_get_pods.return_value = ["pod1", "pod2"]
        mock_get_failures.return_value = [{"name": "rs1", "kind": "ReplicaSet", "namespace": "default"}, 
                                         {"name": "rs2", "kind": "ReplicaSet", "namespace": "default"}]

        with patch("kge.cli.main.sys.exit") as mock_exit:
            with patch("kge.cli.main.print") as mock_print:
                list_pods_for_completion()

                # Verify the output
                mock_print.assert_called_once_with("pod1 pod2 rs1 rs2")
                mock_exit.assert_called_once_with(0)


if __name__ == "__main__":
    unittest.main()
