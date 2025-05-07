import sys
import time
import argparse
from typing import List, Dict
from kubernetes import client, config
from rich.console import Console
import rich.box
import os

from kge.completion import install_completion

from functools import lru_cache


def get_version():
    """Get the version from the package."""
    from kge import __version__

    return __version__


# Initialize rich console
console = Console()

# Cache duration for pods and failed creates
CACHE_DURATION = int(os.getenv("KGE_CACHE_DURATION", "7"))  # Default 7 seconds
pod_cache: Dict[str, tuple[List[Dict[str, str]], float]] = {}
failures_cache: Dict[str, tuple[List[Dict[str, str]], float]] = {}

# Add health check cache
health_check_cache: Dict[str, tuple[bool, float]] = {}

# Version information
VERSION = get_version()

# Debug flag
DEBUG = False


def debug_print(*args, **kwargs):
    """Print debug messages only if debug mode is enabled."""
    if DEBUG:
        console.print("[dim]DEBUG:[/dim]", *args, **kwargs)


@lru_cache(maxsize=1)
def load_k8s_config():
    """Load and cache the Kubernetes config."""
    try:
        debug_print("Loading Kubernetes config...")
        config.load_kube_config()
        debug_print("Successfully loaded Kubernetes config")
    except Exception as e:
        debug_print(f"Error details while loading config: {e}")
        console.print(f"[red]Error loading Kubernetes config: {e}[/red]")
        sys.exit(1)


@lru_cache(maxsize=1)
def get_k8s_client():
    """Initialize and return a Kubernetes client."""
    load_k8s_config()
    return client.CoreV1Api()


@lru_cache(maxsize=1)
def get_k8s_apps_client():
    """Initialize and return a Kubernetes AppsV1Api client."""
    load_k8s_config()
    return client.AppsV1Api()


def test_k8s_connection():
    """Test the connection to the Kubernetes cluster."""
    try:
        debug_print("Testing Kubernetes connection...")
        v1 = get_k8s_client()
        namespaces = v1.list_namespace()
        debug_print(f"Found {len(namespaces.items)} namespaces")
        debug_print("Successfully connected to Kubernetes cluster")
    except Exception as e:
        debug_print(f"Connection error details: {e}")
        if e.status == 401:
            console.print("[red]Error: Unauthorized access to Kubernetes cluster[/red]")
            console.print(
                f"""[yellow]{e.status}:
                Please ensure you have valid credentials to the cluster
                \n{e.reason}[/yellow]"""
            )
        elif e.status == 403:
            console.print("[red]Error: Forbidden access to Kubernetes cluster[/red]")
            console.print(
                f"""[yellow]{e.status}:
                Please ensure you have valid credentials to the cluster
                \n{e.reason}[/yellow]"""
            )
        elif e.status == 111:
            console.print("[red]Error: Connection refused to Kubernetes cluster[/red]")
            console.print(
                f"""[yellow]{e.status}:
                Please ensure your cluster is running and accessible
                \n{e.reason}[/yellow]"""
            )
        else:
            console.print(f"[red]Error connecting to Kubernetes: {e}[/red]")
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


def get_menu_items(namespace: str) -> tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    console.print("[cyan]Fetching Events...[/cyan]")
    pods = get_pods(namespace)
    failures = get_failures(namespace)

    # Create a set of pod names for quick lookup
    pod_names = {pod["name"] for pod in pods}

    # Add failed items that aren't pods to the list
    for failure in failures:
        if failure["name"] not in pod_names:
            pods.append(
                {
                    "name": failure["name"],
                    "controller_kind": failure["kind"],
                    "controller_name": failure["name"],
                }
            )

    # Sort pods by name for consistent display
    pods = sorted(pods, key=lambda x: x["name"])

    if not pods:
        console.print(f"[yellow]No pods found in namespace {namespace}[/yellow]")
        sys.exit(1)
    return pods, failures


