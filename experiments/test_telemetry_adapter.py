from adapters.telemetry_adapter import TelemetryAdapter
from core.packet import CombatPacket, PacketType


adapter = TelemetryAdapter()

target_packet = CombatPacket(
    packet_id=1,
    packet_type=PacketType.TARGET_COORDS,
    timestamp_ms=1000,
    source="BPLA-1",
    payload={
        "target_id": 1,
        "lat": 55.751244,
        "lon": 37.618423,
        "confidence": 0.92,
    },
)

telemetry_packet = CombatPacket(
    packet_id=2,
    packet_type=PacketType.UAV_TELEMETRY,
    timestamp_ms=1010,
    source="BPLA-1",
    payload={
        "alt": 1200,
        "speed": 85,
        "battery": 76,
        "rssi": -67,
    },
)

for packet in [target_packet, telemetry_packet]:
    packed = adapter.pack(packet)

    ratio = packed.size_raw / packed.size_compressed

    print("ID:", packed.packet_id)
    print("TYPE:", packed.packet_type.value)
    print("RAW:", packed.size_raw)
    print("PACKED:", packed.size_compressed)
    print("RATIO:", round(ratio, 2), "x")
    print("BYTES:", packed.payload)
    print("-" * 30)