"""Small synthetic professional network with deterministic shortest paths and relevance."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

import networkx as nx

from backend.models.network import NetworkEdge, NetworkPerson
from backend.services.demo_data import load_people


class NetworkGraphService:
    def __init__(self) -> None:
        self.people = {person.id: person for person in load_people()}
        self.graph = nx.Graph()
        self.graph.add_node("INVESTOR_ROOT", name="You")
        for person in self.people.values():
            self.graph.add_node(person.id, name=person.name)
            if person.closeness_score >= 3:
                self.graph.add_edge(
                    "INVESTOR_ROOT", person.id,
                    relationship_type="KNOWS",
                    weight=float(person.closeness_score),
                )
        by_affiliation: dict[str, list[str]] = defaultdict(list)
        for person in self.people.values():
            affiliations = person.past_companies + person.alma_maters + [person.current_company]
            for affiliation in set(affiliations):
                by_affiliation[affiliation].append(person.id)
        for affiliation, ids in by_affiliation.items():
            for index, person_id in enumerate(ids):
                for other_id in ids[index + 1:]:
                    if not self.graph.has_edge(person_id, other_id):
                        self.graph.add_edge(
                            person_id, other_id,
                            relationship_type="COLLEAGUE_OF",
                            context_notes=f"Shared professional or education network: {affiliation}",
                        )

    def snapshot(self, center_node: str = "INVESTOR_ROOT", depth: int = 2) -> dict[str, Any]:
        if center_node not in self.graph:
            center_node = "INVESTOR_ROOT"
        depth = max(1, min(depth, 3))
        visible = set(nx.single_source_shortest_path_length(self.graph, center_node, cutoff=depth))
        nodes = [{
            "id": "INVESTOR_ROOT", "name": "You", "current_role": "Investor",
            "current_company": "Your network", "closeness_score": 5, "role_type": "investor",
            "past_companies": [], "alma_maters": [], "expertise_tags": [],
        }]
        nodes.extend(person.model_dump(mode="json") for pid, person in self.people.items() if pid in visible)
        edges = [
            NetworkEdge(
                source_id=left,
                target_id=right,
                relationship_type=data["relationship_type"],
                weight=float(data.get("weight", 1)),
                context_notes=data.get("context_notes"),
            ).model_dump()
            for left, right, data in self.graph.edges(data=True)
            if left in visible and right in visible
        ]
        return {"nodes": nodes, "edges": edges, "total_nodes": len(nodes), "total_edges": len(edges)}

    def query(
        self, query: str, company_focus: str | None = None,
        sector_focus: str | None = None, max_results: int = 5,
    ) -> list[dict[str, Any]]:
        terms = set((query + " " + (company_focus or "") + " " + (sector_focus or "")).lower().split())
        ranked = []
        for person in self.people.values():
            searchable = " ".join(
                [person.current_company, person.current_role, *person.expertise_tags, *person.past_companies]
            ).lower()
            overlap = [tag for tag in person.expertise_tags if any(word in tag.lower() for word in terms)]
            company_match = any(word in searchable for word in terms if len(word) > 3)
            score = len(overlap) * 4 + int(company_match) * 2 + person.closeness_score
            if score <= person.closeness_score:
                continue
            try:
                path = nx.shortest_path(self.graph, "INVESTOR_ROOT", person.id)
            except nx.NetworkXNoPath:
                continue
            ranked.append((score, person, path, overlap))
        ranked.sort(key=lambda result: (-result[0], len(result[2]), result[1].name))
        results = []
        for _, person, path, overlap in ranked[:max_results]:
            context = ", ".join(overlap) if overlap else person.current_company
            results.append({
                "person": person.model_dump(mode="json"),
                "relevance_reason": f"Synthetic contact with experience in {context}.",
                "path_from_investor": ["You", *[self.people[node].name for node in path[1:]]],
                "degree": min(len(path) - 1, 3),
                "suggested_icebreaker": f"Ask about their experience with {context}.",
            })
        return results

    def diligence(self, person_id: str) -> dict[str, Any] | None:
        person = self.people.get(person_id)
        if person is None:
            return None
        path = nx.shortest_path(self.graph, "INVESTOR_ROOT", person_id)
        return {
            "person": person.model_dump(mode="json"),
            "shortest_path_from_investor": ["You", *[self.people[node].name for node in path[1:]]],
            "degrees_of_separation": len(path) - 1,
            "common_alumni": person.alma_maters[:1],
            "common_past_employers": person.past_companies[:1],
            "talking_points": [
                f"Discuss their experience at {person.current_company}.",
                f"Explore their expertise in {person.expertise_tags[0]}.",
                "Confirm details directly; this profile is synthetic demo data.",
            ],
        }


network_service = NetworkGraphService()
