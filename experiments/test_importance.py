from core.packet import CombatPacket, PacketType
from core.importance import ImportanceScorer


scorer = ImportanceScorer()

packets = [
    CombatPacket(1, PacketType.TARGET_COORDS, 1000, "BPLA-1", {"target": "T-001"}),
    CombatPacket(2, PacketType.FIRE_COMMAND, 1010, "HQ", {"command": "observe"}),
    CombatPacket(3, PacketType.UAV_TELEMETRY, 1020, "BPLA-1", {"alt": 1200}),
    CombatPacket(4, PacketType.VIDEO_FRAME, 1030, "BPLA-1", {"frame": "demo"}),
    CombatPacket(5, PacketType.SERVICE, 1040, "BPLA-1", {"temp": 45}),
]

for packet in packets:
    packet.priority = scorer.score(packet)
    print(packet.packet_id, packet.packet_type.value, packet.priority)