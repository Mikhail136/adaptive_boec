from core.packet import CombatPacket, PacketType
from core.importance import ImportanceScorer
from core.scheduler import PriorityScheduler


scorer = ImportanceScorer()
scheduler = PriorityScheduler()

packets = [
    CombatPacket(1, PacketType.SERVICE, 1000, "BPLA-1", {"temp": 45}),
    CombatPacket(2, PacketType.VIDEO_FRAME, 1010, "BPLA-1", {"frame": "image_data"}),
    CombatPacket(3, PacketType.TARGET_COORDS, 1020, "BPLA-1", {"target_id": 1}),
    CombatPacket(4, PacketType.UAV_TELEMETRY, 1030, "BPLA-1", {"alt": 1200}),
    CombatPacket(5, PacketType.FIRE_COMMAND, 1040, "HQ", {"command": "observe"}),
]

for packet in packets:
    packet.priority = scorer.score(packet)

scheduled = scheduler.schedule(packets)

print("Очередь отправки:")
for packet in scheduled:
    print(packet.packet_id, packet.packet_type.value, packet.priority)