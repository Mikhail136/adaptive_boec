from collections.abc import Iterable

from core.packet import CombatPacket, PacketType


class DeduplicationController:
    """
    Убирает повторяющиеся низко- и среднеприоритетные сообщения.

    Критические пакеты не удаляются: для демонстрационной системы безопаснее
    передать повтор критического сообщения, чем случайно потерять важное событие.
    """

    def deduplicate(self, packets: Iterable[CombatPacket]) -> list[CombatPacket]:
        result: list[CombatPacket] = []
        seen_keys: set[tuple] = set()

        for packet in packets:
            if packet.priority >= 0.9:
                result.append(packet)
                continue

            key = self._packet_key(packet)
            if key in seen_keys:
                continue

            seen_keys.add(key)
            result.append(packet)

        return result

    def _packet_key(self, packet: CombatPacket) -> tuple:
        payload_key = repr(sorted(packet.payload.items())) if isinstance(packet.payload, dict) else repr(packet.payload)
        return (packet.packet_type, packet.source, payload_key)


class TelemetryAggregator:
    """
    Прореживает частую телеметрию БПЛА.

    Идея демонстрации: при перегрузке канала нет смысла передавать каждую
    похожую телеметрическую точку. Оставляем каждую N-ю и последние данные
    по источнику, чтобы оператор видел актуальное состояние.
    """

    def __init__(self, keep_every: int = 3):
        if keep_every <= 0:
            raise ValueError("keep_every must be positive")
        self.keep_every = keep_every

    def aggregate(self, packets: Iterable[CombatPacket]) -> list[CombatPacket]:
        result: list[CombatPacket] = []
        telemetry_counters: dict[str, int] = {}
        latest_by_source: dict[str, CombatPacket] = {}

        for packet in packets:
            if packet.packet_type != PacketType.UAV_TELEMETRY:
                result.append(packet)
                continue

            count = telemetry_counters.get(packet.source, 0) + 1
            telemetry_counters[packet.source] = count
            latest_by_source[packet.source] = packet

            if count % self.keep_every == 1:
                result.append(packet)

        existing_ids = {packet.packet_id for packet in result}
        for packet in latest_by_source.values():
            if packet.packet_id not in existing_ids:
                result.append(packet)

        return sorted(result, key=lambda packet: packet.timestamp_ms)
