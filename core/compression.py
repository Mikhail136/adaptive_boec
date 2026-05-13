import json
import zlib

from core.packet import CombatPacket


class CompressionController:
    def compress(self, packet: CombatPacket) -> CombatPacket:
        raw_bytes = json.dumps(packet.payload, ensure_ascii=False).encode("utf-8")
        packet.size_raw = len(raw_bytes)

        if packet.priority >= 0.9:
            level = 1
        elif packet.priority >= 0.5:
            level = 6
        else:
            level = 9

        compressed_bytes = zlib.compress(raw_bytes, level)

        packet.payload = compressed_bytes
        packet.size_compressed = len(compressed_bytes)
        packet.compressed = True

        return packet