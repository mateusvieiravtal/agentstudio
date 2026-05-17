from __future__ import annotations

from collections import defaultdict, deque
from typing import Any


class CycleError(Exception):
    """Raised when a pipeline graph contains a cycle."""


class PipelineGraph:
    """Adjacency-list view of a pipeline's nodes/edges."""

    def __init__(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None:
        self.nodes: dict[str, dict[str, Any]] = {n["id"]: n for n in nodes}
        self.edges: list[dict[str, Any]] = list(edges)

        self.adj: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.indeg: dict[str, int] = {nid: 0 for nid in self.nodes}
        for e in edges:
            src, tgt = e["source"], e["target"]
            if src not in self.nodes or tgt not in self.nodes:
                continue
            self.adj[src].append(e)
            self.indeg[tgt] = self.indeg.get(tgt, 0) + 1

    def topological_sort(self) -> list[str]:
        indeg = dict(self.indeg)
        queue: deque[str] = deque(nid for nid, d in indeg.items() if d == 0)
        order: list[str] = []
        while queue:
            nid = queue.popleft()
            order.append(nid)
            for edge in self.adj.get(nid, []):
                tgt = edge["target"]
                indeg[tgt] -= 1
                if indeg[tgt] == 0:
                    queue.append(tgt)
        if len(order) != len(self.nodes):
            raise CycleError("pipeline graph contains a cycle")
        return order

    def successors(self, node_id: str) -> list[dict[str, Any]]:
        return list(self.adj.get(node_id, []))

    def roots(self) -> list[str]:
        return [nid for nid, d in self.indeg.items() if d == 0]
