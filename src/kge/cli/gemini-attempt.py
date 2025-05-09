import sys
import time
import argparse
from typing import List, Dict
from kubernetes import client, config
from rich.console import Console
import rich.box
import os

def get_kubernetes_api_client():
    """
    Loads Kubernetes configuration and returns an API client.
    """
    try:
        # Try to load in-cluster configuration
        config.load_incluster_config()
    except config.ConfigException:
        try:
            # Try to load local kubeconfig
            config.load_kube_config()
        except config.ConfigException:
            raise Exception("Could not configure Kubernetes client. "
                            "Ensure you have a valid kubeconfig or are running in-cluster.")
    return client.CoreV1Api()

def fetch_events(namespace: str, v1: client.CoreV1Api):
    """
    Fetches events from the specified namespace.
    """
    if namespace:
        print(f"Fetching events for namespace: {namespace}")
        return v1.list_namespaced_event(namespace=namespace, watch=False)
    else:
        print("Fetching events for all namespaces")
        return v1.list_event_for_all_namespaces(watch=False)

def process_and_filter_events(namespace: str = None, reason_filter: str = None, kind_filter: str = None, type_filter: str = None):
    """
    Fetches, processes, filters, and displays unique Kubernetes events.

    Args:
        namespace (str, optional): The Kubernetes namespace to fetch events from.
                                   If None, fetches from all namespaces.
        reason_filter (str, optional): Filter events by this reason (e.g., "Failed", "Scheduled").
        kind_filter (str, optional): Filter events by the kind of the involved object (e.g., "Pod", "Deployment").
        type_filter (str, optional): Filter events by type (e.g., "Normal", "Warning").
    """
    try:
        v1 = get_kubernetes_api_client()
        events_list = fetch_events(namespace, v1)
    except Exception as e:
        print(f"Error fetching events: {e}")
        return

    processed_events = []
    # Using a set to track unique event signatures to avoid redundant processing if desired
    # A signature could be a tuple of (name, kind, reason, first_timestamp, message)
    # For simplicity here, we'll just process all and then you can decide how to define "unique"
    # for display or further processing.

    print("\n--- Filtered Events ---")
    if not events_list.items:
        print("No events found.")
        return

    for event_item in events_list.items:
        # Safely access attributes from the event object (V1Event)
        event_namespace = event_item.metadata.namespace if event_item.metadata else None
        reason = event_item.reason
        message = event_item.message
        first_timestamp = event_item.first_timestamp
        last_timestamp = event_item.last_timestamp
        api_version = event_item.involved_object.api_version if event_item.involved_object else None
        event_type = event_item.type

        involved_object_name = None
        involved_object_kind = None

        if event_item.involved_object:
            involved_object_name = event_item.involved_object.name
            involved_object_kind = event_item.involved_object.kind

        # --- Filtering Logic ---
        if reason_filter and reason != reason_filter:
            continue
        if kind_filter and involved_object_kind != kind_filter:
            continue
        if type_filter and event_type != type_filter:
            continue
        # Add more filters as needed

        event_data = {
            "namespace": event_namespace,
            "involved_object_name": involved_object_name,
            "involved_object_kind": involved_object_kind,
            "reason": reason,
            "message": message,
            "first_timestamp": first_timestamp.isoformat() if first_timestamp else None,
            "last_timestamp": last_timestamp.isoformat() if last_timestamp else None,
            "api_version": api_version,
            "type": event_type,
            "count": event_item.count
        }
        processed_events.append(event_data)

        # --- Displaying the event (simple print) ---
        print(f"\nNamespace: {event_namespace}")
        if involved_object_name and involved_object_kind:
            print(f"  Involved Object: {involved_object_kind}/{involved_object_name}")
        print(f"  Reason: {reason}")
        print(f"  Type: {event_type}")
        print(f"  Message: {message}")
        print(f"  Count: {event_item.count}")
        if first_timestamp:
            print(f"  First Seen: {first_timestamp.isoformat()}")
        if last_timestamp:
            print(f"  Last Seen: {last_timestamp.isoformat()}")
        if api_version:
            print(f"  API Version: {api_version}")

    if not processed_events:
        print("No events matched the specified filters.")

    # If you need a list of unique event objects based on some criteria,
    # you would implement that logic here. For example, to get unique
    # combinations of (name, kind, reason):
    # unique_signatures = set()
    # truly_unique_events = []
    # for pe in processed_events:
    #     signature = (pe["involved_object_name"], pe["involved_object_kind"], pe["reason"], pe["message"]) # Adjust signature as needed
    #     if signature not in unique_signatures:
    #         unique_signatures.add(signature)
    #         truly_unique_events.append(pe)
    # print(f"\n--- Truly Unique Event Signatures Found: {len(truly_unique_events)} ---")
    # for ue in truly_unique_events:
    #     print(ue)

    return processed_events


if __name__ == "__main__":
    # Example Usage:

    # 1. Get all events from a specific namespace
    # print("--- Events from 'default' namespace ---")
    # process_and_filter_events(namespace="default")

    # 2. Get all Warning events from all namespaces
    # print("\n--- All Warning Events ---")
    # process_and_filter_events(type_filter="Warning")

    # 3. Get all "Failed" events for "Pod" kinds across all namespaces
    process_and_filter_events()
    print("\n--- Failed Pod Events ---")
    process_and_filter_events(reason_filter="Failed", kind_filter="Pod")

    # 4. Get all events from all namespaces (can be a lot of data)
    # print("\n--- All Events from All Namespaces ---")
    # process_and_filter_events()

    # 5. Get events with a specific reason from a specific namespace
    # print("\n--- 'Pulled' events in 'kube-system' namespace ---")
    # process_and_filter_events(namespace="kube-system", reason_filter="Pulled")