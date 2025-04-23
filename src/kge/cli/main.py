import sys
import time
import argparse
from typing import List, Dict
from functools import lru_cache
from kubernetes import client, config
from rich.console import Console
from rich.style import Style
import os

from kge.completion import install_completion

def get_version():
    """Get the version from the package."""
    from kge import __version__
    return __version__
    

# Initialize rich console
console = Console()

# Cache duration for pods and failed creates
CACHE_DURATION = 10
pod_cache: Dict[str, tuple[List[str], float]] = {}
failed_create_cache: Dict[str, tuple[List[Dict[str, str]], float]] = {}

# Version information
VERSION = get_version()

def test_k8s_connection():
    """Test the connection to the Kubernetes cluster."""
    try:
        print("Testing connection to Kubernetes cluster...")
        get_k8s_client()
        v1 = get_k8s_client()
        namespaces = v1.list_namespace()
        print(f"Connected to cluster. Current namespaces: {namespaces}")
        # current_context = config.list_kube_config_contexts()[1]["context"]["name"]
        # console.print(f"[green]Connected to cluster. Current context: {current_context}[/green]")
    except Exception as e:
        if e.status == 401:
            console.print("[red]Error: Unauthorized access to Kubernetes cluster[/red]")
            console.print(f"[yellow]Please ensure you have valid credentials and proper access to the namespace '{namespace}'[/yellow]")
        elif e.status == 403:
            console.print("[red]Error: Forbidden access to Kubernetes cluster[/red]")
            console.print(f"[yellow]Please ensure you have valid credentials and proper access to the namespace '{namespace}'[/yellow]")
        elif e.status == 111:
            console.print("[red]Error: Connection refused to Kubernetes cluster[/red]")
            console.print("[yellow]Please ensure your cluster is running and accessible[/yellow]")
        else:
            console.print(f"[red]Error connecting to Kubernetes: {e}[/red]")
        sys.exit(1)

def get_k8s_client():
    """Initialize and return a Kubernetes client."""
    try:
        config.load_kube_config()
        return client.CoreV1Api()
    except Exception as e:
        if "MaxRetryError" in str(e):
            console.print("[red]Error: Unable to connect to Kubernetes cluster[/red]")
            console.print("[yellow]Please ensure that:[/yellow]")
            console.print("  1. Your Kubernetes cluster is running")
            console.print("  2. You have valid kubeconfig credentials")
            console.print("  3. The cluster is accessible from your network")
            console.print("  4. The API server is responding")
            console.print(f"\nDetailed error: {e}")
        else:
            console.print(f"[red]Error initializing Kubernetes client: {e}[/red]")
        sys.exit(1)

def get_k8s_apps_client():
    """Initialize and return a Kubernetes AppsV1Api client."""
    try:
        config.load_kube_config()
        return client.AppsV1Api()
    except Exception as e:
        console.print(f"Error initializing Kubernetes Apps client: {e}")
        sys.exit(1)


@lru_cache(maxsize=1)
def get_current_namespace() -> str:
    """Get the current Kubernetes namespace with caching."""
    try:
        return (
            config.list_kube_config_contexts()[1]["context"]["namespace"] or "default"
        )
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
    except client.ApiException as e:
        console.print(f"[red]Error fetching pods: {e}[/red]")
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
    except client.ApiException as e:
        console.print(f"Error fetching events: {e}")
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
    except client.ApiException as e:
        console.print(f"Error fetching events: {e}")
        sys.exit(1)

def format_events(events) -> str:
    """Format events into a readable string with color."""
    if not events.items:
        return "[yellow]No events found[/yellow]"

    output = []
    for event in events.items:
        # Color based on event type
        color = "green" if event.type == "Normal" else "red"
        output.append(
            f"[cyan]{event.last_timestamp}[/cyan] "
            f"[{color}]{event.type}[/{color}] "
            f"{event.involved_object.name} "
            f"[yellow]{event.reason}[/yellow]: "
            f"{event.message}"
        )
    return "\n".join(output)