def get_top_level_controller(v1, apps_v1, namespace: str, owner_ref) -> tuple[str, str]:
    """Get the top level controller by traversing owner references."""
    if owner_ref.kind == "ReplicaSet":
        try:
            rs = apps_v1.read_namespaced_replica_set(owner_ref.name, namespace)
            if (
                hasattr(rs.metadata, "owner_references")
                and rs.metadata.owner_references
            ):
                return get_top_level_controller(
                    v1, apps_v1, namespace, rs.metadata.owner_references[0]
                )
        except Exception as e:
            debug_print(f"Error getting ReplicaSet {owner_ref.name}: {e}")
    return owner_ref.kind, owner_ref.name


def get_pods(namespace: str) -> List[Dict[str, str]]:
    """Get list of pods in the specified namespace with caching."""
    current_time = time.time()
    debug_print(f"Getting pods for namespace: {namespace}")

    # Check cache
    if namespace in pod_cache:
        cached_pods, cache_time = pod_cache[namespace]
        if current_time - cache_time < CACHE_DURATION:
            debug_print(f"Using cached pods for namespace {namespace}")
            return cached_pods

    # Fetch fresh data
    try:
        debug_print(f"Fetching fresh pod data for namespace {namespace}")
        v1 = get_k8s_client()
        apps_v1 = get_k8s_apps_client()
        pods = v1.list_namespaced_pod(namespace)
        pod_info = []
        for pod in pods.items:
            pod_dict = {"name": pod.metadata.name}
            # Check for controller reference
            if (
                hasattr(pod.metadata, "owner_references")
                and pod.metadata.owner_references
            ):
                owner = pod.metadata.owner_references[0]
                controller_kind, controller_name = get_top_level_controller(
                    v1, apps_v1, namespace, owner
                )
                pod_dict["controller_kind"] = controller_kind
                pod_dict["controller_name"] = controller_name
            else:
                pod_dict["controller_kind"] = "Pod"
                pod_dict["controller_name"] = pod.metadata.name
            pod_info.append(pod_dict)
        debug_print(f"Found {len(pod_info)} pods in namespace {namespace}")

        # Update cache
        pod_cache[namespace] = (pod_info, current_time)
        return pod_info
    except client.ApiException as e:
        debug_print(f"Error details while fetching pods: {e}")
        console.print(f"[red]Error fetching pods: {e}[/red]")
        sys.exit(1)


def get_events_for_pod(
    namespace: str, pod: str, non_normal: bool = False, show_timestamps: bool = False
) -> str:
    """Get events for a specific pod."""
    try:
        debug_print(f"Getting events for pod {pod} in namespace {namespace}")
        debug_print(f"Non-normal events only: {non_normal}")
        v1 = get_k8s_client()
        field_selector = f"involvedObject.name={pod}"
        if non_normal:
            field_selector += ",type!=Normal"
        debug_print(f"Using field selector: {field_selector}")
        events = v1.list_namespaced_event(
            namespace,
            field_selector=field_selector,
            limit=100,  # Limit to 100 events to improve performance
        )
        debug_print(f"Found {len(events.items)} events")
        return events
    except client.ApiException as e:
        debug_print(f"Error details while fetching events: {e}")
        console.print(f"Error fetching events: {e}")
        sys.exit(1)


# TODO: This use this instead of pod specific events
def get_abnormal_events(namespace: str) -> List[Dict[str, str]]:
    """Get list of abnormal events in the given namespace."""
    v1 = get_k8s_client()
    events = v1.list_namespaced_event(namespace, field_selector="type!=Normal")
    return [
        event
        for event in events.items
        if not is_resource_healthy(
            namespace, event.involved_object.name, event.involved_object.kind
        )
    ]


