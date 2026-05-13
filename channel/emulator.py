import random

from core.packet import CombatPacket


class ChannelEmulator:
    """
    Эмулятор канала связи.

    bandwidth_bytes — сколько байт канал может передать за один цикл.
    loss_probability — вероятность случайной потери пакета.
    """

    def __init__(self, bandwidth_bytes: int, loss_probability: float):
        self.bandwidth_bytes = bandwidth_bytes
        self.loss_probability = loss_probability

    def transmit(self, packets: list[CombatPacket]) -> list[CombatPacket]:
        delivered = []
        used_bandwidth = 0

        for packet in packets:
            packet_size = packet.size_compressed if packet.compressed else packet.size_raw

            if used_bandwidth + packet_size > self.bandwidth_bytes:
                continue

            if random.random() < self.loss_probability:
                continue

            delivered.append(packet)
            used_bandwidth += packet_size

        return delivered