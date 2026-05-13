from dataclasses import dataclass
from enum import Enum
from typing import Any


class PacketType(Enum):
    TARGET_COORDS = "target_coords"
    FIRE_COMMAND = "fire_command"
    UAV_TELEMETRY = "uav_telemetry"
    VIDEO_FRAME = "video_frame"
    SENSOR_DATA = "sensor_data"
    SERVICE = "service"


@dataclass
class CombatPacket:
    packet_id: int
    packet_type: PacketType
    timestamp_ms: int
    source: str
    payload: Any
    priority: float = 0.0
    compressed: bool = False
    size_raw: int = 0
    size_compressed: int = 0