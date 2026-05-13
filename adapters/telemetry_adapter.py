import struct

from core.packet import CombatPacket, PacketType


class TelemetryAdapter:
    """
    Упаковка координат и телеметрии в компактный бинарный формат.
    """

    def pack_target_coords(self, packet: CombatPacket) -> CombatPacket:
        payload = packet.payload

        target_id = int(payload["target_id"])
        lat = int(payload["lat"] * 1_000_000)
        lon = int(payload["lon"] * 1_000_000)
        confidence = int(payload["confidence"] * 100)

        raw_text = str(payload).encode("utf-8")
        packet.size_raw = len(raw_text)

        packed = struct.pack(
            "<i i i B",
            target_id,
            lat,
            lon,
            confidence,
        )

        packet.payload = packed
        packet.size_compressed = len(packed)
        packet.compressed = True

        return packet

    def pack_uav_telemetry(self, packet: CombatPacket) -> CombatPacket:
        payload = packet.payload

        alt = int(payload["alt"])
        speed = int(payload["speed"])
        battery = int(payload["battery"])
        rssi = int(payload["rssi"])

        raw_text = str(payload).encode("utf-8")
        packet.size_raw = len(raw_text)

        packed = struct.pack(
            "<h h B b",
            alt,
            speed,
            battery,
            rssi,
        )

        packet.payload = packed
        packet.size_compressed = len(packed)
        packet.compressed = True

        return packet

    def pack(self, packet: CombatPacket) -> CombatPacket:
        if packet.packet_type == PacketType.TARGET_COORDS:
            return self.pack_target_coords(packet)

        if packet.packet_type == PacketType.UAV_TELEMETRY:
            return self.pack_uav_telemetry(packet)

        return packet