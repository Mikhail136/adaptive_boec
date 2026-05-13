import random

from core.packet import CombatPacket, PacketType


class MixedStreamGenerator:
    """
    Генератор смешанного боевого информационного потока.

    Имитирует несколько источников:
    - БПЛА
    - радиостанция
    - наземный сенсор
    - командный пункт
    """

    def __init__(self, seed: int = 42):
        random.seed(seed)

    def generate(self, count: int = 500) -> list[CombatPacket]:
        packets = []

        for packet_id in range(1, count + 1):
            timestamp_ms = packet_id * 100

            source_type = random.choices(
                population=["BPLA", "RADIO", "SENSOR", "HQ"],
                weights=[0.45, 0.20, 0.20, 0.15],
                k=1,
            )[0]

            if source_type == "BPLA":
                packet = self._generate_bpla_packet(packet_id, timestamp_ms)

            elif source_type == "RADIO":
                packet = self._generate_radio_packet(packet_id, timestamp_ms)

            elif source_type == "SENSOR":
                packet = self._generate_sensor_packet(packet_id, timestamp_ms)

            else:
                packet = self._generate_hq_packet(packet_id, timestamp_ms)

            packets.append(packet)

        return packets

    def _generate_bpla_packet(self, packet_id: int, timestamp_ms: int) -> CombatPacket:
        packet_type = random.choices(
            population=[
                PacketType.UAV_TELEMETRY,
                PacketType.VIDEO_FRAME,
                PacketType.TARGET_COORDS,
                PacketType.SERVICE,
            ],
            weights=[0.45, 0.40, 0.05, 0.10],
            k=1,
        )[0]

        if packet_type == PacketType.UAV_TELEMETRY:
            payload = {
                "alt": random.randint(500, 3000),
                "speed": random.randint(60, 160),
                "battery": random.randint(20, 100),
                "rssi": random.randint(-95, -45),
            }

        elif packet_type == PacketType.VIDEO_FRAME:
            payload = {
                "frame_id": packet_id,
                "data": "video_background_data_" * random.randint(10, 40),
            }

        elif packet_type == PacketType.TARGET_COORDS:
            payload = {
                "target_id": random.randint(1, 20),
                "lat": 55.0 + random.random(),
                "lon": 37.0 + random.random(),
                "confidence": round(random.uniform(0.75, 0.99), 2),
            }

        else:
            payload = {
                "cpu_temp": random.randint(35, 75),
                "status": "normal",
                "debug": "bpla_service_log",
            }

        return CombatPacket(packet_id, packet_type, timestamp_ms, "BPLA-1", payload)

    def _generate_radio_packet(self, packet_id: int, timestamp_ms: int) -> CombatPacket:
        packet_type = random.choices(
            population=[
                PacketType.FIRE_COMMAND,
                PacketType.SERVICE,
            ],
            weights=[0.20, 0.80],
            k=1,
        )[0]

        if packet_type == PacketType.FIRE_COMMAND:
            payload = {
                "command": random.choice(["observe", "hold", "move"]),
                "sector": random.choice(["A1", "A2", "B1", "B2"]),
            }
        else:
            payload = {
                "radio_status": "ok",
                "noise_level": random.randint(1, 10),
            }

        return CombatPacket(packet_id, packet_type, timestamp_ms, "RADIO-1", payload)

    def _generate_sensor_packet(self, packet_id: int, timestamp_ms: int) -> CombatPacket:
        packet_type = random.choices(
            population=[
                PacketType.SENSOR_DATA,
                PacketType.SERVICE,
            ],
            weights=[0.65, 0.35],
            k=1,
        )[0]

        payload = {
            "motion": random.choice([True, False]),
            "temperature": random.randint(-10, 35),
            "noise": random.choice(["low", "medium", "high"]),
        }

        return CombatPacket(packet_id, packet_type, timestamp_ms, "SENSOR-1", payload)

    def _generate_hq_packet(self, packet_id: int, timestamp_ms: int) -> CombatPacket:
        packet_type = random.choices(
            population=[
                PacketType.FIRE_COMMAND,
                PacketType.SERVICE,
            ],
            weights=[0.35, 0.65],
            k=1,
        )[0]

        if packet_type == PacketType.FIRE_COMMAND:
            payload = {
                "command": random.choice(["observe", "hold", "move"]),
                "priority_note": "hq_control",
            }
        else:
            payload = {
                "hq_status": "sync",
                "operator": "control_node",
            }

        return CombatPacket(packet_id, packet_type, timestamp_ms, "HQ", payload)