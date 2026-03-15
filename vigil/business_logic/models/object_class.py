from enum import Enum


class ObjectClass(str, Enum):
    """Supported object classes for detection and tracking."""

    PERSON = "person"
    VEHICLE = "vehicle"
