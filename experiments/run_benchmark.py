from adapters.mixed_stream_generator import MixedStreamGenerator
from adapters.telemetry_adapter import TelemetryAdapter

from channel.emulator import ChannelEmulator

from core.compression import CompressionController
from core.importance import ImportanceScorer
from core.metrics import calculate_metrics
from core.packet import PacketType
from core.scheduler import PriorityScheduler


def prepare_packets(packets):
    scorer = ImportanceScorer()
    compressor = CompressionController()
    telemetry_adapter = TelemetryAdapter()

    prepared = []

    for packet in packets:
        packet.priority = scorer.score(packet)

        if packet.packet_type in [PacketType.TARGET_COORDS, PacketType.UAV_TELEMETRY]:
            packet = telemetry_adapter.pack(packet)
        else:
            packet = compressor.compress(packet)

        prepared.append(packet)

    return prepared


def run_one_experiment(count: int, bandwidth_bytes: int, seed: int):
    generator = MixedStreamGenerator(seed=seed)
    scheduler = PriorityScheduler()

    packets = generator.generate(count=count)
    prepared_packets = prepare_packets(packets)

    channel = ChannelEmulator(
        bandwidth_bytes=bandwidth_bytes,
        loss_probability=0.0,
    )

    normal_delivered = channel.transmit(prepared_packets)
    priority_delivered = channel.transmit(scheduler.schedule(prepared_packets))

    normal_metrics = calculate_metrics(prepared_packets, normal_delivered)
    priority_metrics = calculate_metrics(prepared_packets, priority_delivered)

    return normal_metrics, priority_metrics


def main():
    experiments = [
        (100, 1800),
        (300, 5000),
        (500, 8000),
        (1000, 15000),
    ]

    print("count,bandwidth,normal_delivery,adaptive_delivery,normal_critical,adaptive_critical,normal_ratio,adaptive_ratio")

    for count, bandwidth in experiments:
        normal, adaptive = run_one_experiment(
            count=count,
            bandwidth_bytes=bandwidth,
            seed=42,
        )

        print(
            f"{count},"
            f"{bandwidth},"
            f"{normal['delivery_rate']:.3f},"
            f"{adaptive['delivery_rate']:.3f},"
            f"{normal['critical_delivery_rate']:.3f},"
            f"{adaptive['critical_delivery_rate']:.3f},"
            f"{normal['compression_ratio']:.3f},"
            f"{adaptive['compression_ratio']:.3f}"
        )


if __name__ == "__main__":
    main()