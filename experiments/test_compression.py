from core.packet import CombatPacket, PacketType
from core.importance import ImportanceScorer
from core.compression import CompressionController


scorer = ImportanceScorer()
compressor = CompressionController()

packets = [
    CombatPacket(
        1,
        PacketType.TARGET_COORDS,
        1000,
        "BPLA-1",
        {
            "target_id": "T-001",
            "lat": 55.751244,
            "lon": 37.618423,
            "confidence": 0.92,
        },
    ),
    CombatPacket(
        2,
        PacketType.SERVICE,
        1010,
        "BPLA-1",
        {
            "cpu_temp": 46,
            "voltage": 12.4,
            "status": "normal",
            "debug": "background service data repeated repeated repeated",
        },
    ),
]

for packet in packets:
    packet.priority = scorer.score(packet)
    packet = compressor.compress(packet)

    ratio = packet.size_raw / packet.size_compressed

    print("ID:", packet.packet_id)
    print("TYPE:", packet.packet_type.value)
    print("PRIORITY:", packet.priority)
    print("RAW:", packet.size_raw)
    print("COMPRESSED:", packet.size_compressed)
    print("RATIO:", round(ratio, 2), "x")
    print("COMPRESSED:", packet.compressed)
    print("-" * 30)