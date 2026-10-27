from lck_backend.strategies.base import KnowledgeStrategy
from lck_backend.strategies.okf import OKFStrategy
from lck_backend.strategies.rag import RAGStrategy


class StrategyFactory:
    def __init__(self):
        self._okf = OKFStrategy()
        self._rag = RAGStrategy()

    def get_strategy(self, name: str) -> KnowledgeStrategy:
        if name.lower() == "rag":
            return self._rag
        return self._okf


strategy_factory = StrategyFactory()

