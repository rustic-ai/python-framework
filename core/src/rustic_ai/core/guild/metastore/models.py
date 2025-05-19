from enum import Enum
from typing import Dict, List, Optional

import shortuuid
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlmodel import JSON, Column, Field, Relationship, Session, SQLModel
from sympy import Union

from rustic_ai.core.guild.builders import GuildHelper
from rustic_ai.core.guild.dsl import AgentSpec, DependencySpec, GuildSpec
from rustic_ai.core.guild.dsl import KeyConstants as GSKC
from rustic_ai.core.guild.execution import SyncExecutionEngine
from rustic_ai.core.messaging.core.message import AgentTag, RoutingRule, RoutingSlip
from rustic_ai.core.utils.priority import Priority


class GuildStatus(str, Enum):
    """Status values for Guild models."""

    ACTIVE = "active"
    STOPPED = "stopped"
    ARCHIVED = "archived"


class GuildRoutes(SQLModel, table=True):

    __tablename__ = "guild_routes"  # type: ignore

    id: str = Field(primary_key=True, index=True, default_factory=shortuuid.uuid)
    guild_id: Optional[str] = Field(index=True, foreign_key="guilds.id", primary_key=True)

    agent_name: Optional[str] = Field(default=None)
    agent_id: Optional[str] = Field(default=None)
    agent_type: Optional[str] = Field(default=None)
    origin_sender_id: Optional[str] = Field(default=None)
    origin_sender_name: Optional[str] = Field(default=None)
    origin_topic: Optional[str] = Field(default=None)
    origin_message_format: Optional[str] = Field(default=None)
    current_message_format: Optional[str] = Field(default=None)
    transformer: Optional[Dict] = Field(default=None, sa_column=Column(MutableDict.as_mutable(JSON(none_as_null=True))))
    destination_topics: List[str] = Field(
        sa_column=Column(MutableList.as_mutable(JSON(none_as_null=True))),
        default_factory=list,
    )
    destination_recipient_list: List[Dict[str, str]] = Field(
        sa_column=Column(MutableList.as_mutable(JSON(none_as_null=True))),
        default_factory=list,
    )
    destination_priority: Optional[Priority] = Field(default=None)
    method_name: Optional[str] = Field(default=None)
    route_times: int = Field(default=1)

    guild: Optional["GuildModel"] = Relationship(back_populates="routes")

    agent_state_update: Optional[Dict] = Field(
        default=None, sa_column=Column(MutableDict.as_mutable(JSON(none_as_null=True)))
    )
    guild_state_update: Optional[Dict] = Field(
        default=None, sa_column=Column(MutableDict.as_mutable(JSON(none_as_null=True)))
    )

    @classmethod
    def from_routing_rule(cls, guild_id: str, routing_rule: RoutingRule):
        rlist = []
        if routing_rule.destination and routing_rule.destination.recipient_list:
            for recipient in routing_rule.destination.recipient_list:
                rlist.append(recipient.model_dump())

        origin_sender_id = (
            routing_rule.origin_filter.origin_sender.id
            if routing_rule.origin_filter and routing_rule.origin_filter.origin_sender
            else None
        )

        origin_sender_name = (
            routing_rule.origin_filter.origin_sender.name
            if routing_rule.origin_filter and routing_rule.origin_filter.origin_sender
            else None
        )

        destination_topics = []
        if routing_rule.destination and routing_rule.destination.topics:
            if isinstance(routing_rule.destination.topics, str):
                destination_topics.append(routing_rule.destination.topics)
            else:
                destination_topics = routing_rule.destination.topics

        return cls(
            guild_id=guild_id,
            agent_name=routing_rule.agent.name if routing_rule.agent else None,
            agent_id=routing_rule.agent.id if routing_rule.agent else None,
            agent_type=routing_rule.agent_type,
            origin_sender_id=origin_sender_id,
            origin_sender_name=origin_sender_name,
            origin_topic=(routing_rule.origin_filter.origin_topic if routing_rule.origin_filter else None),
            origin_message_format=(
                routing_rule.origin_filter.origin_message_format if routing_rule.origin_filter else None
            ),
            current_message_format=routing_rule.message_format,
            transformer=(routing_rule.transformer.model_dump() if routing_rule.transformer else None),
            destination_topics=destination_topics,
            destination_recipient_list=rlist,
            destination_priority=(routing_rule.destination.priority if routing_rule.destination else None),
            method_name=routing_rule.method_name,
            route_times=routing_rule.route_times,
            agent_state_update=(
                routing_rule.agent_state_update.model_dump() if routing_rule.agent_state_update else None
            ),
            guild_state_update=(
                routing_rule.guild_state_update.model_dump() if routing_rule.guild_state_update else None
            ),
        )

    def to_routing_rule(self) -> RoutingRule:
        recipient_list = []
        if self.destination_recipient_list:
            for recipient in self.destination_recipient_list:
                recipient_list.append(AgentTag.model_validate(recipient))

        origin_sender_id = self.origin_sender_id
        origin_sender_name = self.origin_sender_name

        origin_sender: Optional[AgentTag] = None

        if origin_sender_id or origin_sender_name:
            origin_sender = AgentTag(id=origin_sender_id, name=origin_sender_name)

        origin_topic = self.origin_topic
        origin_message_format = self.origin_message_format

        origin_filter = None

        if origin_sender or origin_topic or origin_message_format:
            origin_filter = {
                "origin_sender": origin_sender,
                "origin_topic": origin_topic,
                "origin_message_format": origin_message_format,
            }

        destination = None
        if self.destination_topics or recipient_list or self.destination_priority:
            destination_topics: Optional[Union[str, List[str]]] = (
                self.destination_topics if self.destination_topics else None
            )
            if destination_topics and len(destination_topics) == 1:
                destination_topics = destination_topics[0]
            destination = {
                "topics": destination_topics,
                "recipient_list": recipient_list,
                "priority": self.destination_priority,
            }

        agent_tag = None
        if self.agent_name or self.agent_id:
            agent_tag = {"name": self.agent_name, "id": self.agent_id}

        rule_dict = {
            "agent": agent_tag,
            "agent_type": self.agent_type,
            "origin_filter": origin_filter,
            "message_format": self.current_message_format,
            "destination": destination,
            "method_name": self.method_name,
            "route_times": self.route_times,
            "transformer": self.transformer,
            "agent_state_update": self.agent_state_update,
            "guild_state_update": self.guild_state_update,
        }

        return RoutingRule.model_validate(rule_dict)


