# NIA knowledge corpus — what you retrieve from

This folder is the **only** factual source your avatar may use. The airport is fictional. If a traveler asks something that is not in these files, your avatar says it does not know.

## What you do with these files

1. Read them. Gate C22, the prayer room, and lost-and-found are the demo facts.
2. Write an ingest script that indexes **only** the paths in [`manifest.json`](./manifest.json) into ChromaDB.
3. Do **not** ingest [`unknown_traps.json`](./unknown_traps.json). Use that file to test refusals.
4. Wire `search_airport(query)` to that index. Path A: Nova Sonic calls this tool. Path B: your code calls it after Wispr transcribes, before Kokoro speaks. Either way, no factual answer without this tool.

Hindi and Spanish pages translate the English facts. Do not add a gate, time, or phone number that is missing from the English files.

| File | What it covers |
|---|---|
| [`nia_airport/terminals.md`](./nia_airport/terminals.md) | T1 / T2 / T3, airlines, walking times |
| [`nia_airport/gates.md`](./nia_airport/gates.md) | Gate → terminal, food, last-call (includes **C22**) |
| [`nia_airport/security.md`](./nia_airport/security.md) | Liquids, laptops, family lane — not visa law |
| [`nia_airport/transport.md`](./nia_airport/transport.md) | Metro, taxi, car park, hotel shuttle |
| [`nia_airport/amenities.md`](./nia_airport/amenities.md) | Prayer room, medical, lost & found, wifi |
| [`nia_airport/hours.md`](./nia_airport/hours.md) | Desk hours, last metro, phones |
| [`nia_airport/faq.md`](./nia_airport/faq.md) | Short answers meant to be spoken |
| [`nia_airport/hi/`](./nia_airport/hi/) | Hindi — same facts, not new facts |
| [`nia_airport/es/`](./nia_airport/es/) | Spanish — same facts, not new facts |
| [`unknown_traps.json`](./unknown_traps.json) | Questions your avatar must **refuse** |
