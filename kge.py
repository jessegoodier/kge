#!/usr/bin/env python3

import sys
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
        print(f"Error initializing Kubernetes client: {e}")
        sys.exit(1)

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
        print(f"Error fetching pods: {e}")
        sys.exit(1)

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
        print(f"Error fetching events: {e}")
        sys.exit(1)

def get_all_events(namespace: str) -> str:
    """Get all events in the namespace."""
    try:
        v1 = get_k8s_client()
        events = v1.list_namespaced_event(namespace)
        return format_events(events)
    except ApiException as e:
        print(f"Error fetching events: {e}")
        sys.exit(1)

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

def list_pods_for_completion():
    """List pods for zsh completion."""
    namespace = get_current_namespace()
    pods = get_pods(namespace)
    print(" ".join(pods))
    sys.exit(0)

def display_menu(pods: List[str]) -> None:
    """Display numbered menu of pods."""
    print("Select a pod:")
    print("  0) All pods")
    for i, pod in enumerate(pods, 1):
        print(f"{i:3d}) {pod}")

def get_user_selection(max_value: int) -> int:
    """Get and validate user selection."""
    while True:
        try:
            selection = int(input(f"Enter pod number (0-{max_value}): "))
            if 0 <= selection <= max_value:
                return selection
            print(f"Invalid selection. Please enter a number between 0 and {max_value}")
        except ValueError:
            print("Please enter a valid number")

def main():
    # Check if we can connect to Kubernetes
    try:
        get_k8s_client()
    except Exception as e:
        print(f"Error connecting to Kubernetes: {e}")
        sys.exit(1)

    # Check if we're being called for completion
    if len(sys.argv) > 1 and sys.argv[1] == "--complete":
        list_pods_for_completion()

    # Get current namespace
    namespace = get_current_namespace()
    print(f"Current namespace: {namespace}")

    # Handle -A flag for all events
    if len(sys.argv) > 1 and sys.argv[1] == "-A":
        print("Getting events for all pods")
        print("-" * 40)
        try:
            events = get_all_events(namespace)
            print(events)
            sys.exit(0)
        except Exception as e:
            print(f"Error getting events: {e}")
            sys.exit(1)

    # If a pod name is provided as a direct argument
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        pod_name = sys.argv[1]
        print(f"Getting events for pod: {pod_name}")
        print("-" * 40)
        try:
            events = get_events_for_pod(namespace, pod_name)
            print(events)
            sys.exit(0)
        except Exception as e:
            print(f"Error getting events: {e}")
            sys.exit(1)

    # Normal interactive execution
    print("Fetching pods...")
    pods = get_pods(namespace)
    if not pods:
        print(f"No pods found in namespace {namespace}")
        sys.exit(1)

    display_menu(pods)
    selection = get_user_selection(len(pods))
    
    if selection == 0:
        print("\nGetting events for all pods")
        print("-" * 40)
        try:
            events = get_all_events(namespace)
            print(events)
        except Exception as e:
            print(f"Error getting events: {e}")
    else:
        selected_pod = pods[selection - 1]
        print(f"\nGetting events for pod: {selected_pod}")
        print("-" * 40)
        try:
            events = get_events_for_pod(namespace, selected_pod)
            print(events)
        except Exception as e:
            print(f"Error getting events: {e}")

if __name__ == "__main__":
    main()