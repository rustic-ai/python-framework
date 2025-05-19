from abc import ABC, abstractmethod
from typing import (
    Annotated,
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    cast,
)

import jsonata
import shortuuid
from pydantic import BaseModel, ConfigDict, Field, model_validator

from rustic_ai.core.guild.agent_ext.depends.dependency_resolver import DependencySpec
from rustic_ai.core.guild.metaprog.constants import MetaclassConstants
from rustic_ai.core.messaging.core.message import AgentTag, RoutingSlip
from rustic_ai.core.utils.basic_class_utils import get_class_from_name
from rustic_ai.core.utils.json_utils import JsonDict


class BaseAgentProps(BaseModel):
    """
    Empty class for Agent properties.
    """

    @classmethod
    def get_qualified_class_name(cls) -> str:
        return f"{cls.__module__}.{cls.__name__}"


APT = TypeVar("APT", bound=BaseAgentProps)


class KeyConstants:
    """
    Constants for keys used in GuildSpec properties.
    """

    EXECUTION_ENGINE = "execution_engine"
    MESSAGING = "messaging"
    BACKEND_MODULE = "backend_module"
    BACKEND_CLASS = "backend_class"
    BACKEND_CONFIG = "backend_config"
    CLIENT_TYPE = "client_type"
    CLIENT_PROPERTIES = "client_properties"
    STATE_MANAGER = "state_manager"


class GuildTopics:
    """
    Constants for global values.
    """

    DEFAULT_TOPICS: List[str] = ["default_topic"]

    SYSTEM_TOPIC: str = "system_topic"

    GUILD_STATUS_TOPIC: str = "guild_status_topic"

    ESSENTIAL_TOPICS: List[str] = [GUILD_STATUS_TOPIC]


class RuntimePredicate(ABC, BaseModel):
    @abstractmethod
    def evaluate(self, message: JsonDict, agent_state: JsonDict, guild_state: JsonDict) -> bool:
        pass


class SimpleRuntimePredicate(RuntimePredicate):
    expression: str

    def evaluate(self, message: JsonDict, agent_state: JsonDict, guild_state: JsonDict) -> bool:
        expr = jsonata.Jsonata(self.expression)
        result = expr.evaluate({"message": message, "agent_state": agent_state, "guild_state": guild_state})

        # Make sure we return a boolean
        if result:
            return True
        else:
            return False


