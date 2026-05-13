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


def print_metrics(title, metrics):
    print("\n" + title)
    print("-" * 50)
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"{key}: {value:.3f}")
        else:
            print(f"{key}: {value}")


def main():
    generator = MixedStreamGenerator(seed=42)
    scheduler = PriorityScheduler()

    packets = generator.generate(count=100)
    prepared_packets = prepare_packets(packets)

    channel = ChannelEmulator(
        bandwidth_bytes=1800,
        loss_probability=0.0,
    )

    normal_delivered = channel.transmit(prepared_packets)
    priority_delivered = channel.transmit(scheduler.schedule(prepared_packets))

    normal_metrics = calculate_metrics(prepared_packets, normal_delivered)
    priority_metrics = calculate_metrics(prepared_packets, priority_delivered)

    print_metrics("Обычная отправка", normal_metrics)
    print_metrics("АДАПТИВ-БОЕЦ: приоритетная отправка", priority_metrics)


if __name__ == "__main__":
    main()