import time
from typing import List, Dict
from functools import lru_cache
from kubernetes import client, config
from kubernetes.client import ApiException

# Cache pod list for 30 seconds
POD_CACHE_DURATION = 30
pod_cache: Dict[str, tuple[List[str], float]] = {}

def get_k8s_client():
    """Initialize and return a Kubernetes client."""
    try:
        config.load_kube_config()
        return client.CoreV1Api()
    except Exception as e:
        raise RuntimeError(f"Error initializing Kubernetes client: {e}")

@lru_cache(maxsize=1)
def get_current_namespace() -> str:
    """Get the current Kubernetes namespace with caching."""
    try:
        return config.list_kube_config_contexts()[1]['context']['namespace'] or "default"
    except Exception:
        return "default"

def get_pods(namespace: str) -> List[str]:
    """Get list of pods in the specified namespace with caching."""
    current_time = time.time()
    
    # Check cache
    if namespace in pod_cache:
        cached_pods, cache_time = pod_cache[namespace]
        if current_time - cache_time < POD_CACHE_DURATION:
            return cached_pods
    
    # Fetch fresh data
    try:
        v1 = get_k8s_client()
        pods = v1.list_namespaced_pod(namespace)
        pod_names = [pod.metadata.name for pod in pods.items]
        
        # Update cache
        pod_cache[namespace] = (pod_names, current_time)
        return pod_names
    except ApiException as e:
        raise RuntimeError(f"Error fetching pods: {e}")

def get_events_for_pod(namespace: str, pod: str) -> str:
    """Get events for a specific pod."""
    try:
        v1 = get_k8s_client()
        events = v1.list_namespaced_event(
            namespace,
            field_selector=f"involvedObject.name={pod}"
        )
        return format_events(events)
    except ApiException as e:
        raise RuntimeError(f"Error fetching events: {e}")

def get_all_events(namespace: str) -> str:
    """Get all events in the namespace."""
    try:
        v1 = get_k8s_client()
        events = v1.list_namespaced_event(namespace)
        return format_events(events)
    except ApiException as e:
        raise RuntimeError(f"Error fetching events: {e}")

def format_events(events) -> str:
    """Format events into a readable string."""
    if not events.items:
        return "No events found"
    
    output = []
    for event in events.items:
        output.append(
            f"{event.last_timestamp} {event.type} {event.reason}: {event.message}"
        )
    return "\n".join(output) 