class AgentSpec(BaseModel, Generic[APT]):
    """
    A specification for an agent that describes its name, description, and properties.

    Attributes:
        name (str): The name of the agent.
        description (str): A description of the agent.
        class_name (str): The name of the class of the agent.
        additional_topics (List[str]): A list of additional topics to which the agent should subscribe.
        properties (APT): The properties of the agent.
        listen_to_default_topic (bool): Whether the agent should listen to the default topic.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(default_factory=shortuuid.uuid)
    name: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1)
    class_name: str
    additional_topics: List[str] = []
    properties: APT = Field(default_factory=lambda: BaseAgentProps())  # type: ignore
    listen_to_default_topic: bool = True

    act_only_when_tagged: bool = False

    predicates: Dict[str, SimpleRuntimePredicate] = Field(
        default_factory=dict,
        description="A mapping of functions to their runtime predicates.",
    )

    # A mapping for guild's dependency to resolver class
    dependency_map: Dict[str, DependencySpec] = {}

    _subscribed_topics: Set[str] = set()

    @property
    def props(self) -> APT:
        assert self.properties is not None, f"Agent type {self.class_name} does not have properties defined."
        return self.properties

    @property
    def subscribed_topics(self) -> Set[str]:
        if not self._subscribed_topics:
            topics: Set[str] = set(self.additional_topics)
            if self.listen_to_default_topic:
                topics.update(set(GuildTopics.DEFAULT_TOPICS))

            topics.update(set(GuildTopics.ESSENTIAL_TOPICS))
            self._subscribed_topics = topics
        return self._subscribed_topics

    @model_validator(mode="before")
    @classmethod
    def pre_build_validator(cls, data):

        class_name = data.get("class_name")
        agent_class: Type

        if not class_name:
            raise ValueError("class_name is required")
        else:
            try:
                agent_class = get_class_from_name(class_name)

                # Loading the class from the string to avoid circular imports

                agent_base_class = get_class_from_name("rustic_ai.core.guild.Agent")
            except Exception as e:
                raise ValueError(f"Invalid class name: {class_name}") from e

            if not issubclass(agent_class, agent_base_class):
                raise ValueError(f"Class {class_name} is not a subclass of Agent")

        properties_type: Type[BaseAgentProps] = agent_class.__annotations__[MetaclassConstants.AGENT_PROPS_TYPE] or BaseAgentProps  # type: ignore

        properties = data.get("properties")

        if properties_type != BaseAgentProps:
            if not properties or type(properties) is BaseAgentProps:
                data["properties"] = properties_type()
            elif properties and isinstance(properties, dict):
                data["properties"] = properties_type.model_validate(properties)
            elif not isinstance(properties, properties_type):
                raise ValueError(f"Properties must be an instance of {properties_type}")
        elif properties and type(properties) is not BaseAgentProps:
            raise ValueError(f"Agent {class_name} does not accept properties")

        return data

    @classmethod
    def get_pydantic_generic_type(cls) -> Type[BaseAgentProps]:
        margs = cls.__pydantic_generic_metadata__["args"]
        if len(margs) >= 1:
            gt = margs[0]
        else:
            gt = BaseAgentProps
        return cast(Type[BaseAgentProps], gt)


class GuildSpec(BaseModel):
    """
    A specification for a guild that describes its name, description, and agents.

    Attributes:
        name (str): The name of the guild.
        description (str): A description of the guild.
        properties (Dict[str, Any]): The properties of the guild.
        agents (list[AgentSpec]): A list of agents in the guild.
        dependency_map (Dict[str, DependencySpec]): A mapping for guild's dependency to resolver class.
        routes (RoutingSlip): The routes to be attached to every message coming in the guild.
        status (str): The status of the guild, e.g., "active", "stopped", "archived".
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(default_factory=shortuuid.uuid)
    name: Annotated[str, Field(min_length=1, max_length=64)]
    description: Annotated[str, Field(min_length=1)]
    properties: Dict[str, Any] = {}
    agents: list[AgentSpec] = []
    status: str = "active"  # Using string instead of enum to avoid circular imports

    # A mapping for guild's dependency to resolver class
    dependency_map: Dict[str, DependencySpec] = {}

    routes: RoutingSlip = Field(default_factory=RoutingSlip)

    def __init__(self, **data):
        super().__init__(**data)

    def add_agent_spec(self, agent: AgentSpec):
        if agent not in self.agents:
            self.agents.append(agent)
        else:
            raise ValueError(f"Agent {agent.name} already exists in guild")

    def set_execution_engine(self, execution_engine: str):
        self.properties[KeyConstants.EXECUTION_ENGINE] = execution_engine

    def set_messaging(self, backend_module: str, backend_class: str, backend_config: dict = {}):
        self.properties[KeyConstants.MESSAGING] = {}

        self.properties[KeyConstants.MESSAGING][KeyConstants.BACKEND_MODULE] = backend_module
        self.properties[KeyConstants.MESSAGING][KeyConstants.BACKEND_CLASS] = backend_class
        self.properties[KeyConstants.MESSAGING][KeyConstants.BACKEND_CONFIG] = backend_config

    def get_execution_engine(self) -> Optional[str]:
        return self.properties.get("execution_engine", None)  # pragma: no cover

    def get_messaging(self) -> Optional[dict]:
        return self.properties.get(KeyConstants.MESSAGING, None)  # pragma: no cover

    def get_guild_agents(self) -> List[AgentTag]:
        return [AgentTag(id=agent.id, name=agent.name) for agent in self.agents]
