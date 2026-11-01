"""engine/events/__init__.py

Normalized Workflow Event Models & Deterministic Output Parsers.
Agrees directly with Remotion WorkflowStateTransition and TimelineMapper contracts.
"""

from .event_model import (
    WorkflowAction,
    NormalizedEvent,
    WorkflowEntity,
    validate_event_sequence,
    parse_structured_execution_events,
)

__all__ = [
    "WorkflowAction",
    "NormalizedEvent",
    "WorkflowEntity",
    "validate_event_sequence",
    "parse_structured_execution_events",
]

