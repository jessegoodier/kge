import sys
import argparse
from typing import List

from ..kubernetes import (
    get_current_namespace,
    get_pods,
    get_events_for_pod,
    get_all_events,
    get_k8s_client
)

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

def generate_zsh_completion():
    """Generate zsh completion script."""
    script = """#compdef kge

_kge() {
    local -a pods
    pods=($(kge --complete))
    _describe 'pods' pods
}

compdef _kge kge
"""
    print(script)
    sys.exit(0)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="""A kubectl plugin for viewing Kubernetes events in a user-friendly way.

Examples:
  # View events for all pods in current namespace
  kge -A
  kge --all

  # View events for a specific pod
  kge my-pod

  # Interactive mode (shows menu of pods)
  kge

  # Enable shell completion for zsh
  source <(kge --completion=zsh)""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-A", "--all",
        action="store_true",
        help="Get events for all pods in the current namespace"
    )
    group.add_argument(
        "--complete",
        action="store_true",
        help="List pods for shell completion (internal use)"
    )
    group.add_argument(
        "--completion",
        choices=["zsh"],
        help="Generate shell completion script. Usage: source <(kge --completion=zsh)"
    )
    
    parser.add_argument(
        "pod_name",
        nargs="?",
        help="Name of the pod to get events for"
    )
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Check if we can connect to Kubernetes
    try:
        get_k8s_client()
    except Exception as e:
        print(f"Error connecting to Kubernetes: {e}")
        sys.exit(1)

    # Handle completion options
    if args.complete:
        list_pods_for_completion()
    elif args.completion == "zsh":
        generate_zsh_completion()

    # Get current namespace
    namespace = get_current_namespace()
    print(f"Current namespace: {namespace}")

    # Handle -A flag for all events
    if args.all:
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
    if args.pod_name:
        print(f"Getting events for pod: {args.pod_name}")
        print("-" * 40)
        try:
            events = get_events_for_pod(namespace, args.pod_name)
            print(events)
            sys.exit(0)
        except Exception as e:
            print(f"Error getting events: {e}")
            sys.exit(1)

    # Normal interactive execution
    print("Fetching pods...")
    try:
        pods = get_pods(namespace)
        if not pods:
            print(f"No pods found in namespace {namespace}")
            sys.exit(1)

        display_menu(pods)
        selection = get_user_selection(len(pods))
        
        if selection == 0:
            print("\nGetting events for all pods")
            print("-" * 40)
            events = get_all_events(namespace)
            print(events)
        else:
            selected_pod = pods[selection - 1]
            print(f"\nGetting events for pod: {selected_pod}")
            print("-" * 40)
            events = get_events_for_pod(namespace, selected_pod)
            print(events)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 