def is_resource_healthy(namespace: str, name: str, kind: str) -> bool:
    """Check if a Kubernetes resource is healthy."""
    try:
        if kind == "ReplicaSet":
            apps_v1 = get_k8s_apps_client()
            rs = apps_v1.read_namespaced_replica_set(name, namespace)
            if rs.status.ready_replicas == rs.status.replicas:
                return True
            else:
                if hasattr(rs.metadata, 'owner_references') and rs.metadata.owner_references:
                    owner = rs.metadata.owner_references[0]  # Get first owner
                    return is_resource_healthy(namespace, owner.name, owner.kind)
                return False
        elif kind == "Deployment":
            apps_v1 = get_k8s_apps_client()
            deployment = apps_v1.read_namespaced_deployment(name, namespace)
            return deployment.status.ready_replicas == deployment.status.replicas
        elif kind == "StatefulSet":
            apps_v1 = get_k8s_apps_client()
            sts = apps_v1.read_namespaced_stateful_set(name, namespace)
            return sts.status.ready_replicas == sts.status.replicas
        elif kind == "Pod":
            v1 = get_k8s_client()
            pod = v1.read_namespaced_pod(name, namespace)
            return pod.status.phase == "Running"
        else:
            # For other resource types, we'll consider them healthy if they exist
            return True
    except Exception as e:
        print(f"Error checking health of {name} {kind}: {e}")
        # If we can't get the resource, assume it's not healthy
        return False

def get_failed_create(namespace: str) -> List[Dict[str, str]]:
    """Get list of things that failed to create in the given namespace.
    
    Returns a list of dictionaries with keys:
    - name: The name of the resource
    - kind: The kind of resource (e.g. ReplicaSet, Deployment)
    - namespace: The namespace the resource is in
    """
    current_time = time.time()
    
    # Check cache
    if namespace in failed_create_cache:
        cached_failed_rs, cache_time = failed_create_cache[namespace]
        if current_time - cache_time < CACHE_DURATION:
            return cached_failed_rs
    
    # kubectl get events --field-selector reason=FailedCreate
    try:
        v1 = get_k8s_client()
        events = v1.list_namespaced_event(namespace, field_selector="reason=FailedCreate")
        failed_create_items = []
        for event in events.items:
            # Check if the involved object exists and is healthy
            if hasattr(event, 'involved_object') and hasattr(event.involved_object, 'name'):
                name = event.involved_object.name
                kind = event.involved_object.kind
                if not is_resource_healthy(namespace, name, kind):
                    failed_create_items.append({
                        "name": name,
                        "kind": kind,
                        "namespace": namespace
                    })
            else:
                failed_create_items.append({
                    "name": event.metadata.name,
                    "kind": "Unknown",  # TODO: Add what kind of event it is this?
                    "namespace": namespace
                })

        # Update cache
        failed_create_cache[namespace] = (failed_create_items, current_time)
        return failed_create_items
    except Exception as e:
        console.print(f"Error fetching ReplicaSets: {e}")
        return []

def list_pods_for_completion():
    """List pods for zsh completion."""
    # Get namespace from command line arguments
    namespace = None
    for i, arg in enumerate(sys.argv):
        if arg in ["-n", "--namespace"] and i + 1 < len(sys.argv):
            namespace = sys.argv[i + 1]
            break

    if namespace is None:
        namespace = get_current_namespace()

    pods = get_pods(namespace)
    failed_create = get_failed_create(namespace)
    pods.extend([item["name"] for item in failed_create])
    print(" ".join(pods))
    sys.exit(0)

def display_menu(pods: List[str]) -> None:
    """Display numbered menu of pods with color."""
    console.print("[cyan]Select a pod:[/cyan]")
    console.print("  [green]e[/green]) Abnormal events for all pods")
    console.print("  [green]a[/green]) All pods, all events")
    for i, pod in enumerate(pods, 1):
        # Check if the pod is a failed create item
        if pod in [item["name"] for item in get_failed_create(get_current_namespace())]:
            console.print(f"[green]{i:3d}[/green]) [dark_orange]{pod}[/dark_orange] [red]FailedCreate[/red]")
        else:
            console.print(f"[green]{i:3d}[/green]) {pod}")
    console.print("  [green]q[/green]) Quit")

def get_user_selection(max_value: int) -> int:
    """Get and validate user selection."""
    while True:
        try:
            selection = input(f"Enter selection: ")
            if selection.lower() == "q":
                console.print("\nExiting gracefully...")
                sys.exit(0)
            if selection == "a":
                return "a"
            if selection == "e":
                return "e"
            selection = int(selection)
            if 1 <= selection <= max_value:
                return selection
            console.print(
                f"Invalid selection. Please enter a number between 1 and {max_value} or q to quit"
            )
        except ValueError:
            console.print("Please enter a valid number, a, e or q to quit")
        except KeyboardInterrupt:
            console.print("\nExiting gracefully...")
            sys.exit(0)

