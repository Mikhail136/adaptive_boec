from core.packet import CombatPacket


class PriorityScheduler:
    """
    Планировщик отправки пакетов.
    Чем выше priority, тем раньше пакет уйдёт в канал.
    """

    def schedule(self, packets: list[CombatPacket]) -> list[CombatPacket]:
        return sorted(
            packets,
            key=lambda packet: packet.priority,
            reverse=True,
        )