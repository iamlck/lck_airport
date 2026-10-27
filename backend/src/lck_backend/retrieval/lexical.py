from typing import List, Dict, Any
from rank_bm25 import BM25Okapi


class LexicalIndex:
    def __init__(self, chunks: List[Dict[str, Any]]):
        self.chunks = chunks
        self.corpus = [c["text"].lower().split() for c in chunks]
        self.bm25 = BM25Okapi(self.corpus) if self.corpus else None

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.bm25 or not self.chunks:
            return []
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for rank, idx in enumerate(ranked_indices):
            if scores[idx] > 0.0:
                item = dict(self.chunks[idx])
                item["bm25_score"] = float(scores[idx])
                item["bm25_rank"] = rank + 1
                results.append(item)
        return results