def get_failures(namespace: str) -> List[Dict[str, str]]:
    """Get list of things that failed to create in the given namespace."""
    current_time = time.time()
    debug_print(f"Getting failed items for namespace: {namespace}")

    # Check cache
    if namespace in failures_cache:
        cached_failures, cache_time = failures_cache[namespace]
        if current_time - cache_time < CACHE_DURATION:
            debug_print(f"Using cached failed items for namespace {namespace}")
            return cached_failures

    try:
        debug_print(f"Fetching fresh failed items data for namespace {namespace}")
        v1 = get_k8s_client()
        events = v1.list_namespaced_event(namespace)
        failed_items = []
        for event in events.items:
            if hasattr(event, "involved_object") and hasattr(
                event.involved_object, "name"
            ):
                debug_print(f"Processing event: {event.reason}")
                if "warning" in event.type.lower():
                    name = event.involved_object.name
                    kind = event.involved_object.kind
                    if not is_resource_healthy(namespace, name, kind):
                        debug_print(f"Found {event.reason}: {name} {kind} {namespace}")
                        failed_items.append(
                            {
                                "name": name,
                                "kind": kind,
                                "namespace": namespace,
                                "reason": event.reason,
                            }
                        )
            else:
                debug_print(f"Event without involved object: {event.metadata.name}")
                failed_items.append(
                    {
                        "name": event.metadata.name,
                        "kind": "Unknown",
                        "namespace": namespace,
                        "reason": event.reason,
                    }
                )

        debug_print(f"Found {len(failed_items)} failed items")
        # Update cache
        failures_cache[namespace] = (failed_items, current_time)
        return failed_items
    except Exception as e:
        debug_print(f"Error details while fetching failed items: {e}")
        console.print(
            f"""[red]Error fetching failed events in namespace '{namespace}':
            \n{str(e)}[/red]"""
        )
        return []


def get_all_events(
    namespace: str, non_normal: bool = False, show_timestamps: bool = False
) -> str:
    """Get all events in the namespace."""
    try:
        v1 = get_k8s_client()
        field_selector = None
        if non_normal:
            field_selector = "type!=Normal"
        events = v1.list_namespaced_event(
            namespace,
            field_selector=field_selector,
            limit=1000,  # Limit to 1000 events to improve performance
        )
        debug_print(f"Found {len(events.items)} events")
        return events
    except client.ApiException as e:
        console.print(f"Error fetching events: {e}")
        sys.exit(1)


