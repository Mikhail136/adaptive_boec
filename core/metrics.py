from core.packet import CombatPacket


def is_critical(packet: CombatPacket) -> bool:
    return packet.priority >= 0.9


def calculate_metrics(
    total_packets: list[CombatPacket],
    delivered_packets: list[CombatPacket],
) -> dict:
    total_count = len(total_packets)
    delivered_count = len(delivered_packets)

    total_critical = [p for p in total_packets if is_critical(p)]
    delivered_critical = [p for p in delivered_packets if is_critical(p)]

    raw_size = sum(p.size_raw for p in total_packets)
    sent_size = sum(
        p.size_compressed if p.compressed else p.size_raw
        for p in delivered_packets
    )

    return {
        "total_packets": total_count,
        "delivered_packets": delivered_count,
        "delivery_rate": delivered_count / total_count if total_count else 0,

        "total_critical": len(total_critical),
        "delivered_critical": len(delivered_critical),
        "critical_delivery_rate": (
            len(delivered_critical) / len(total_critical)
            if total_critical else 0
        ),

        "raw_size": raw_size,
        "sent_size": sent_size,
        "compression_ratio": raw_size / sent_size if sent_size else 0,
    }