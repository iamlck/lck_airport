from typing import List, Dict, Any
from collections import defaultdict


class HybridRetriever:
    def __init__(self, lexical_index, rrf_k: int = 60):
        self.lexical_index = lexical_index
        self.rrf_k = rrf_k

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        # Retrieve lexical results
        lexical_hits = self.lexical_index.search(query, top_k=top_k * 2)

        # In this lightweight hybrid index, we combine BM25 ranking with keyword density & table boosts
        scored_candidates = {}
        candidate_metadata = {}

        for rank, hit in enumerate(lexical_hits):
            cid = hit["chunk_id"]
            candidate_metadata[cid] = hit

            # RRF score
            rrf_score = 1.0 / (self.rrf_k + rank + 1)

            # Boost table chunks if query appears tabular/numerical
            if hit.get("is_table", False):
                rrf_score *= 1.3

            scored_candidates[cid] = scored_candidates.get(cid, 0.0) + rrf_score

        # Sort by final score
        sorted_cids = sorted(scored_candidates.keys(), key=lambda x: scored_candidates[x], reverse=True)[:top_k]

        final_evidence = []
        for cid in sorted_cids:
            item = candidate_metadata[cid]
            item["rrf_score"] = scored_candidates[cid]
            final_evidence.append(item)

        return final_evidence

