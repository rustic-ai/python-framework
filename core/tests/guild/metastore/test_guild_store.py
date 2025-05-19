import pytest

from rustic_ai.core.agents.testutils.echo_agent import EchoAgent
from rustic_ai.core.guild.builders import AgentBuilder, GuildBuilder
from rustic_ai.core.guild.dsl import AgentSpec, DependencySpec
from rustic_ai.core.guild.metastore.database import Metastore
from rustic_ai.core.guild.metastore.guild_store import GuildStore
from rustic_ai.core.guild.metastore.models import GuildModel, GuildStatus
from rustic_ai.core.messaging.core.message import (
    AgentTag,
    FunctionalTransformer,
    PayloadTransformer,
    RoutingDestination,
    RoutingRule,
    RoutingSlip,
)


class TestGuildStore:

    @pytest.fixture
    def engine(self):
        Metastore.drop_db(True)
        Metastore.initialize_engine("sqlite:///rustic_store_test.db")
        yield Metastore.get_engine()
        Metastore.drop_db(True)

    @pytest.fixture
    def guild(self):
        return self._get_guild("guild1")

    @pytest.fixture
    def agent(self):
        return self._get_agent("agent1")

    def _get_agent(self, name):
        return AgentBuilder(EchoAgent).set_name(name).set_description(name).build_spec()

    def _get_guild(self, name):
        return GuildBuilder(name).set_name(name).set_description(name).build_spec()

    def test_add_guild(self, engine, guild):
        store = GuildStore(engine)
        gm1 = store.add_guild(guild)
        assert gm1.id == "guild1"
        guild = store.get_guild(gm1.id)
        assert guild.id == "guild1"

    def test_update_guild_status(self, engine, guild):
        store = GuildStore(engine)
        guild_model = store.add_guild(guild)
        assert guild_model.status.value == "active"  

        store.update_guild_status(guild.id, GuildStatus.STOPPED)

        updated_guild = store.get_guild(guild.id)
        assert updated_guild is not None
        assert updated_guild.status.value == "stopped"

        store.update_guild_status(guild.id, GuildStatus.ARCHIVED)
        updated_guild = store.get_guild(guild.id)
        assert updated_guild.status.value == "archived"

        with pytest.raises(ValueError):
            store.update_guild_status("nonexistent_guild", GuildStatus.ACTIVE)

    def test_list_guilds(self, engine, guild):
        store = GuildStore(engine)
        store.add_guild(guild)
        store.add_guild(self._get_guild("guild2"))
        guilds = store.list_guilds()
        assert len(guilds) == 2

        assert guilds[0].id == "guild1"
        assert guilds[1].id == "guild2"

    def test_remove_guild(self, engine, guild):
        store = GuildStore(engine)
        store.add_guild(guild)
        store.remove_guild(guild.id)
        guild = store.get_guild(guild.id)
        assert guild is None

    def test_add_agent(self, engine, guild, agent):
        store = GuildStore(engine)
        store.add_guild(guild)
        store.add_agent(guild.id, agent)

        agent2 = self._get_agent("agent2")
        store.add_agent(guild.id, agent2)

        guild = store.get_guild(guild.id)

        assert len(guild.agents) == 2
        assert guild.agents[0].name == "agent1"
        assert guild.agents[1].name == "agent2"

        agent1 = store.get_agent(guild.id, agent.id)

        assert agent1 is not None
        assert agent1.name == "agent1"

    def test_get_guild_none(self, engine):
        store = GuildStore(engine)
        guild = store.get_guild("test_guild")
        assert guild is None

    def test_get_guilds_none(self, engine):
        store = GuildStore(engine)
        guilds = store.list_guilds()
        assert guilds == []

    def test_remove_guild_none(self, engine, guild):
        store = GuildStore(engine)
        store.add_guild(guild)
        gm = store.get_guild(guild.id)

        assert gm is not None

        assert gm.id == guild.id

        store.remove_guild(guild.id)
        guild = store.get_guild(guild.id)

        assert guild is None

    def test_remove_agent(self, engine, guild, agent):
        store = GuildStore(engine)

        store.add_guild(guild)
        store.add_agent(guild.id, agent)

        gm = store.get_guild(guild.id)

        assert gm is not None

        assert len(gm.agents) == 1
        assert gm.agents[0].name == "agent1"

        store.remove_agent(guild.id, agent.id)

        gm = store.get_guild(guild.id)

        assert gm is not None

        assert len(gm.agents) == 0

    def test_remove_agent_none(self, engine):
        store = GuildStore(engine)
        with pytest.raises(ValueError):
            store.remove_agent("test_guild", "test_agent")

    def test_remove_agent_guild_none(self, engine, guild):

        store = GuildStore(engine)
        store.add_guild(guild)

        with pytest.raises(ValueError):
            store.remove_agent(guild.id, "test_agent")

    def test_list_agents(self, engine, guild, agent):
        store = GuildStore(engine)
        store.add_guild(guild)

        agent2 = self._get_agent("agent2")
        store.add_agent(guild.id, agent)
        store.add_agent(guild.id, agent2)

        agents = store.list_agents(guild.id)

        assert len(agents) == 2
        assert agents[0].name == "agent1"

        assert agents[1].name == "agent2"

    def test_model_from_spec(self):
        spec = GuildBuilder("guild1").set_name("guild1").set_description("guild1").build_spec()
        gm = GuildModel.from_guild_spec(spec)

        assert gm.id == "guild1"
        assert gm.name == "guild1"
        assert gm.description == "guild1"

        assert gm.execution_engine == "rustic_ai.core.guild.execution.sync.sync_exec_engine.SyncExecutionEngine"
        assert gm.backend_module == "rustic_ai.core.messaging.backend"
        assert gm.backend_class == "InMemoryMessagingBackend"
        assert gm.backend_config == {}

    def test_model_with_routing_rules(self, engine):
        guild_id = "guild_with_routing"

        spec = (
            GuildBuilder(guild_id)
            .set_name("guild1")
            .set_description("guild1")
            .set_routes(
                routes=RoutingSlip(
                    steps=[
                        RoutingRule(
                            agent=AgentTag(id="test_agent01", name="test_agent01"),
                            method_name="test_method01",
                            destination=RoutingDestination(topics="new_test_topic"),
                            transformer=PayloadTransformer(
                                expression="$",
                                output_format="test_message_format",
                            ),
                        )
                    ]
                )
            )
            .add_route(
                route=RoutingRule(
                    agent=AgentTag(id="test", name="Test Agent"),
                    destination=RoutingDestination(
                        topics="test_topic",
                        recipient_list=[AgentTag(id="agent2", name="Agent 002")],
                    ),
                )
            )
            .add_route(
                route=RoutingRule(
                    agent=AgentTag(id="test_agent_02", name="Test Agent"),
                    transformer=PayloadTransformer(
                        output_format="test_message_format2",
                    ),
                )
            )
            .add_route(
                route=RoutingRule(
                    agent=AgentTag(id="test_agent_03", name="Test Agent"),
                    transformer=FunctionalTransformer(
                        handler="{'payload': {'new_key': payload.key, 'origin_id': $.origin.id}}",
                    ),
                )
            )
            .build_spec()
        )

        store = GuildStore(engine)
        store.add_guild(spec)

        guild_model = store.get_guild(guild_id)

        assert guild_model is not None
        guild = guild_model.to_guild_spec()

        assert guild is not None
        assert guild.id == guild_id
        assert guild.name == "guild1"
        assert guild.description == "guild1"

        assert guild.routes is not None
        assert len(guild.routes.steps) == 4

        rule01 = guild.routes.steps[0]

        assert rule01 is not None
        assert rule01.method_name == "test_method01"
        assert rule01.destination is not None
        assert rule01.destination.topics == "new_test_topic"
        assert rule01.transformer is not None
        assert isinstance(rule01.transformer, PayloadTransformer)
        assert rule01.transformer.expression == "$"
        assert rule01.transformer.output_format == "test_message_format"

        rule02 = guild.routes.steps[1]

        assert rule02 is not None
        assert rule02.agent is not None
        assert rule02.agent.id == "test"
        assert rule02.agent.name == "Test Agent"
        assert rule02.destination is not None
        assert rule02.destination.topics == "test_topic"
        assert len(rule02.destination.recipient_list) == 1
        assert rule02.destination.recipient_list[0].id == "agent2"
        assert rule02.destination.recipient_list[0].name == "Agent 002"

        rule03 = guild.routes.steps[2]

        assert rule03 is not None
        assert rule03.agent is not None
        assert rule03.agent.id == "test_agent_02"
        assert rule03.agent.name == "Test Agent"
        assert rule03.transformer is not None
        assert isinstance(rule03.transformer, PayloadTransformer)
        assert rule03.transformer.output_format == "test_message_format2"

        rule04 = guild.routes.steps[3]

        assert rule04 is not None
        assert rule04.agent is not None
        assert rule04.agent.id == "test_agent_03"
        assert rule04.agent.name == "Test Agent"
        assert rule04.transformer is not None
        assert isinstance(rule04.transformer, FunctionalTransformer)
        assert rule04.transformer.handler == "{'payload': {'new_key': payload.key, 'origin_id': $.origin.id}}"

    def test_model_with_dependencies(self, engine):
        guild_id = "guild_with_deps"

        builder = (
            GuildBuilder(guild_id)
            .set_name("guild1")
            .set_description("guild1")
            .set_dependency_map(
                {
                    "test_dep_01": DependencySpec(
                        class_name="test_dep01",
                        properties={"test_dep": "test_dep_value1"},
                    )
                }
            )
            .add_dependency_resolver(
                "test_dep_02",
                DependencySpec(class_name="test_dep02", properties={"test_dep": "test_dep_value2"}),
            )
        )

        agent: AgentSpec = (
            AgentBuilder(EchoAgent)
            .set_name("test_agent")
            .set_description("test_agent")
            .set_dependency_map(
                {
                    "test_dep_03": DependencySpec(
                        class_name="test_dep03",
                        properties={"test_dep": "test_dep_value3"},
                    )
                }
            )
            .add_dependency_resolver(
                "test_dep_04",
                DependencySpec(class_name="test_dep04", properties={"test_dep": "test_dep_value4"}),
            )
            .build_spec()
        )

        spec = builder.build_spec()

        store = GuildStore(engine)
        store.add_guild(spec)
        store.add_agent(guild_id, agent)

        guild_model = store.get_guild(guild_id)

        assert guild_model is not None

        gs = guild_model.to_guild_spec()

        assert gs.id == guild_id
        assert gs.name == "guild1"
        assert gs.description == "guild1"

        assert len(gs.dependency_map) == 2
        gdmap = gs.dependency_map

        assert "test_dep_01" in gdmap
        assert "test_dep_02" in gdmap

        d1 = gdmap["test_dep_01"]
        d2 = gdmap["test_dep_02"]

        assert d1.class_name == "test_dep01"
        assert d1.properties == {"test_dep": "test_dep_value1"}

        assert d2.class_name == "test_dep02"
        assert d2.properties == {"test_dep": "test_dep_value2"}

        agent_spec = gs.agents[0]

        assert len(agent_spec.dependency_map) == 2
        admap = agent_spec.dependency_map

        assert "test_dep_03" in admap
        assert "test_dep_04" in admap

        d3 = admap["test_dep_03"]
        d4 = admap["test_dep_04"]

        assert d3.class_name == "test_dep03"
        assert d3.properties == {"test_dep": "test_dep_value3"}

        assert d4.class_name == "test_dep04"
        assert d4.properties == {"test_dep": "test_dep_value4"}