class GuildModel(SQLModel, table=True):

    __tablename__ = "guilds"  # type: ignore

    id: str = Field(primary_key=True, index=True)
    name: str = Field(index=True)
    description: str = Field(default="")
    execution_engine: str = Field(default=SyncExecutionEngine.get_qualified_class_name())

    backend_module: str = Field(default="rustic_ai.core.messaging.backend")
    backend_class: str = Field(default="InMemoryMessagingBackend")
    backend_config: dict = Field(sa_column=Column(MutableDict.as_mutable(JSON(none_as_null=True)), default={}))

    dependency_map: dict = Field(sa_column=Column(MutableDict.as_mutable(JSON(none_as_null=True)), default={}))
    status: GuildStatus = Field(default=GuildStatus.ACTIVE)
    routes: list[GuildRoutes] = Relationship(
        back_populates="guild",
        sa_relationship_kwargs={"cascade": "all", "lazy": "joined"},
    )

    agents: list["AgentModel"] = Relationship(
        back_populates="guild",
        sa_relationship_kwargs={"cascade": "all", "lazy": "joined"},
    )

    @classmethod
    def get_by_id(cls, session: Session, guild_id: str) -> Optional["GuildModel"]:
        return session.get(cls, guild_id)

    @classmethod
    def from_guild_spec(cls, guild_spec: GuildSpec) -> "GuildModel":
        """
        Create a GuildModel instance from a GuildSpec instance.

        Args:
            guild_spec (GuildSpec): The GuildSpec instance.

        Returns:
            GuildModel: The GuildModel instance. This instance DOES NOT have the agents populated.
        """

        exec_engine = GuildHelper.get_execution_engine(guild_spec)

        backend = GuildHelper.get_messaging_config(guild_spec)

        deps_map = {k: v.model_dump() for k, v in guild_spec.dependency_map.items()}

        routes = []

        if guild_spec.routes:
            for rule in guild_spec.routes.steps:
                routes.append(GuildRoutes.from_routing_rule(guild_spec.id, rule))

        return cls(
            id=guild_spec.id,
            name=guild_spec.name,
            description=guild_spec.description,
            status=guild_spec.status,
            execution_engine=exec_engine,
            backend_module=backend.backend_module,
            backend_class=backend.backend_class,
            backend_config=backend.backend_config,
            dependency_map=deps_map,
            routes=routes,
        )

    def to_guild_spec(self) -> GuildSpec:
        """
        Convert the GuildModel instance to a GuildSpec instance.

        Returns:
            GuildSpec: The GuildSpec instance.
        """
        deps = {k: DependencySpec.model_validate(v) for k, v in self.dependency_map.items()}

        routes = []
        if self.routes:
            for route in self.routes:
                routes.append(route.to_routing_rule())

        routing_slip = RoutingSlip(steps=routes)

        return GuildSpec(
            id=self.id,
            name=self.name,
            description=self.description,
            status=self.status,
            agents=[agent.to_agent_spec() for agent in self.agents],
            properties={
                GSKC.EXECUTION_ENGINE: self.execution_engine,
                GSKC.MESSAGING: {
                    GSKC.BACKEND_MODULE: self.backend_module,
                    GSKC.BACKEND_CLASS: self.backend_class,
                    GSKC.BACKEND_CONFIG: self.backend_config,
                },
            },
            dependency_map=deps,
            routes=routing_slip,
        )