def get_namespaces() -> List[str]:
    """Get list of available namespaces."""
    try:
        v1 = get_k8s_client()
        namespaces = v1.list_namespace()
        return [ns.metadata.name for ns in namespaces.items]
    except client.ApiException as e:
        console.print(f"Error fetching namespaces: {e}")
        return []

def list_namespaces_for_completion():
    """List namespaces for zsh completion."""
    namespaces = get_namespaces()
    print(" ".join(namespaces))
    sys.exit(0)

def get_all_kinds(namespace: str) -> List[str]:
    """Get list of all unique kinds from events in the namespace."""
    try:
        v1 = get_k8s_client()
        events = v1.list_namespaced_event(namespace)
        kinds = set()
        for event in events.items:
            if hasattr(event.involved_object, 'kind'):
                kinds.add(event.involved_object.kind)
        return sorted(list(kinds))
    except client.ApiException as e:
        console.print(f"Error fetching kinds: {e}")
        return []

def list_kinds_for_completion():
    """List kinds for zsh completion."""
    # Get namespace from command line arguments
    namespace = None
    for i, arg in enumerate(sys.argv):
        if arg in ["-n", "--namespace"] and i + 1 < len(sys.argv):
            namespace = sys.argv[i + 1]
            break

    if namespace is None:
        namespace = get_current_namespace()

    kinds = get_all_kinds(namespace)
    print(" ".join(kinds))
    sys.exit(0)

def get_resources_of_kind(namespace: str, kind: str) -> List[str]:
    """Get list of resources of a specific kind in the namespace."""
    try:
        v1 = get_k8s_client()
        # Get all events and filter by kind
        events = v1.list_namespaced_event(namespace)
        resources = set()
        for event in events.items:
            if (
                hasattr(event.involved_object, "kind")
                and event.involved_object.kind == kind
            ):
                resources.add(event.involved_object.name)
        return sorted(list(resources))
    except client.ApiException as e:
        console.print(f"Error fetching resources: {e}")
        return []