def format_events(
    events, show_timestamps: bool = False, text_format: bool = False
) -> str:
    """Format events into a readable string with color."""
    if not events.items:
        return "[yellow]No events found[/yellow]"

    # Sort events by timestamp in ascending order (oldest first)
    # Handle None timestamps by putting them at the end
    from datetime import datetime, timezone

    def get_sort_key(event):
        # First try to use series.last_observed_time if available
        if (
            hasattr(event, "series")
            and event.series is not None
            and hasattr(event.series, "last_observed_time")
        ):
            debug_print(f"Event Series: {event.series}")
            if event.series.last_observed_time is None:
                return datetime.max.replace(tzinfo=timezone.utc)
            return event.series.last_observed_time
        # Fall back to last_timestamp if series is not available
        if event.last_timestamp is None:
            return datetime.max.replace(tzinfo=timezone.utc)
        if isinstance(event.last_timestamp, str):
            return datetime.strptime(
                event.last_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=timezone.utc)
        return event.last_timestamp

    sorted_events = sorted(events.items, key=get_sort_key)

    if text_format:
        output = []
        for event in sorted_events:

            # Format timestamp
            if show_timestamps:
                # Try to use series.last_observed_time first
                if (
                    hasattr(event, "series")
                    and event.series is not None
                    and hasattr(event.series, "last_observed_time")
                ):
                    timestamp = str(event.series.last_observed_time)
                else:
                    timestamp = str(event.last_timestamp)
            else:
                # Convert to relative time
                if (
                    hasattr(event, "series")
                    and event.series is not None
                    and hasattr(event.series, "last_observed_time")
                ):
                    if event.series.last_observed_time is None:
                        timestamp = "unknown time"
                        debug_print(
                            f"""Event 'unknown time':
                            \n{event.type} {event.series.last_observed_time}
                            \n{event.metadata.name} {timestamp}"""
                        )
                        continue
                    event_time = event.series.last_observed_time
                else:
                    if event.last_timestamp is None:
                        timestamp = "unknown time"
                        debug_print(
                            f"""Event 'unknown time':
                            \n{event.type} {event.last_timestamp}
                            \n{event.metadata.name} {timestamp}"""
                        )
                        continue
                    elif isinstance(event.last_timestamp, str):
                        event_time = datetime.strptime(
                            event.last_timestamp, "%Y-%m-%dT%H:%M:%SZ"
                        ).replace(tzinfo=timezone.utc)
                    else:
                        event_time = event.last_timestamp
                now = datetime.now(timezone.utc)
                delta = now - event_time

                if delta.days > 0:
                    timestamp = f"{delta.days}d ago"
                elif delta.seconds >= 3600:
                    hours = delta.seconds // 3600
                    timestamp = f"{hours}h ago"
                elif delta.seconds >= 60:
                    minutes = delta.seconds // 60
                    timestamp = f"{minutes}m ago"
                else:
                    timestamp = f"{delta.seconds}s ago"

            output.append(
                f"[cyan]{timestamp}[/cyan] "
                f"[yellow]{event.type}[/yellow] "
                f"[red]{event.reason}[/red] "
                f"[blue]{event.involved_object.kind}/{event.involved_object.name}[/blue] "
                f"[white]{event.message}[/white]"
            )
        return "\n".join(output)
    else:
        from rich.table import Table
        from rich.text import Text

        table = Table(
            show_header=True,
            header_style="bold magenta",
            box=rich.box.ROUNDED,
            show_lines=True,
            padding=(0, 1),
            border_style="white",
            style="dim",
        )
        table.add_column("Time", no_wrap=True, style="cyan")
        table.add_column("Type", no_wrap=True, style="yellow")
        table.add_column("Reason", no_wrap=True, style="red")
        table.add_column("Resource", no_wrap=True, style="blue")
        table.add_column("Message", style="white")

        for event in sorted_events:
            # Format timestamp
            if show_timestamps:
                if (
                    hasattr(event, "series")
                    and event.series is not None
                    and hasattr(event.series, "last_observed_time")
                ):
                    timestamp = str(event.series.last_observed_time)
                else:
                    timestamp = str(event.last_timestamp)
            else:
                if (
                    hasattr(event, "series")
                    and event.series is not None
                    and hasattr(event.series, "last_observed_time")
                ):
                    if event.series.last_observed_time is None:
                        timestamp = "unknown time"
                        continue
                    event_time = event.series.last_observed_time
                else:
                    if event.last_timestamp is None:
                        timestamp = "unknown time"
                        continue
                    elif isinstance(event.last_timestamp, str):
                        event_time = datetime.strptime(
                            event.last_timestamp, "%Y-%m-%dT%H:%M:%SZ"
                        ).replace(tzinfo=timezone.utc)
                    else:
                        event_time = event.last_timestamp
                now = datetime.now(timezone.utc)
                delta = now - event_time

                if delta.days > 0:
                    timestamp = f"{delta.days}d ago"
                elif delta.seconds >= 3600:
                    hours = delta.seconds // 3600
                    timestamp = f"{hours}h ago"
                elif delta.seconds >= 60:
                    minutes = delta.seconds // 60
                    timestamp = f"{minutes}m ago"
                else:
                    timestamp = f"{delta.seconds}s ago"

            table.add_row(
                Text(timestamp, style="cyan"),
                Text(event.type, style="yellow"),
                Text(event.reason, style="red"),
                Text(
                    f"{event.involved_object.kind}/{event.involved_object.name}",
                    style="blue",
                ),
                Text(event.message, style="white"),
            )

        console.print(table)
        return ""


