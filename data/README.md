# 📂 LCK Airport Knowledge Base — Source of Truth

This directory houses the **approved, authoritative knowledge corpus** for the **Chaudhary Charan Singh International Airport (LCK / VILK)** AI Assistant in Lucknow, India.

Under the closed-world knowledge policy, the AI Assistant is strictly restricted to facts contained within this corpus. If a passenger inquires about an unverified detail, unknown flight number, or missing amenity, the assistant must politely abstain and redirect the traveler.

---

## 📋 Document Inventory

All active documents are declaratively registered in [`manifest.json`](./manifest.json):

| Document ID | Source File | Description | Language |
|---|---|---|---|
| `terminals` | [`lck_airport/terminals.md`](./lck_airport/terminals.md) | Terminal 1, 2, and 3 layouts, airline allocations, walking times | English (`en`) |
| `gates` | [`lck_airport/gates.md`](./lck_airport/gates.md) | Gate concourses, boarding procedures, last-call rules | English (`en`) |
| `security` | [`lck_airport/security.md`](./lck_airport/security.md) | CISF screening rules, allowed liquids, electronics, baggage limits | English (`en`) |
| `transport` | [`lck_airport/transport.md`](./lck_airport/transport.md) | Lucknow Metro (Red Line), prepaid taxis, parking tariffs, shuttles | English (`en`) |
| `amenities` | [`lck_airport/amenities.md`](./lck_airport/amenities.md) | Lounges, prayer rooms, medical clinics, lost & found, Wi-Fi | English (`en`) |
| `hours` | [`lck_airport/hours.md`](./lck_airport/hours.md) | Terminal opening hours, inquiry desk schedules, helpline phones | English (`en`) |
| `faq` | [`lck_airport/faq.md`](./lck_airport/faq.md) | Concise spoken answers tailored for kiosk voice queries | English (`en`) |
| `gates-hi` | [`lck_airport/hi/gates.md`](./lck_airport/hi/gates.md) | गेट और बोर्डिंग नियम (Hindi translation of gates) | Hindi (`hi`) |
| `amenities-hi` | [`lck_airport/hi/amenities.md`](./lck_airport/hi/amenities.md) | प्रार्थना कक्ष, मेडिकल, खोया-पाया (Hindi translation) | Hindi (`hi`) |
| `faq-hi` | [`lck_airport/hi/faq.md`](./lck_airport/hi/faq.md) | छोटे बोले जाने वाले जवाब (Hindi FAQ) | Hindi (`hi`) |
| `gates-es` | [`lck_airport/es/gates.md`](./lck_airport/es/gates.md) | Puertas y último aviso (Spanish translation) | Spanish (`es`) |
| `amenities-es` | [`lck_airport/es/amenities.md`](./lck_airport/es/amenities.md) | Salas, médico, objetos perdidos (Spanish translation) | Spanish (`es`) |
| `faq-es` | [`lck_airport/es/faq.md`](./lck_airport/es/faq.md) | Respuestas cortas para hablar (Spanish FAQ) | Spanish (`es`) |

---

## 🚫 Excluded Files & Trap Benchmarks

Files registered under `"do_not_ingest"` in `manifest.json`:
* **[`unknown_traps.json`](./unknown_traps.json)**: Adversarial test suite of unanswerable and out-of-scope questions (fake flight statuses, legal advice, out-of-bounds gates) used to verify that the LLM abstains rather than hallucinating.
* **`README.md`**: Corpus documentation.
* **`manifest.json`**: Structural inventory file.

---

## ⚙️ How the Pipeline Consumes This Data

1. **Atomic Snapshot Activation**: On application startup or when calling `POST /api/v1/knowledge/refresh`, the backend validates paths against directory traversal attacks, compiles documents into memory, and tags the snapshot with an immutable version ID.
2. **OKF Processing**: Compiles all approved documents into a continuous Markdown context injected directly into the LLM system prompt.
3. **RAG Processing**: Splits documents into table-aware semantic chunks and indexes them into an in-memory **BM25 Lexical Index** with Reciprocal Rank Fusion (RRF).