def list_resources_for_completion():
    """List resources for zsh completion."""
    # Get namespace and kind from command line arguments
    namespace = None
    kind = None
    for i, arg in enumerate(sys.argv):
        if arg in ["-n", "--namespace"] and i + 1 < len(sys.argv):
            namespace = sys.argv[i + 1]
        elif arg in ["-k", "--kind"] and i + 1 < len(sys.argv):
            kind = sys.argv[i + 1]

    if namespace is None:
        namespace = get_current_namespace()

    if kind is None:
        print("")
        sys.exit(0)

    resources = get_resources_of_kind(namespace, kind)
    print(" ".join(resources))
    sys.exit(0)

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description=f'''View Kubernetes events
Suggested usage:
[cyan]kge -ea[/cyan] to see all abnormal events in the namespace add [cyan]-n[/cyan] to specify a different namespace
[cyan]source <(kge --completion=zsh)[/cyan] to enable zsh completion for pods and namespaces''',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pod", nargs="?", help="Pod name to get events for")
    parser.add_argument("-n", "--namespace", help="Namespace to use")
    parser.add_argument(
        "-e",
        "--exceptions-only",
        action="store_true",
        help="Show only non-normal events",
    )
    parser.add_argument(
        "-a", "--all", action="store_true", help="Get events for all pods"
    )
    parser.add_argument("-k", "--kind", help="List all unique kinds from events")
    parser.add_argument('--completion', choices=['zsh'], help="Output shell completion script")
    parser.add_argument(
        "--install-completion", action="store_true", help="Install shell completion"
    )
    parser.add_argument(
        "-v", "--version", action="store_true", help="Show version information"
    )
    parser.add_argument(
        "--complete-ns", action="store_true", help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--complete-kind", action="store_true", help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--complete-pod", action="store_true", help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--complete-resource", action="store_true", help=argparse.SUPPRESS
    )

    args = parser.parse_args()

    if args.version:
        console.print(f"kge version {VERSION}")
        sys.exit(0)

    if args.install_completion:
        install_completion()
        sys.exit(0)

    # Check if we can connect to Kubernetes
    try:
        get_k8s_client()
        test_k8s_connection()
    except Exception as e:
        console.print(f"[red]Error connecting to Kubernetes: {e}[/red]")
        sys.exit(1)

    if args.completion:
        try:
            completion_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'completion', '_kge')
            with open(completion_file, 'r') as f:
                print(f.read())
            sys.exit(0)
        except Exception as e:
            console.print(f"[red]Error reading completion file: {e}[/red]")
            sys.exit(1)

    # Handle completion requests
    if args.complete_pod:
        list_pods_for_completion()
    if args.complete_ns:
        list_namespaces_for_completion()
    if args.complete_kind:
        list_kinds_for_completion()
    if args.complete_resource:
        list_resources_for_completion()

    # Get namespace (use specified or current)
    namespace = args.namespace if args.namespace else get_current_namespace()
    console.print(f"[cyan]Using namespace: {namespace}[/cyan]")

    # Handle -k flag for listing kinds or showing events for a specific resource
    if args.kind:
        # If there's a resource name argument, show events for that specific resource
        if args.pod:
            console.print(
                f"[cyan]Getting events for {args.kind} {args.pod}[/cyan]"
            )
            console.print(f"[cyan]{'-' * 40}[/cyan]")
            try:
                v1 = get_k8s_client()
                field_selector = (
                    f"involvedObject.name={args.pod},involvedObject.kind={args.kind}"
                )
                if args.exceptions_only:
                    field_selector += ",type!=Normal"
                events = v1.list_namespaced_event(
                    namespace, field_selector=field_selector
                )
                console.print(format_events(events))
                sys.exit(0)
            except Exception as e:
                console.print(f"[red]Error getting events: {e}[/red]")
                sys.exit(1)
        # Otherwise, just list the kinds
        else:
            console.print(f"[cyan]Getting all unique kinds from events[/cyan]")
            console.print(f"[cyan]{'-' * 40}[/cyan]")
            try:
                kinds = get_all_kinds(namespace)
                if kinds:
                    for kind in kinds:
                        console.print(f"[green]{kind}[/green]")
                else:
                    console.print(
                        f"[yellow]No kinds found in namespace {namespace}[/yellow]"
                    )
                sys.exit(0)
            except Exception as e:
                console.print(f"[red]Error getting kinds: {e}[/red]")
                sys.exit(1)

    # Handle direct pod name argument (default case)
    if args.pod:
        console.print(f"[cyan]Getting events for pod: {args.pod}[/cyan]")
        console.print(f"[cyan]{'-' * 40}[/cyan]")
        try:
            events = get_events_for_pod(namespace, args.pod, args.exceptions_only)
            console.print(events)
            sys.exit(0)
        except Exception as e:
            console.print(f"[red]Error getting events: {e}[/red]")
            sys.exit(1)

    # Handle -a flag for all events
    if args.all:
        console.print(f"[cyan]Getting events for all pods[/cyan]")
        console.print(f"[cyan]{'-' * 40}[/cyan]")
        try:
            events = get_all_events(namespace, args.exceptions_only)
            console.print(events)
            sys.exit(0)
        except Exception as e:
            console.print(f"[red]Error getting events: {e}[/red]")
            sys.exit(1)

    # Normal interactive execution
    console.print(f"[cyan]Fetching pods...[/cyan]")
    pods = get_pods(namespace)
    failed_create = get_failed_create(namespace)
    pods.extend([item["name"] for item in failed_create])
    if not pods:
        console.print(f"[yellow]No pods found in namespace {namespace}[/yellow]")
        sys.exit(1)

    display_menu(pods)
    selection = get_user_selection(len(pods))

    if selection == "e":  # Non-normal events for all pods
        console.print(f"\n[cyan]Getting non-normal events for all pods[/cyan]")
        console.print(f"[cyan]{'-' * 40}[/cyan]")
        try:
            events = get_all_events(namespace, non_normal=True)
            console.print(events)
        except Exception as e:
            console.print(f"[red]Error getting events: {e}[/red]")
    elif selection == "a":  # All events for all pods
        console.print(f"\n[cyan]Getting events for all pods[/cyan]")
        console.print(f"[cyan]{'-' * 40}[/cyan]")
        try:
            events = get_all_events(namespace, args.exceptions_only)
            console.print(events)
        except Exception as e:
            console.print(f"[red]Error getting events: {e}[/red]")
    else:  # Events for specific pod
        selected_pod = pods[selection - 1]
        console.print(f"\n[cyan]Getting events for pod: {selected_pod}[/cyan]")
        console.print(f"[cyan]{'-' * 40}[/cyan]")
        try:
            events = get_events_for_pod(namespace, selected_pod, args.exceptions_only)
            console.print(events)
        except Exception as e:
            console.print(f"[red]Error getting events: {e}[/red]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\nExiting gracefully...")
        sys.exit(0)
    except Exception as e:
        console.print(f"\nError: {e}")
        sys.exit(1)