class AgentModel(SQLModel, table=True):

    __tablename__ = "agents"  # type: ignore

    id: str = Field(primary_key=True, index=True)
    name: str = Field(index=True)
    description: str = Field(default="")
    class_name: str
    properties: str = Field(sa_column=Column(MutableDict.as_mutable(JSON(none_as_null=True)), default={}))
    additional_topics: List[str] = Field(
        sa_column=Column(MutableList.as_mutable(JSON(none_as_null=True))),
        default_factory=list,
    )
    listen_to_default_topic: bool = True

    dependency_map: dict = Field(sa_column=Column(MutableDict.as_mutable(JSON(none_as_null=True)), default={}))

    guild_id: Optional[str] = Field(index=True, foreign_key="guilds.id", primary_key=True)
    guild: Optional[GuildModel] = Relationship(back_populates="agents")

    predicates: dict = Field(sa_column=Column(MutableDict.as_mutable(JSON(none_as_null=True)), default={}))

    @classmethod
    def get_by_id(cls, session, guild_id: str, agent_id: str) -> Optional["AgentModel"]:
        return session.get(cls, (agent_id, guild_id))

    @classmethod
    def get_by_guild_id(cls, session, guild_id: str) -> Optional["AgentModel"]:
        return session.get(cls, guild_id)

    @classmethod
    def from_agent_spec(cls, guild_id: str, agent_spec: AgentSpec) -> "AgentModel":
        """
        Create an AgentModel instance from an AgentSpec instance.

        Args:
            agent_spec (AgentSpec): The AgentSpec instance.
            guild_id (str): The guild ID.

        Returns:
            AgentModel: The AgentModel instance.

        """
        deps_map = {k: v.model_dump() for k, v in agent_spec.dependency_map.items()}
        predicates = {k: v.model_dump() for k, v in agent_spec.predicates.items()}

        return cls(
            id=agent_spec.id,
            name=agent_spec.name,
            description=agent_spec.description,
            class_name=agent_spec.class_name,
            properties=(agent_spec.properties.model_dump() if agent_spec.properties else {}),
            additional_topics=agent_spec.additional_topics,
            listen_to_default_topic=agent_spec.listen_to_default_topic,
            guild_id=guild_id,
            dependency_map=deps_map,
            predicates=predicates,
        )

    def to_agent_spec(self) -> AgentSpec:
        """
        Convert the AgentModel instance to an AgentSpec instance.

        Returns:
            AgentSpec: The AgentSpec instance.
        """
        # deps = {k: DependencySpec.model_validate(v) for k, v in self.dependency_map.items()}
        # predicates = {k: RuntimePredicate.model_validate(v) for k, v in self.predicates.items()}

        spec_dict = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "class_name": self.class_name,
            "properties": self.properties,
            "additional_topics": self.additional_topics,
            "listen_to_default_topic": self.listen_to_default_topic,
            "dependency_map": self.dependency_map,
            "predicates": self.predicates,
        }

        return AgentSpec.model_validate(spec_dict)
