from core.packet import CombatPacket, PacketType


packet = CombatPacket(
    packet_id=1,
    packet_type=PacketType.TARGET_COORDS,
    timestamp_ms=1000,
    source="BPLA-1",
    payload={
        "target_id": "T-001",
        "lat": 55.751244,
        "lon": 37.618423,
        "confidence": 0.92,
    },
)

print(packet)