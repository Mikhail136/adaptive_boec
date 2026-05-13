from collections import Counter

from adapters.mixed_stream_generator import MixedStreamGenerator


generator = MixedStreamGenerator()
packets = generator.generate(count=100)

type_counter = Counter(packet.packet_type.value for packet in packets)
source_counter = Counter(packet.source for packet in packets)

print("Всего пакетов:", len(packets))

print("\nПо типам:")
for key, value in type_counter.items():
    print(key, value)

print("\nПо источникам:")
for key, value in source_counter.items():
    print(key, value)

print("\nПервые 10 пакетов:")
for packet in packets[:10]:
    print(packet.packet_id, packet.source, packet.packet_type.value, packet.payload)