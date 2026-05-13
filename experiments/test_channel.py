from core.packet import CombatPacket, PacketType
from core.importance import ImportanceScorer
from core.scheduler import PriorityScheduler
from channel.emulator import ChannelEmulator


scorer = ImportanceScorer()
scheduler = PriorityScheduler()

packets = [
    CombatPacket(1, PacketType.SERVICE, 1000, "BPLA-1", {"temp": 45}, size_raw=30),
    CombatPacket(2, PacketType.VIDEO_FRAME, 1010, "BPLA-1", {"frame": "image_data"}, size_raw=80),
    CombatPacket(3, PacketType.TARGET_COORDS, 1020, "BPLA-1", {"target_id": 1}, size_raw=20),
    CombatPacket(4, PacketType.UAV_TELEMETRY, 1030, "BPLA-1", {"alt": 1200}, size_raw=30),
    CombatPacket(5, PacketType.FIRE_COMMAND, 1040, "HQ", {"command": "observe"}, size_raw=20),
]

for packet in packets:
    packet.priority = scorer.score(packet)

channel = ChannelEmulator(
    bandwidth_bytes=70,
    loss_probability=0.0,
)

print("Обычная отправка:")
delivered_normal = channel.transmit(packets)
for packet in delivered_normal:
    print(packet.packet_id, packet.packet_type.value, packet.priority)

print("\nПриоритетная отправка:")
scheduled = scheduler.schedule(packets)
delivered_priority = channel.transmit(scheduled)
for packet in delivered_priority:
    print(packet.packet_id, packet.packet_type.value, packet.priority)