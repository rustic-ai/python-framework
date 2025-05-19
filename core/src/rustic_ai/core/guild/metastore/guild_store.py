from typing import Optional, Sequence

from sqlalchemy import Engine
from sqlmodel import Session, select

from ..dsl import APT, AgentSpec, GuildSpec
from .models import AgentModel, GuildModel, GuildStatus


class GuildStore:
    """
    A metadata management counterpart to the GuildManager.
    This class is responsible for storing and retrieving guilds and agents from a database.
    """

    def __init__(self, engine: Engine):
        self.engine = engine

    def get_guild(self, guild_id: str) -> Optional[GuildModel]:
        """
        Get a guild by its ID.
        """
        with Session(self.engine) as session:
            guild_query = select(GuildModel).where(GuildModel.id == guild_id)
            guild_model = session.exec(guild_query).unique().one_or_none()
            session.close()
        return guild_model

    def add_guild(self, guild_spec: GuildSpec) -> GuildModel:
        """
        Add a guild to the metastore.
        """
        with Session(self.engine) as session:
            guild_model = GuildModel.from_guild_spec(guild_spec)
            session.add(guild_model)
            session.commit()
            session.refresh(guild_model)
        return guild_model

    def update_guild_status(self, guild_id: str, status: GuildStatus) -> Optional[GuildModel]:
        """
        Update a guild's status.

        Args:
            guild_id (str): The ID of the guild to update
            status (GuildStatus): The new status value to set

        Returns:
            Optional[GuildModel]: The updated guild model, or None if the guild was not found

        Raises:
            ValueError: If the guild is not found
        """
        with Session(self.engine) as session:
            guild_model = GuildModel.get_by_id(session, guild_id)

            if not guild_model:
                raise ValueError(f"Guild with ID {guild_id} not found")

            guild_model.status = status

            session.add(guild_model)
            session.commit()
            session.refresh(guild_model)

        return guild_model

    def list_guilds(self) -> Sequence[GuildModel]:
        """
        List the guilds in the metastore.
        """
        with Session(self.engine) as session:
            get_guilds_stmt = select(GuildModel)
            guilds = session.exec(get_guilds_stmt).unique().all()
            session.close()
        return guilds

    def remove_guild(self, guild_id: str) -> None:
        """
        Remove a guild and all its agents from the metastore.
        """

        with Session(self.engine) as session:
            guild_model = GuildModel.get_by_id(session, guild_id)
            session.delete(guild_model)
            session.commit()
            session.close()

    def add_agent(self, guild_id: str, agent_spec: AgentSpec[APT]) -> AgentModel:
        """
        Add an agent to the guild.
        """

        with Session(self.engine) as session:
            guild = GuildModel.get_by_id(session, guild_id)

            if not guild:
                raise ValueError(f"Guild with ID {guild_id} not found")
            else:
                agent_model = AgentModel.from_agent_spec(guild_id, agent_spec)
                session.add(agent_model)
                session.commit()
            session.close()
        return agent_model

    def get_agent(self, guild_id: str, agent_id: str) -> Optional[AgentModel]:
        """
        Get an agent by its ID.
        """
        with Session(self.engine) as session:
            guild = GuildModel.get_by_id(session, guild_id)

            if not guild:
                agent_model = None
            else:
                agent_model = AgentModel.get_by_id(session, guild_id, agent_id)
            session.close()
        return agent_model

    def remove_agent(self, guild_id: str, agent_id: str) -> None:
        """
        Remove an agent from the guild.
        """
        with Session(self.engine) as session:
            guild = GuildModel.get_by_id(session, guild_id)

            if not guild:
                raise ValueError(f"Guild with ID {guild_id} not found")
            else:
                agent_model = AgentModel.get_by_id(session, guild_id, agent_id)
                if agent_model:
                    session.delete(agent_model)
                else:
                    raise ValueError(f"Agent with ID {agent_id} not found in guild {guild_id}")
                session.commit()
            session.close()

    def list_agents(self, guild_id: str) -> Sequence[AgentModel]:
        """
        List the agents in the guild.
        """
        with Session(self.engine) as session:
            guild_model = GuildModel.get_by_id(session, guild_id)
            if not guild_model:
                raise ValueError(f"Guild with ID {guild_id} not found")
            else:
                agents = guild_model.agents
            session.close()
        return agents
