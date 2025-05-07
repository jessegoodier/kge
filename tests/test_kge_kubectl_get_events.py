import unittest
import time
import os
import subprocess
from kubernetes import client, config
from kge.cli.main import (
    get_events_for_pod,
    get_all_events,
    get_k8s_client,
    get_failures,
    get_pods,
    get_current_namespace,
    list_pods_for_completion,
    CACHE_DURATION,
    pod_cache,
    failures_cache,
    load_k8s_config,
)


class TestCLIWithRealK8s(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test namespace and resources before all tests."""
        # Load kube config
        config.load_kube_config()
        cls.v1 = client.CoreV1Api()

        # Create test namespace
        cls.test_namespace = "kge-test-namespace"
        try:
            cls.v1.create_namespace(
                client.V1Namespace(
                    metadata=client.V1ObjectMeta(name=cls.test_namespace)
                )
            )
        except client.ApiException as e:
            if e.status != 409:  # 409 means namespace already exists
                raise

        # Create test pod
        cls.test_pod_name = "test-pod"
        pod_manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": cls.test_pod_name},
            "spec": {
                "containers": [
                    {
                        "name": "nginx",
                        "image": "nginx:latest",
                        "ports": [{"containerPort": 80}],
                    }
                ]
            },
        }
        cls.v1.create_namespaced_pod(cls.test_namespace, pod_manifest)

        # Wait for pod to be ready and ensure events are generated
        for _ in range(30):  # Wait up to 30 seconds
            pod = cls.v1.read_namespaced_pod(cls.test_pod_name, cls.test_namespace)
            events = cls.v1.list_namespaced_event(
                cls.test_namespace,
                field_selector=f"involvedObject.name={cls.test_pod_name}"
            )
            if pod.status.phase == "Running" and len(events.items) > 0:
                # Verify we have events with timestamps
                if any(event.last_timestamp is not None for event in events.items):
                    break
            time.sleep(1)
        else:
            raise TimeoutError("Test pod failed to start or no events were generated")

    @classmethod
    def tearDownClass(cls):
        """Clean up test resources after all tests."""
        try:
            # Delete test pod
            cls.v1.delete_namespaced_pod(cls.test_pod_name, cls.test_namespace)
            # Delete test namespace
            cls.v1.delete_namespace(cls.test_namespace)
        except client.ApiException as e:
            print(f"Warning: Cleanup failed: {e}")

    def setUp(self):
        """Clear caches before each test."""
        pod_cache.clear()
        failures_cache.clear()
        get_current_namespace.cache_clear()
        load_k8s_config.cache_clear()
        get_k8s_client.cache_clear()

    def test_get_events_for_pod(self):
        """Test getting events for a specific pod."""
        events = get_events_for_pod(self.test_namespace, self.test_pod_name)
        self.assertIsNotNone(events)
        self.assertGreater(len(events.items), 0)

        # Verify event format
        event = events.items[0]
        self.assertIn(event.type, ["Normal", "Warning"])
        self.assertIsNotNone(event.reason)
        self.assertIsNotNone(event.message)

    def test_get_all_events(self):
        """Test getting all events in the namespace."""
        events = get_all_events(self.test_namespace)
        self.assertIsNotNone(events)
        self.assertGreater(len(events.items), 0)

    def test_get_failures(self):
        """Test getting failed items in the namespace."""
        failures = get_failures(self.test_namespace)
        self.assertIsInstance(failures, list)
        # In a clean test environment, there should be no failures
        self.assertEqual(len(failures), 0)

    def test_get_pods(self):
        """Test getting pods in the namespace."""
        pods = get_pods(self.test_namespace)
        self.assertIsInstance(pods, list)
        pod_names = [pod["name"] for pod in pods]
        self.assertIn(self.test_pod_name, pod_names)

    def test_list_pods_for_completion(self):
        """Test listing pods for completion."""
        # Mock command line arguments
        import sys

        original_argv = sys.argv
        sys.argv = ["kge", "--complete-pod", "-n", self.test_namespace]

        try:
            # Capture stdout
            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                with self.assertRaises(SystemExit) as cm:
                    list_pods_for_completion()
                self.assertEqual(cm.exception.code, 0)
            output = f.getvalue().strip()

            # Verify output contains our test pod
            self.assertIn(self.test_pod_name, output.split())
        finally:
            sys.argv = original_argv

    def test_get_events_for_pod_with_timestamps(self):
        """Test getting events with timestamps."""
        events = get_events_for_pod(
            self.test_namespace, self.test_pod_name, show_timestamps=True
        )
        self.assertIsNotNone(events)
        self.assertGreater(len(events.items), 0)

        # Verify at least one event has a timestamp
        has_timestamp = False
        for event in events.items:
            if event.last_timestamp is not None:
                has_timestamp = True
                break
        self.assertTrue(has_timestamp, "No events found with timestamps")

    def test_get_all_events_with_timestamps(self):
        """Test getting all events with timestamps."""
        events = get_all_events(self.test_namespace, show_timestamps=True)
        self.assertIsNotNone(events)
        self.assertGreater(len(events.items), 0)

        # Verify at least one event has a timestamp
        has_timestamp = False
        for event in events.items:
            if event.last_timestamp is not None:
                has_timestamp = True
                break
        self.assertTrue(has_timestamp, "No events found with timestamps")


if __name__ == "__main__":
    unittest.main()
