from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_agent(client: AsyncClient) -> None:
    payload = {
        "name": "Researcher",
        "type": "LLM",
        "provider": "anthropic",
        "model": "claude-sonnet-4-6",
        "system_prompt": "You are a researcher.",
    }
    r = await client.post("/api/v1/agents", json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["name"] == "Researcher"
    assert body["type"] == "LLM"
    agent_id = body["id"]

    r2 = await client.get(f"/api/v1/agents/{agent_id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == agent_id


@pytest.mark.asyncio
async def test_list_agents_empty(client: AsyncClient) -> None:
    r = await client.get("/api/v1/agents")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_update_and_delete_agent(client: AsyncClient) -> None:
    r = await client.post("/api/v1/agents", json={"name": "A"})
    aid = r.json()["id"]

    r2 = await client.patch(f"/api/v1/agents/{aid}", json={"name": "B"})
    assert r2.status_code == 200
    assert r2.json()["name"] == "B"

    r3 = await client.delete(f"/api/v1/agents/{aid}")
    assert r3.status_code == 204

    r4 = await client.get(f"/api/v1/agents/{aid}")
    assert r4.status_code == 404
