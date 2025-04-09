import sys
import time
import argparse
from typing import List, Dict
from functools import lru_cache
from kubernetes import client, config
from kubernetes.client import ApiException
from colorama import init, Fore, Style

# Initialize colorama
init()

# Cache duration for pods and replicasets
CACHE_DURATION = 10
pod_cache: Dict[str, tuple[List[str], float]] = {}
replicaset_cache: Dict[str, tuple[List[str], float]] = {}

# Version information
VERSION = "0.2.5"

# class CustomHelpFormatter(argparse.HelpFormatter):
#     def __init__(self, prog):
#         super().__init__(prog, width=240)

#     def _format_usage(self, usage, actions, groups, prefix):
#         # Set width to 240 for usage message
#         self._width = 240
#         return super()._format_usage(usage, actions, groups, prefix)

def get_k8s_client():
    """Initialize and return a Kubernetes client."""
    try:
        config.load_kube_config()
        return client.CoreV1Api()
    except Exception as e:
        print(f"Error initializing Kubernetes client: {e}")
        sys.exit(1)

def get_k8s_apps_client():
    """Initialize and return a Kubernetes AppsV1Api client."""
    try:
        config.load_kube_config()
        return client.AppsV1Api()
    except Exception as e:
        print(f"Error initializing Kubernetes Apps client: {e}")
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
        if current_time - cache_time < CACHE_DURATION:
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

def get_events_for_pod(namespace: str, pod: str, non_normal: bool = False) -> str:
    """Get events for a specific pod."""
    try:
        v1 = get_k8s_client()
        field_selector = f"involvedObject.name={pod}"
        if non_normal:
            field_selector += ",type!=Normal"
        events = v1.list_namespaced_event(
            namespace,
            field_selector=field_selector
        )
        return format_events(events)
    except ApiException as e:
        print(f"Error fetching events: {e}")
        sys.exit(1)

def get_all_events(namespace: str, non_normal: bool = False) -> str:
    """Get all events in the namespace."""
    try:
        v1 = get_k8s_client()
        field_selector = None
        if non_normal:
            field_selector = "type!=Normal"
        events = v1.list_namespaced_event(namespace, field_selector=field_selector)
        return format_events(events)
    except ApiException as e:
        print(f"Error fetching events: {e}")
        sys.exit(1)

def format_events(events) -> str:
    """Format events into a readable string with color."""
    if not events.items:
        return f"{Fore.YELLOW}No events found{Style.RESET_ALL}"
    
    output = []
    for event in events.items:
        # Color based on event type
        color = Fore.GREEN if event.type == "Normal" else Fore.RED
        output.append(
            f"{Fore.CYAN}{event.last_timestamp}{Style.RESET_ALL} "
            f"{color}{event.type}{Style.RESET_ALL} "
            f"{Style.RESET_ALL}{event.involved_object.name} "
            f"{Fore.YELLOW}{event.reason}{Style.RESET_ALL}: "
            f"{event.message}"
        )
    return "\n".join(output)

def get_failed_replicasets(namespace: str) -> List[str]:
    """Get list of failed ReplicaSets in the specified namespace with caching."""
    current_time = time.time()
    
    # Check cache
    if namespace in replicaset_cache:
        cached_rs, cache_time = replicaset_cache[namespace]
        if current_time - cache_time < CACHE_DURATION:
            return cached_rs
    
    # Fetch fresh data
    try:
        v1 = get_k8s_apps_client()
        replicasets = v1.list_namespaced_replica_set(namespace)
        failed_rs = []
        for rs in replicasets.items:
            if rs.status and rs.status.conditions:
                for condition in rs.status.conditions:
                    if condition.type == "ReplicaFailure":
                        failed_rs.append(rs.metadata.name)
                        break
        
        # Update cache
        replicaset_cache[namespace] = (failed_rs, current_time)
        return failed_rs
    except ApiException as e:
        print(f"Error fetching ReplicaSets: {e}")
        return []

def list_pods_for_completion():
    """List pods for zsh completion."""
    namespace = get_current_namespace()
    pods = get_pods(namespace)
    failed_rs = get_failed_replicasets(namespace)
    pods.extend(failed_rs)
    print(" ".join(pods))
    sys.exit(0)

def display_menu(pods: List[str]) -> None:
    """Display numbered menu of pods with color."""
    print(f"{Fore.CYAN}Select a pod:{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}e{Style.RESET_ALL}) Abnormal events for all pods")
    print(f"  {Fore.GREEN}a{Style.RESET_ALL}) All pods, all events")
    for i, pod in enumerate(pods, 1):
        print(f"{Fore.GREEN}{i:3d}{Style.RESET_ALL}) {pod}")
    print(f"  {Fore.GREEN}q{Style.RESET_ALL}) Quit")

