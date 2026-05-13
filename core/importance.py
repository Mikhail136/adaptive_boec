from core.packet import CombatPacket, PacketType


class ImportanceScorer:
    def score(self, packet: CombatPacket) -> float:
        if packet.packet_type == PacketType.TARGET_COORDS:
            return 1.0

        if packet.packet_type == PacketType.FIRE_COMMAND:
            return 0.95

        if packet.packet_type == PacketType.UAV_TELEMETRY:
            return 0.75

        if packet.packet_type == PacketType.VIDEO_FRAME:
            return 0.55

        if packet.packet_type == PacketType.SENSOR_DATA:
            return 0.45

        if packet.packet_type == PacketType.SERVICE:
            return 0.2

        return 0.1