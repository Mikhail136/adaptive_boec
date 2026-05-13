from core.packet import CombatPacket, PacketType
from core.importance import ImportanceScorer
from core.compression import CompressionController
from core.scheduler import PriorityScheduler
from core.metrics import calculate_metrics
from channel.emulator import ChannelEmulator
from adapters.telemetry_adapter import TelemetryAdapter


scorer = ImportanceScorer()
compressor = CompressionController()
telemetry_adapter = TelemetryAdapter()
scheduler = PriorityScheduler()


def create_packets():
    return [
        CombatPacket(
            1,
            PacketType.SERVICE,
            1000,
            "BPLA-1",
            {"cpu_temp": 45, "status": "normal", "debug": "system check"},
        ),
        CombatPacket(
            2,
            PacketType.VIDEO_FRAME,
            1010,
            "BPLA-1",
            {"frame_id": 1, "data": "background_frame_data" * 10},
        ),
        CombatPacket(
            3,
            PacketType.TARGET_COORDS,
            1020,
            "BPLA-1",
            {
                "target_id": 1,
                "lat": 55.751244,
                "lon": 37.618423,
                "confidence": 0.92,
            },
        ),
        CombatPacket(
            4,
            PacketType.UAV_TELEMETRY,
            1030,
            "BPLA-1",
            {"alt": 1200, "speed": 85, "battery": 76, "rssi": -67},
        ),
        CombatPacket(
            5,
            PacketType.FIRE_COMMAND,
            1040,
            "HQ",
            {"command": "observe", "sector": "A3"},
        ),
        CombatPacket(
            6,
            PacketType.SENSOR_DATA,
            1050,
            "SENSOR-1",
            {"motion": True, "temperature": 18, "noise": "low"},
        ),
    ]


def prepare_packets(packets):
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
    print("-" * 40)
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"{key}: {value:.3f}")
        else:
            print(f"{key}: {value}")


def print_delivered(title, packets):
    print("\n" + title)
    print("-" * 40)
    for packet in packets:
        size = packet.size_compressed if packet.compressed else packet.size_raw
        print(
            f"ID={packet.packet_id} | "
            f"{packet.packet_type.value} | "
            f"priority={packet.priority} | "
            f"size={size} bytes"
        )


def main():
    packets = create_packets()
    prepared_packets = prepare_packets(packets)

    channel = ChannelEmulator(
        bandwidth_bytes=120,
        loss_probability=0.0,
    )

    normal_delivered = channel.transmit(prepared_packets)

    priority_queue = scheduler.schedule(prepared_packets)
    priority_delivered = channel.transmit(priority_queue)

    normal_metrics = calculate_metrics(prepared_packets, normal_delivered)
    priority_metrics = calculate_metrics(prepared_packets, priority_delivered)

    print_delivered("Обычная отправка", normal_delivered)
    print_metrics("Метрики обычной отправки", normal_metrics)

    print_delivered("Приоритетная отправка", priority_delivered)
    print_metrics("Метрики приоритетной отправки", priority_metrics)


if __name__ == "__main__":
    main()