def is_resource_healthy(namespace: str, name: str, kind: str) -> bool:
    """Check if a Kubernetes resource is healthy."""
    cache_key = f"{namespace}/{kind}/{name}"
    current_time = time.time()

    # Check cache first
    if cache_key in health_check_cache:
        cached_result, cache_time = health_check_cache[cache_key]
        if current_time - cache_time < CACHE_DURATION:
            debug_print(f"Using cached health check for {cache_key}")
            return cached_result

    debug_print(f"Checking health of {name} {kind} in namespace {namespace}")
    try:
        if kind == "ReplicaSet":
            debug_print(
                f"Checking health of ReplicaSet {name} in namespace {namespace}"
            )
            apps_v1 = get_k8s_apps_client()
            rs = apps_v1.read_namespaced_replica_set(name, namespace)
            is_healthy = False
            if rs.status.ready_replicas == rs.status.replicas:
                debug_print(f"ReplicaSet {name} in namespace {namespace} is healthy")
                is_healthy = True
            elif (
                hasattr(rs.status, "unavailable_replicas")
                and rs.status.unavailable_replicas == 0
            ):
                debug_print(
                    f"ReplicaSet {name} in namespace {namespace} unavailable_replicas=0"
                )
                is_healthy = True
            else:
                if (
                    hasattr(rs.metadata, "owner_references")
                    and rs.metadata.owner_references
                ):
                    debug_print(
                        f"ReplicaSet {name} in namespace {namespace} has owner references"
                    )
                    owner = rs.metadata.owner_references[0]
                    is_healthy = is_resource_healthy(namespace, owner.name, owner.kind)
                else:
                    debug_print(
                        f"""ReplicaSet {name} in namespace:
                        {namespace} has no owner references
                        \n{rs.metadata.owner_references}"""
                    )
                    is_healthy = False
        elif kind == "Deployment":
            debug_print(
                f"Checking health of Deployment {name} in namespace {namespace}"
            )
            apps_v1 = get_k8s_apps_client()
            deployment = apps_v1.read_namespaced_deployment(name, namespace)
            is_healthy = (
                deployment.status.unavailable_replicas == 0
                and deployment.status.ready_replicas == deployment.status.replicas
            )
        elif kind == "StatefulSet":
            debug_print(
                f"Checking health of StatefulSet {name} in namespace {namespace}"
            )
            apps_v1 = get_k8s_apps_client()
            sts = apps_v1.read_namespaced_stateful_set(name, namespace)
            is_healthy = sts.status.ready_replicas == sts.status.replicas
        elif kind == "Pod":
            debug_print(f"Checking health of Pod {name} in namespace {namespace}")
            v1 = get_k8s_client()
            pod = v1.read_namespaced_pod(name, namespace)
            is_healthy = pod.status.phase == "Running"
        else:
            debug_print(f"Unknown resource kind: {kind}, assuming unhealthy")
            is_healthy = False

        # Update cache
        health_check_cache[cache_key] = (is_healthy, current_time)
        return is_healthy
    except Exception as e:
        debug_print(f"Error checking health of {name} {kind}: {e}")
        if not hasattr(e, "status"):
            return True
        if e.status == 404:
            debug_print(f"Resource {name} {kind} not found, assuming deleted")
            return True
        debug_print(f"Error checking health of {name} {kind}: {e}")
        return False


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
    failures = get_failures(namespace)
    # Combine pod names and failed items
    pod_names = [pod["name"] for pod in pods]
    failure_names = [item["name"] for item in failures]
    all_items = pod_names + failure_names
    print(" ".join(all_items))
    sys.exit(0)


def display_menu(pods: List[Dict[str, str]]) -> None:
    """Display numbered menu of pods with color."""
    console.print("[cyan]Select a pod:[/cyan]")
    console.print("  [green]e[/green]) All abnormal events")
    console.print("  [green]a[/green]) All events")
    failed_items = get_failures(get_current_namespace())
    for i, pod in enumerate(pods, 1):
        # Check if the pod is a failed item
        failed_item = next(
            (item for item in failed_items if item["name"] == pod["name"]), None
        )
        if failed_item:
            console.print(
                f"[green]{i:3d}[/green]) {failed_item['kind']}/{pod['name']} [red]{failed_item['reason']}[/red]"  # noqa: E501
            )
        else:
            console.print(
                f"[green]{i:3d}[/green]) {pod['controller_kind']}/{pod['name']}"
            )
    console.print("  [green]Enter[/green]) exit")


def get_user_selection(max_value: int) -> int:
    """Get and validate user selection."""
    while True:
        try:
            selection = input("Enter selection: ")
            if not selection:  # Empty input means exit
                console.print("No selection made, exiting...")
                sys.exit(0)
            if selection == "a":
                return "a"
            if selection == "e":
                return "e"
            selection = int(selection)
            if 1 <= selection <= max_value:
                return selection
            console.print(
                f"""Invalid selection. Please enter a number between 1 and {max_value}
                or press Enter to exit"""
            )
        except ValueError:
            console.print("Please enter a valid number, a, e or press Enter to exit")
        except KeyboardInterrupt:
            console.print("Exiting...")
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
            if hasattr(event.involved_object, "kind"):
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


