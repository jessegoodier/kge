import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from kge.cli.main import KubeEventsInteractiveSelector, KubernetesEvent


def make_grouped_data(
    uid: str, name: str, timestamp: datetime
) -> Dict[str, Dict[str, Any]]:
    return {
        uid: {
            "events": [
                {
                    "namespace": "default",
                    "involved_object_name": name,
                    "involved_object_kind": "Pod",
                    "reason": "TestReason",
                    "message": "Test message",
                    "first_timestamp": None,
                    "last_timestamp": None,
                    "api_version": "v1",
                    "type": "Normal",
                    "count": 1,
                    "involved_object_uid": uid,
                }
            ],
            "owner_info": {
                "kind": "Pod",
                "name": name,
                "namespace": "default",
                "uid": uid,
            },
            "latest_event_timestamp": timestamp,
            "latest_event_type": "Normal",
            "latest_event_reason": "TestReason",
        }
    }


class FakeEventManager:
    def __init__(self, grouped_response: Dict[str, Dict[str, Any]]) -> None:
        self.grouped_response = grouped_response
        self.fetch_namespace: Optional[str] = None
        self.group_sort_direction: Optional[str] = None

    def fetch_events(self, namespace: Optional[str] = None) -> List[KubernetesEvent]:
        self.fetch_namespace = namespace
        if not self.grouped_response:
            return []
        return [
            KubernetesEvent(
                namespace="default",
                involved_object_name="test-pod",
                involved_object_kind="Pod",
                reason="TestReason",
                message="Test message",
                first_timestamp=None,
                last_timestamp=None,
                api_version="v1",
                type="Normal",
                count=1,
                involved_object_uid="test-uid",
            )
        ]

    def group_events_by_owner(
        self, events: List[KubernetesEvent], sort_direction: str = "asc"
    ) -> Dict[str, Dict[str, Any]]:
        self.group_sort_direction = sort_direction
        return self.grouped_response


def test_initial_menu_load() -> None:
    # Create a mock grouped data with no events
    mock_grouped_data: Dict[str, Dict[str, Any]] = {}

    # Create the selector with mock data
    selector = KubeEventsInteractiveSelector(mock_grouped_data)

    # Get the initial list content
    content = selector._get_list_content()

    # Verify that the content is a FormattedText object
    assert content is not None

    # Verify that the content contains the expected message for no events
    content_str = str(content)
    assert "No event groups to display" in content_str


def test_initial_menu_with_events() -> None:
    # Create mock grouped data with one event
    mock_grouped_data = make_grouped_data(
        "test-event", "test-pod", datetime.now(timezone.utc)
    )

    # Create the selector with mock data
    selector = KubeEventsInteractiveSelector(mock_grouped_data)

    # Get the initial list content
    content = selector._get_list_content()

    # Verify that the content is a FormattedText object
    assert content is not None

    # Verify that the content contains the event information
    content_str = str(content)
    assert "test-pod" in content_str
    assert "TestReason" in content_str


def test_refresh_data_clears_empty_result() -> None:
    selector = KubeEventsInteractiveSelector(
        grouped_data=make_grouped_data(
            "test-event", "test-pod", datetime.now(timezone.utc)
        ),
        event_manager=FakeEventManager({}),
        namespace="default",
    )

    asyncio.run(selector._refresh_data())

    assert selector.grouped_data == {}
    assert selector.sorted_owner_uids == []
    assert selector.selected_index == 0


def test_refresh_data_preserves_selection_for_existing_owner() -> None:
    older = datetime(2026, 1, 1, tzinfo=timezone.utc)
    newer = datetime(2026, 1, 2, tzinfo=timezone.utc)
    initial_data = {
        **make_grouped_data("older-uid", "older-pod", older),
        **make_grouped_data("newer-uid", "newer-pod", newer),
    }
    refreshed_data = {
        **make_grouped_data("newer-uid", "newer-pod", newer),
        **make_grouped_data("older-uid", "older-pod", older),
    }
    selector = KubeEventsInteractiveSelector(
        grouped_data=initial_data,
        event_manager=FakeEventManager(refreshed_data),
        namespace="default",
        sort_direction="asc",
    )

    asyncio.run(selector._refresh_data())

    assert selector.sorted_owner_uids[selector.selected_index] == "newer-uid"
