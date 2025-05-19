import json

from rustic_ai.core.agents.testutils import EchoAgent
from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.core.guild.dsl import AgentSpec, GuildSpec


def test_update_guild_status(client):
    agent1: AgentSpec = AgentBuilder(EchoAgent).set_name("Agent1").set_description("First agent").build_spec()

    guild_spec = GuildSpec(
        name="TestGuild",
        description="A guild for status update testing",
        properties={
            "storage": {
                "class": "rustic_ai.core.messaging.storage.InMemoryStorage",
                "properties": {},
            }
        },
        agents=[agent1],
    )
    json_data = guild_spec.model_dump_json()
    data = json.loads(json_data)
    post_response = client.post("/api/guilds", json=data, headers={"Content-Type": "application/json"})

    assert post_response.status_code == 201
    assert "id" in post_response.json()

    guild_id = post_response.json()["id"]

    get_response = client.get(f"/api/guilds/{guild_id}")
    assert get_response.status_code == 200
    assert get_response.json().get("status") == "active"

    update_response = client.patch(
        f"/api/guilds/{guild_id}/status", json={"status": "stopped"}, headers={"Content-Type": "application/json"}
    )

    assert update_response.status_code == 200
    assert update_response.json().get("status") == "stopped"

    get_updated_response = client.get(f"/api/guilds/{guild_id}")
    assert get_updated_response.status_code == 200
    assert get_updated_response.json().get("status") == "stopped"

    update_response = client.patch(
        f"/api/guilds/{guild_id}/status", json={"status": "archived"}, headers={"Content-Type": "application/json"}
    )

    assert update_response.status_code == 200
    assert update_response.json().get("status") == "archived"

    get_archived_response = client.get(f"/api/guilds/{guild_id}")
    assert get_archived_response.status_code == 200
    assert get_archived_response.json().get("status") == "archived"


def test_update_guild_status_invalid_guild_id(client):
    update_data = {"status": "stopped"}
    response = client.patch(
        "/api/guilds/nonexistent_guild_id/status", json=update_data, headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 404


def test_update_guild_status_invalid_status(client):
    agent1: AgentSpec = AgentBuilder(EchoAgent).set_name("Agent1").set_description("First agent").build_spec()

    guild_spec = GuildSpec(
        name="TestGuild2",
        description="Another guild for testing invalid status",
        properties={
            "storage": {
                "class": "rustic_ai.core.messaging.storage.InMemoryStorage",
                "properties": {},
            }
        },
        agents=[agent1],
    )
    json_data = guild_spec.model_dump_json()
    data = json.loads(json_data)
    post_response = client.post("/api/guilds", json=data, headers={"Content-Type": "application/json"})

    assert post_response.status_code == 201
    guild_id = post_response.json()["id"]

    update_data = {"status": "invalid_status"}
    response = client.patch(
        f"/api/guilds/{guild_id}/status", json=update_data, headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 400