@lru_cache(maxsize=32)
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
        description="""View Kubernetes events\n
Suggested usage:
`kge -ea` to see all abnormal events
`source <(kge --completion=zsh)` to enable zsh completion for pods and namespaces""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("pod", nargs="?", help="Pod name to get events for")
    parser.add_argument("-n", "--namespace", help="Namespace to use")
    parser.add_argument(
        "-e",
        "--exceptions-only",
        action="store_true",
        help="Show only non-normal events",
    )
    parser.add_argument(
        "-a", "--all", action="store_true", help="Get all events in the namespace"
    )
    parser.add_argument("-k", "--kind", help="List all unique kinds from events")
    parser.add_argument(
        "--completion", choices=["zsh"], help="Output shell completion script"
    )
    parser.add_argument(
        "--install-completion", action="store_true", help="Install shell completion"
    )
    parser.add_argument(
        "-v", "--version", action="store_true", help="Show version information"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument(
        "--show-timestamps",
        action="store_true",
        help="Show absolute timestamps instead of relative times",
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="Display output in text format instead of table",
    )
    parser.add_argument("--complete-ns", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--complete-kind", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--complete-pod", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--complete-resource", action="store_true", help=argparse.SUPPRESS
    )

    args = parser.parse_args()

    # Set global debug flag
    global DEBUG
    DEBUG = args.debug

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
            completion_file = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "completion", "_kge"
            )
            with open(completion_file, "r") as f:
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
            console.print(f"[cyan]Getting events for {args.kind} {args.pod}[/cyan]")
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
                console.print(format_events(events, args.show_timestamps, args.text))
                sys.exit(0)
            except Exception as e:
                console.print(f"[red]Error getting events: {e}[/red]")
                sys.exit(1)
        # Otherwise, just list the kinds
        else:
            console.print("[cyan]Getting all unique kinds from events[/cyan]")
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
            console.print(format_events(events, args.show_timestamps, args.text))
            sys.exit(0)
        except Exception as e:
            console.print(f"[red]Error getting events: {e}[/red]")
            sys.exit(1)

    # Handle -a flag for all events
    if args.all:
        console.print("[cyan]Getting all events[/cyan]")
        console.print(f"[cyan]{'-' * 40}[/cyan]")
        try:
            events = get_all_events(
                namespace, args.exceptions_only, args.show_timestamps
            )
            console.print(format_events(events, args.show_timestamps, args.text))
            sys.exit(0)
        except Exception as e:
            console.print(f"[red]Error getting events: {e}[/red]")
            sys.exit(1)

    # Normal interactive execution
    pods, failures = get_menu_items(namespace)

    display_menu(pods)
    selection = get_user_selection(len(pods))

    if selection == "e":
        console.print("\n[cyan]Getting all non-normal events[/cyan]")
        console.print(f"[cyan]{'-' * 40}[/cyan]")
        try:
            events = get_all_events(
                namespace, non_normal=True, show_timestamps=args.show_timestamps
            )
            console.print(format_events(events, args.show_timestamps, args.text))
        except Exception as e:
            console.print(f"[red]Error getting events: {e}[/red]")
    elif selection == "a":
        console.print("\n[cyan]Getting all events[/cyan]")
        console.print(f"[cyan]{'-' * 40}[/cyan]")
        try:
            events = get_all_events(
                namespace, args.exceptions_only, show_timestamps=args.show_timestamps
            )
            console.print(format_events(events, args.show_timestamps, args.text))
        except Exception as e:
            console.print(f"[red]Error getting events: {e}[/red]")
    else:  # Events for specific pod
        selected_pod = pods[selection - 1]
        console.print(f"\n[cyan]Getting events for pod: {selected_pod['name']}[/cyan]")
        console.print(f"[cyan]{'-' * 40}[/cyan]")
        try:
            events = get_events_for_pod(
                namespace,
                selected_pod["name"],
                args.exceptions_only,
                show_timestamps=args.show_timestamps,
            )
            console.print(format_events(events, args.show_timestamps, args.text))
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
