from kge.cli.main import KubeEventsInteractiveSelector
from datetime import datetime, timezone


def test_initial_menu_load():
    # Create a mock grouped data with no events
    mock_grouped_data = {}

    # Create the selector with mock data
    selector = KubeEventsInteractiveSelector(mock_grouped_data)

    # Get the initial list content
    content = selector._get_list_content()

    # Verify that the content is a FormattedText object
    assert content is not None

    # Verify that the content contains the expected message for no events
    content_str = str(content)
    assert "No event groups to display" in content_str


def test_initial_menu_with_events():
    # Create mock grouped data with one event
    mock_grouped_data = {
        "test-event": {
            "events": [
                {
                    "namespace": "default",
                    "involved_object_name": "test-pod",
                    "involved_object_kind": "Pod",
                    "reason": "TestReason",
                    "message": "Test message",
                    "first_timestamp": None,
                    "last_timestamp": None,
                    "api_version": "v1",
                    "type": "Normal",
                    "count": 1,
                    "involved_object_uid": "test-uid",
                }
            ],
            "owner_info": {
                "kind": "Pod",
                "name": "test-pod",
                "namespace": "default",
                "uid": "test-uid",
            },
            "latest_event_timestamp": datetime.now(timezone.utc),
            "latest_event_type": "Normal",
            "latest_event_reason": "TestReason",
        }
    }

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
