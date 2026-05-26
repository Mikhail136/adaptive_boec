from adapters.mixed_stream_generator import MixedStreamGenerator
from adapters.telemetry_adapter import TelemetryAdapter
from channel.emulator import ChannelEmulator
from core.compression import CompressionController
from core.deduplication import DeduplicationController, TelemetryAggregator
from core.importance import ImportanceScorer
from core.metrics import calculate_metrics
from core.packet import CombatPacket, PacketType
from core.scheduler import PriorityScheduler


def test_importance_orders_critical_packets_highest():
    scorer = ImportanceScorer()
    target = CombatPacket(1, PacketType.TARGET_COORDS, 100, "BPLA", {"target_id": 1})
    service = CombatPacket(2, PacketType.SERVICE, 200, "BPLA", {"status": "ok"})

    assert scorer.score(target) > scorer.score(service)
    assert scorer.score(target) >= 0.9


def test_compression_sets_sizes_and_flag():
    packet = CombatPacket(1, PacketType.SERVICE, 100, "NODE", {"status": "normal", "log": "abc" * 20})
    packet.priority = 0.2

    compressed = CompressionController().compress(packet)

    assert compressed.compressed is True
    assert compressed.size_raw > 0
    assert compressed.size_compressed > 0


def test_telemetry_adapter_packs_uav_telemetry():
    packet = CombatPacket(
        1,
        PacketType.UAV_TELEMETRY,
        100,
        "BPLA",
        {"alt": 1200, "speed": 90, "battery": 80, "rssi": -70},
    )

    packed = TelemetryAdapter().pack(packet)

    assert packed.compressed is True
    assert packed.size_compressed == 6


def test_scheduler_prioritizes_high_priority_packets():
    low = CombatPacket(1, PacketType.SERVICE, 100, "A", {}, priority=0.2)
    high = CombatPacket(2, PacketType.TARGET_COORDS, 200, "A", {}, priority=1.0)

    scheduled = PriorityScheduler().schedule([low, high])

    assert scheduled[0] == high


def test_channel_report_accounts_for_bandwidth_drops():
    packets = [
        CombatPacket(1, PacketType.SERVICE, 100, "A", {}, size_raw=100),
        CombatPacket(2, PacketType.SERVICE, 200, "A", {}, size_raw=100),
    ]
    channel = ChannelEmulator(bandwidth_bytes=100, loss_probability=0.0, seed=1)

    report = channel.transmit_with_report(packets)

    assert len(report.delivered_packets) == 1
    assert len(report.dropped_by_bandwidth) == 1
    assert report.used_bandwidth == 100


def test_deduplication_preserves_critical_duplicates():
    p1 = CombatPacket(1, PacketType.TARGET_COORDS, 100, "A", {"x": 1}, priority=1.0)
    p2 = CombatPacket(2, PacketType.TARGET_COORDS, 200, "A", {"x": 1}, priority=1.0)
    s1 = CombatPacket(3, PacketType.SERVICE, 300, "A", {"status": "ok"}, priority=0.2)
    s2 = CombatPacket(4, PacketType.SERVICE, 400, "A", {"status": "ok"}, priority=0.2)

    result = DeduplicationController().deduplicate([p1, p2, s1, s2])

    assert result == [p1, p2, s1]


def test_telemetry_aggregation_keeps_latest_packet():
    packets = [
        CombatPacket(i, PacketType.UAV_TELEMETRY, i * 100, "BPLA", {"alt": i}, priority=0.75)
        for i in range(1, 6)
    ]

    result = TelemetryAggregator(keep_every=3).aggregate(packets)

    assert result[-1].packet_id == 5
    assert len(result) < len(packets)


def test_end_to_end_metrics_are_stable():
    generator = MixedStreamGenerator(seed=42)
    scorer = ImportanceScorer()
    compressor = CompressionController()

    packets = generator.generate(count=20)
    prepared = []
    for packet in packets:
        packet.priority = scorer.score(packet)
        prepared.append(compressor.compress(packet))

    delivered = PriorityScheduler().schedule(prepared)[:10]
    metrics = calculate_metrics(prepared, delivered)

    assert metrics["total_packets"] == 20
    assert metrics["delivered_packets"] == 10
    assert metrics["raw_size"] > 0
