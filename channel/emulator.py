import random
from dataclasses import dataclass

from core.packet import CombatPacket


@dataclass(frozen=True)
class ChannelReport:
    delivered_packets: list[CombatPacket]
    dropped_by_bandwidth: list[CombatPacket]
    dropped_by_loss: list[CombatPacket]
    used_bandwidth: int
    bandwidth_bytes: int

    @property
    def utilization(self) -> float:
        if self.bandwidth_bytes <= 0:
            return 0.0
        return self.used_bandwidth / self.bandwidth_bytes


class ChannelEmulator:
    """
    Эмулятор ограниченного канала связи.

    bandwidth_bytes — сколько байт канал может передать за один цикл.
    loss_probability — вероятность случайной потери пакета.
    seed — фиксирует случайность для воспроизводимых экспериментов.
    """

    def __init__(self, bandwidth_bytes: int, loss_probability: float = 0.0, seed: int | None = None):
        if bandwidth_bytes <= 0:
            raise ValueError("bandwidth_bytes must be positive")
        if not 0.0 <= loss_probability <= 1.0:
            raise ValueError("loss_probability must be between 0.0 and 1.0")

        self.bandwidth_bytes = bandwidth_bytes
        self.loss_probability = loss_probability
        self._rng = random.Random(seed)

    def transmit_with_report(self, packets: list[CombatPacket]) -> ChannelReport:
        delivered: list[CombatPacket] = []
        dropped_by_bandwidth: list[CombatPacket] = []
        dropped_by_loss: list[CombatPacket] = []
        used_bandwidth = 0

        for packet in packets:
            packet_size = packet.size_compressed if packet.compressed else packet.size_raw

            if used_bandwidth + packet_size > self.bandwidth_bytes:
                dropped_by_bandwidth.append(packet)
                continue

            if self._rng.random() < self.loss_probability:
                dropped_by_loss.append(packet)
                continue

            delivered.append(packet)
            used_bandwidth += packet_size

        return ChannelReport(
            delivered_packets=delivered,
            dropped_by_bandwidth=dropped_by_bandwidth,
            dropped_by_loss=dropped_by_loss,
            used_bandwidth=used_bandwidth,
            bandwidth_bytes=self.bandwidth_bytes,
        )

    def transmit(self, packets: list[CombatPacket]) -> list[CombatPacket]:
        return self.transmit_with_report(packets).delivered_packets
