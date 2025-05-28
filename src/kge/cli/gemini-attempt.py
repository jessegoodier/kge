import sys
import argparse
import kubernetes
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.text import Text
import rich.box

console = Console()


@dataclass
class KubernetesEvent:
    """Represents a Kubernetes event with all relevant information."""

    namespace: str
    involved_object_name: str
    involved_object_kind: str
    reason: str
    message: str
    first_timestamp: Optional[datetime]
    last_timestamp: Optional[datetime]
    api_version: Optional[str]
    type: str
    count: int

    @classmethod
    def from_v1_event(cls, event: Any) -> "KubernetesEvent":
        """Create a KubernetesEvent from a V1Event object."""
        return cls(
            namespace=event.metadata.namespace,
            involved_object_name=event.involved_object.name,
            involved_object_kind=event.involved_object.kind,
            reason=event.reason,
            message=event.message,
            first_timestamp=event.first_timestamp,
            last_timestamp=event.last_timestamp,
            api_version=event.involved_object.api_version,
            type=event.type,
            count=event.count,
        )

    def to_dict(self) -> Dict:
        """Convert the event to a dictionary."""
        return {
            "namespace": self.namespace,
            "involved_object_name": self.involved_object_name,
            "involved_object_kind": self.involved_object_kind,
            "reason": self.reason,
            "message": self.message,
            "first_timestamp": (
                self.first_timestamp.isoformat() if self.first_timestamp else None
            ),
            "last_timestamp": (
                self.last_timestamp.isoformat() if self.last_timestamp else None
            ),
            "api_version": self.api_version,
            "type": self.type,
            "count": self.count,
        }


class KubernetesEventManager:
    """Manages Kubernetes events fetching and processing."""

    def __init__(self):
        self._init_kubernetes_client()

    def _init_kubernetes_client(self):
        """Initialize the Kubernetes client with proper configuration."""
        try:
            # First try to load in-cluster config
            kubernetes.config.load_incluster_config()
            console.print("[green]Using in-cluster configuration[/green]")
        except kubernetes.config.ConfigException:
            try:
                # Then try to load from kubeconfig
                kubernetes.config.load_kube_config()
                console.print("[green]Using kubeconfig configuration[/green]")
            except kubernetes.config.ConfigException:
                console.print("[red]Could not configure Kubernetes client.[/red]")
                console.print(
                    "[yellow]Please ensure you have a valid kubeconfig file or are running in-cluster.[/yellow]"
                )
                console.print(
                    "[yellow]You can set KUBECONFIG environment variable to specify a custom kubeconfig path.[/yellow]"
                )
                raise Exception(
                    "Could not configure Kubernetes client. "
                    "Ensure you have a valid kubeconfig or are running in-cluster."
                )

        self.v1 = kubernetes.client.CoreV1Api()

    def fetch_events(self, namespace: Optional[str] = None) -> List[KubernetesEvent]:
        """Fetches events from the specified namespace."""
        try:
            if namespace:
                console.print(
                    f"[cyan]Fetching events for namespace: {namespace}[/cyan]"
                )
                events = self.v1.list_namespaced_event(namespace=namespace, watch=False)
            else:
                console.print("[cyan]Fetching events for all namespaces[/cyan]")
                events = self.v1.list_event_for_all_namespaces(watch=False)

            return [KubernetesEvent.from_v1_event(event) for event in events.items]
        except Exception as e:
            console.print(f"[red]Error fetching events: {e}[/red]")
            return []

    def filter_events(
        self,
        events: List[KubernetesEvent],
        reason_filter: Optional[str] = None,
        kind_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
    ) -> List[KubernetesEvent]:
        """Filters events based on specified criteria."""
        filtered_events = events

        if reason_filter:
            filtered_events = [e for e in filtered_events if e.reason == reason_filter]
        if kind_filter:
            filtered_events = [
                e for e in filtered_events if e.involved_object_kind == kind_filter
            ]
        if type_filter:
            filtered_events = [e for e in filtered_events if e.type == type_filter]

        return filtered_events

    def display_events_table(
        self, events: List[KubernetesEvent], show_timestamps: bool = False
    ):
        """Displays events in a Rich table format."""
        if not events:
            console.print("[yellow]No events found.[/yellow]")
            return

        table = Table(
            show_header=True,
            header_style="bold magenta",
            box=rich.box.ROUNDED,
            show_lines=True,
            padding=(0, 1),
            border_style="white",
            style="dim",
        )

        # Add columns
        table.add_column("Time", no_wrap=True, style="cyan")
        table.add_column("Type", no_wrap=True, style="yellow")
        table.add_column("Reason", no_wrap=True, style="red")
        table.add_column("Resource", no_wrap=True, style="blue")
        table.add_column("Message", style="white")

        # Sort events by timestamp
        sorted_events = sorted(
            events,
            key=lambda x: x.last_timestamp or datetime.max.replace(tzinfo=timezone.utc),
        )

        for event in sorted_events:
            # Format timestamp
            if show_timestamps:
                timestamp = (
                    str(event.last_timestamp)
                    if event.last_timestamp
                    else "unknown time"
                )
            else:
                if event.last_timestamp is None:
                    timestamp = "unknown time"
                else:
                    now = datetime.now(timezone.utc)
                    delta = now - event.last_timestamp

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
                    f"{event.involved_object_kind}/{event.involved_object_name}",
                    style="blue",
                ),
                Text(event.message, style="white"),
            )

        console.print(table)


def main():
    parser = argparse.ArgumentParser(
        description="View Kubernetes events with a beautiful TUI"
    )
    parser.add_argument("-n", "--namespace", help="Namespace to fetch events from")
    parser.add_argument("-r", "--reason", help="Filter events by reason")
    parser.add_argument("-k", "--kind", help="Filter events by kind")
    parser.add_argument("-t", "--type", help="Filter events by type")
    parser.add_argument(
        "--show-timestamps",
        action="store_true",
        help="Show absolute timestamps instead of relative times",
    )

    args = parser.parse_args()

    try:
        event_manager = KubernetesEventManager()
        events = event_manager.fetch_events(args.namespace)
        filtered_events = event_manager.filter_events(
            events,
            reason_filter=args.reason,
            kind_filter=args.kind,
            type_filter=args.type,
        )
        event_manager.display_events_table(filtered_events, args.show_timestamps)
    except KeyboardInterrupt:
        console.print("\nExiting gracefully...")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