def get_user_selection(max_value: int) -> int:
    """Get and validate user selection."""
    while True:
        try:
            selection = input(f"Enter selection: ")
            if selection.lower() == "q":
                print("\nExiting gracefully...")
                sys.exit(0)
            if selection == "a":
                return "a"
            if selection == "e":
                return "e"
            selection = int(selection)
            if 1 <= selection <= max_value:
                return selection
            print(f"Invalid selection. Please enter a number between 1 and {max_value} or q to quit")
        except ValueError:
            print("Please enter a valid number, a, e or q to quit")
        except KeyboardInterrupt:
            print("\nExiting gracefully...")
            sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description='View Kubernetes events')
    parser.add_argument('pod', nargs='?', help='Pod name to view events for')
    parser.add_argument('-a', '--all', action='store_true', help='Get events for all pods')
    parser.add_argument('-n', '--namespace', help='Specify namespace to use')
    parser.add_argument('-e', '--exceptions-only', action='store_true', help='Show only non-normal events')
    parser.add_argument('--complete', action='store_true', help='List pods for shell completion')
    parser.add_argument('--completion', choices=['zsh'], help='Generate shell completion script')
    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {VERSION}',
                       help='Show version information and exit')
    args = parser.parse_args()

    # Check if we can connect to Kubernetes
    try:
        get_k8s_client()
    except Exception as e:
        print(f"{Fore.RED}Error connecting to Kubernetes: {e}{Style.RESET_ALL}")
        sys.exit(1)

    # Handle completion requests
    if args.complete:
        list_pods_for_completion()
    if args.completion == 'zsh':
        print("""_kge() {
    local -a pods
    pods=($(kge --complete))
    _describe 'pods' pods
}
compdef _kge kge""")
        sys.exit(0)

    # Get namespace (use specified or current)
    namespace = args.namespace if args.namespace else get_current_namespace()
    print(f"{Fore.CYAN}Using namespace: {namespace}{Style.RESET_ALL}")

    # Handle direct pod name argument
    if args.pod:
        print(f"{Fore.CYAN}Getting events for pod: {args.pod}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 40}{Style.RESET_ALL}")
        try:
            events = get_events_for_pod(namespace, args.pod, args.exceptions_only)
            print(events)
            sys.exit(0)
        except Exception as e:
            print(f"{Fore.RED}Error getting events: {e}{Style.RESET_ALL}")
            sys.exit(1)

    # Handle -a flag for all events
    if args.all:
        print(f"{Fore.CYAN}Getting events for all pods{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 40}{Style.RESET_ALL}")
        try:
            events = get_all_events(namespace, args.exceptions_only)
            print(events)
            sys.exit(0)
        except Exception as e:
            print(f"{Fore.RED}Error getting events: {e}{Style.RESET_ALL}")
            sys.exit(1)

    # Normal interactive execution
    print(f"{Fore.CYAN}Fetching pods...{Style.RESET_ALL}")
    pods = get_pods(namespace)
    failed_rs = get_failed_replicasets(namespace)
    pods.extend(failed_rs)
    if not pods:
        print(f"{Fore.YELLOW}No pods found in namespace {namespace}{Style.RESET_ALL}")
        sys.exit(1)

    display_menu(pods)
    selection = get_user_selection(len(pods))
    
    if selection == "e":  # Non-normal events for all pods
        print(f"\n{Fore.CYAN}Getting non-normal events for all pods{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 40}{Style.RESET_ALL}")
        try:
            events = get_all_events(namespace, non_normal=True)
            print(events)
        except Exception as e:
            print(f"{Fore.RED}Error getting events: {e}{Style.RESET_ALL}")
    elif selection == "a":  # All events for all pods
        print(f"\n{Fore.CYAN}Getting events for all pods{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 40}{Style.RESET_ALL}")
        try:
            events = get_all_events(namespace, args.exceptions_only)
            print(events)
        except Exception as e:
            print(f"{Fore.RED}Error getting events: {e}{Style.RESET_ALL}")
    else:  # Events for specific pod
        selected_pod = pods[selection - 1]
        print(f"\n{Fore.CYAN}Getting events for pod: {selected_pod}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 40}{Style.RESET_ALL}")
        try:
            events = get_events_for_pod(namespace, selected_pod, args.exceptions_only)
            print(events)
        except Exception as e:
            print(f"{Fore.RED}Error getting events: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)