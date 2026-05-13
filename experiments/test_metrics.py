from core.packet import CombatPacket, PacketType
from core.importance import ImportanceScorer
from core.scheduler import PriorityScheduler
from core.metrics import calculate_metrics
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

normal_delivered = channel.transmit(packets)
priority_delivered = channel.transmit(scheduler.schedule(packets))

normal_metrics = calculate_metrics(packets, normal_delivered)
priority_metrics = calculate_metrics(packets, priority_delivered)

print("Обычная отправка:")
for key, value in normal_metrics.items():
    print(key, "=", round(value, 3) if isinstance(value, float) else value)

print("\nПриоритетная отправка:")
for key, value in priority_metrics.items():
    print(key, "=", round(value, 3) if isinstance(value, float) else value)