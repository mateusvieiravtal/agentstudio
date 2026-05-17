from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_pipeline_with_two_agents(client: AsyncClient) -> None:
    a = (await client.post("/api/v1/agents", json={"name": "A"})).json()
    b = (await client.post("/api/v1/agents", json={"name": "B"})).json()

    payload = {
        "name": "Pipe1",
        "description": "two agents in sequence",
        "nodes": [
            {"id": "n1", "agent_id": a["id"], "position": {"x": 0, "y": 0}},
            {"id": "n2", "agent_id": b["id"], "position": {"x": 200, "y": 0}},
        ],
        "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
    }
    r = await client.post("/api/v1/pipelines", json=payload)
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    r2 = await client.get(f"/api/v1/pipelines/{pid}")
    assert r2.status_code == 200
    body = r2.json()
    assert len(body["nodes"]) == 2
    assert len(body["edges"]) == 1
    assert body["edges"][0]["source"] == "n1"
    assert body["edges"][0]["target"] == "n2"


@pytest.mark.asyncio
async def test_update_pipeline(client: AsyncClient) -> None:
    r = await client.post("/api/v1/pipelines", json={"name": "P"})
    pid = r.json()["id"]

    r2 = await client.patch(
        f"/api/v1/pipelines/{pid}",
        json={"description": "updated"},
    )
    assert r2.status_code == 200
    assert r2.json()["description"] == "updated"


@pytest.mark.asyncio
async def test_delete_pipeline(client: AsyncClient) -> None:
    r = await client.post("/api/v1/pipelines", json={"name": "P"})
    pid = r.json()["id"]
    r2 = await client.delete(f"/api/v1/pipelines/{pid}")
    assert r2.status_code == 204
    r3 = await client.get(f"/api/v1/pipelines/{pid}")
    assert r3.status_code == 404
