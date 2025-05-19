import importlib
import json
import logging
import mimetypes
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import quote

import griffe
from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
)
from fastapi.responses import JSONResponse, StreamingResponse
from griffe import Alias, Class, Module, Object
from pydantic import BaseModel, ValidationError
from sqlalchemy import Engine
from starlette import status

from rustic_ai.api_server.api_dependency_manager import ApiDependencyManager
from rustic_ai.api_server.guilds.comms_manager import GuildCommunicationManager
from rustic_ai.api_server.guilds.schema import IdInfo
from rustic_ai.api_server.guilds.service import GuildService
from rustic_ai.core import Agent
from rustic_ai.core.agents.commons.media import MediaLink
from rustic_ai.core.guild.agent_ext.depends.filesystem import FileSystem
from rustic_ai.core.guild.dsl import GuildSpec
from rustic_ai.core.guild.metaprog.agent_registry import AgentRegistry
from rustic_ai.core.guild.metastore import Metastore
from rustic_ai.core.messaging.core.message import Message
from rustic_ai.core.utils.basic_class_utils import get_class_from_name

router = APIRouter()
guild_service = GuildService()


@router.post("/guilds", response_model=IdInfo, status_code=status.HTTP_201_CREATED, operation_id="createGuild")
def create_guild(guild_spec: GuildSpec):
    """
    Creates a new guild and adds it to the database.

    Args:
        guild_spec (GuildSpec): The spec for the new guild

    Returns:
        IdInfo: The id of the newly created guild
    """
    if not guild_spec:
        raise HTTPException(status_code=400, detail="Invalid input")  # pragma: no cover

    try:
        guild_id = guild_service.create_guild(Metastore.get_db_url(), guild_spec)
        logging.debug(f"New guild created: {guild_id}")
        return IdInfo(id=guild_id)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())  # pragma: no cover
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  # pragma: no cover


@router.get("/guilds/{guild_id}", response_model=GuildSpec, operation_id="getGuildDetailsById")
def get_guild(guild_id: str, engine=Depends(Metastore.get_engine)) -> GuildSpec:
    """
    Retrieves details for a guild based on the provided guild_id.

    Args:
        guild_id (str): The ID of the guild to retrieve details for.

    Returns:
        GuildSpec: The retrieved guild details, or None if the guild was not found.

    Raises:
        HTTPException: If the guild is not found, raises an HTTPException with a status code of 404.
    """
    logging.debug(f"Retrieving details for guild: {guild_id}")
    maybeGuild = guild_service.get_guild(engine, guild_id)

    if maybeGuild is None:
        raise HTTPException(status_code=404, detail="Guild not found")

    return maybeGuild


@router.patch("/guilds/{guild_id}/status", response_model=GuildSpec, operation_id="updateGuildStatus")
def update_guild_status(
    guild_id: str,
    status: str = Body(..., embed=True, description="Guild status: 'active', 'stopped', or 'archived'"),
    engine=Depends(Metastore.get_engine),
) -> GuildSpec:
    """
    Updates the status of a guild.

    Args:
        guild_id (str): The ID of the guild to update.
        status (str): The new status for the guild. Must be one of: 'active', 'stopped', 'archived'.
                     These correspond to the GuildSpec.GuildStatus enum values.

    Returns:
        GuildSpec: The updated guild details.

    Raises:
        HTTPException: If the guild is not found (404) or if the status is invalid (400).
    """
    logging.debug(f"Updating status for guild: {guild_id} to {status}")

    try:
        updated_guild = guild_service.update_guild_status(engine, guild_id, status)
        return updated_guild
    except ValueError as e:
        if "Invalid guild status" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guilds/{guild_id}/{user_id}/messages", operation_id="getHistoricalUserMessages")
async def get_historical_user_notifications(
    guild_id: str,
    user_id: str,
    guild_comm_manager: GuildCommunicationManager = Depends(GuildCommunicationManager.get_instance),
    engine: Engine = Depends(Metastore.get_engine),
) -> List[Message]:
    return await guild_comm_manager.get_historical_user_notifications(guild_id, user_id, engine)


def _get_meta_file_name(filename: str) -> str:
    return f".{filename}.meta"


async def upload_file(
    guild_id: str,
    file: UploadFile,
    engine: Engine,
    api_deps_manager: ApiDependencyManager,
    agent_id: Optional[str] = None,
    metadata: Optional[str] = None,
):
    """
    Uploads a file to a guild.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Invalid input: file and filename are required")

    filesystem: FileSystem = api_deps_manager.get_dependency("filesystem", engine, guild_id, agent_id)
    contents = await file.read()

    if filesystem.exists(file.filename):
        raise HTTPException(status_code=409, detail="File already exists")

    file_meta = json.loads(metadata) if metadata else {}
    file_meta["content_length"] = len(contents)
    file_meta["content_type"] = file.content_type
    file_meta["uploaded_at"] = datetime.now(timezone.utc).isoformat()

    try:
        with filesystem.open(file.filename, "wb") as f:
            f.write(contents)
        with filesystem.open(_get_meta_file_name(file.filename), "wb") as mf:  # type: ignore[arg-type]
            mf.write(json.dumps(file_meta).encode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    encoded_filename = quote(file.filename)

    return JSONResponse(
        content={
            "guild_id": guild_id,
            "filename": file.filename,
            "url": f"/rustic/api/guilds/{guild_id}/files/{encoded_filename}",
            "content_type": file.content_type,
            "content_length": len(contents),
        }
    )


@router.post("/guilds/{guild_id}/files/", operation_id="uploadFileForGuild")
async def upload_file_for_guild(
    guild_id: str,
    file: UploadFile = File(...),
    file_meta: Optional[str] = Form(None),
    engine: Engine = Depends(Metastore.get_engine),
    api_deps_manager: ApiDependencyManager = Depends(ApiDependencyManager.get_instance),
):
    return await upload_file(guild_id, file, engine, api_deps_manager, metadata=file_meta)


@router.post(
    "/guilds/{guild_id}/agents/{agent_id}/files/", operation_id="uploadFileForAgent", response_model=List[MediaLink]
)
async def upload_file_for_agent(
    guild_id: str,
    agent_id: str,
    file: UploadFile = File(...),
    file_meta: Optional[str] = Form(None),
    engine: Engine = Depends(Metastore.get_engine),
    api_deps_manager: ApiDependencyManager = Depends(ApiDependencyManager.get_instance),
):
    return await upload_file(guild_id, file, engine, api_deps_manager, agent_id, metadata=file_meta)


async def list_files(
    guild_id: str, engine: Engine, api_deps_manager: ApiDependencyManager, agent_id: Optional[str] = None
):
    """Lists available files for a guild/agent."""
    filesystem: FileSystem = api_deps_manager.get_dependency("filesystem", engine, guild_id, agent_id)
    try:
        files_with_details = filesystem.ls("/")
        result = []
        for file_details in files_with_details:
            file_name = file_details["name"]
            if not file_name.startswith("."):
                file_meta = json.load(filesystem.open(_get_meta_file_name(file_name), "r"))
                mimetype = file_meta["content_type"]
                result.append(
                    MediaLink(
                        url=file_name,
                        name=file_name,
                        metadata={x: file_meta[x] for x in file_meta if x != "content_type"},
                        on_filesystem=True,
                        mimetype=mimetype,
                    ).model_dump()
                )
        return JSONResponse(content=result)
    except Exception as e:
        logging.error(e)
        # An exception is thrown when no such directory exists.
        # This can happen when no files have been uploaded for the guild/agent yet.
        # In such cases, we must return an empty list
        return JSONResponse(content=[])


@router.get("/guilds/{guild_id}/files/", operation_id="listFilesForGuild")
async def list_files_for_guild(
    guild_id: str,
    engine: Engine = Depends(Metastore.get_engine),
    api_deps_manager: ApiDependencyManager = Depends(ApiDependencyManager.get_instance),
):
    return await list_files(guild_id, engine, api_deps_manager)


@router.get("/guilds/{guild_id}/agents/{agent_id}/files/", operation_id="listFilesForAgent")
async def list_files_for_agent(
    guild_id: str,
    agent_id: str,
    engine: Engine = Depends(Metastore.get_engine),
    api_deps_manager: ApiDependencyManager = Depends(ApiDependencyManager.get_instance),
):
    return await list_files(guild_id, engine, api_deps_manager, agent_id)


async def download_file(
    guild_id: str,
    filename: str,
    engine: Engine,
    api_deps_manager: ApiDependencyManager,
    agent_id: Optional[str] = None,
):
    """
    Downloads a file from a guild.
    """

    filesystem: FileSystem = api_deps_manager.get_dependency("filesystem", engine, guild_id, agent_id)

    if not filesystem.exists(filename):
        raise HTTPException(status_code=404, detail="File not found")

    try:

        def serve_file():
            with filesystem.open(filename, "rb") as file_like:
                yield from file_like

        response = StreamingResponse(serve_file(), media_type="application/octet-stream")
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_file_content(
    guild_id: str,
    filename: str,
    engine: Engine,
    api_deps_manager: ApiDependencyManager,
    agent_id: Optional[str] = None,
):
    """
    Gets the file from a guild.
    """

    filesystem: FileSystem = api_deps_manager.get_dependency("filesystem", engine, guild_id, agent_id)

    if not filesystem.exists(filename):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        with filesystem.open(filename, "rb") as file_like:
            return file_like.read()
    except Exception as e:
        logging.error(f"Error getting file content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guilds/{guild_id}/files/{filename}", operation_id="getFileForGuild")
async def get_file_for_guild(
    guild_id: str,
    filename: str,
    download: Optional[bool] = False,
    engine: Engine = Depends(Metastore.get_engine),
    api_deps_manager: ApiDependencyManager = Depends(ApiDependencyManager.get_instance),
):
    if download:
        return await download_file(guild_id, filename, engine, api_deps_manager)
    else:
        content = await get_file_content(guild_id, filename, engine, api_deps_manager)
        return Response(content=content, media_type=mimetypes.guess_type(filename)[0])


@router.get("/guilds/{guild_id}/agents/{agent_id}/files/{filename}", operation_id="getFileForAgent")
async def get_file_for_agent(
    guild_id: str,
    agent_id: str,
    filename: str,
    download: Optional[bool] = False,
    engine: Engine = Depends(Metastore.get_engine),
    api_deps_manager: ApiDependencyManager = Depends(ApiDependencyManager.get_instance),
):
    if download:
        return await download_file(guild_id, filename, engine, api_deps_manager, agent_id)
    else:
        content = await get_file_content(guild_id, filename, engine, api_deps_manager, agent_id)
        return Response(content=content, media_type=mimetypes.guess_type(filename)[0])


async def delete_file(
    guild_id: str,
    filename: str,
    engine: Engine,
    api_deps_manager: ApiDependencyManager,
    agent_id: Optional[str] = None,
):
    """
    Deletes the file from the guild/agent.
    """

    filesystem: FileSystem = api_deps_manager.get_dependency("filesystem", engine, guild_id, agent_id)

    if not filesystem.exists(filename):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        filesystem.rm_file(filename)
        filesystem.rm_file(_get_meta_file_name(filename))
        return Response(status_code=204)
    except Exception as e:
        logging.error(f"Error getting file content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/guilds/{guild_id}/files/{filename}", status_code=status.HTTP_204_NO_CONTENT, operation_id="deleteGuildFile"
)
async def delete_file_for_guild(
    guild_id: str,
    filename: str,
    engine: Engine = Depends(Metastore.get_engine),
    api_deps_manager: ApiDependencyManager = Depends(ApiDependencyManager.get_instance),
):
    return await delete_file(guild_id, filename, engine, api_deps_manager)


@router.delete(
    "/guilds/{guild_id}/agents/{agent_id}/files/{filename}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteAgentFile",
)
async def delete_files_for_agent(
    guild_id: str,
    agent_id: str,
    filename: str,
    engine: Engine = Depends(Metastore.get_engine),
    api_deps_manager: ApiDependencyManager = Depends(ApiDependencyManager.get_instance),
):
    return await delete_file(guild_id, filename, engine, api_deps_manager, agent_id)


_base_agent_class = Agent.get_qualified_class_name()


def _load_agents():
    """
    Scans the agents module for agents and imports them.
    """
    packages = ["rustic_ai"]

    for package in packages:
        all_agents = _scan_module_for_agents(griffe.load(package))

    for agent in all_agents:
        importlib.import_module(agent.module.path)


def _inherits_agent(member: Class) -> bool:
    if member.is_class and hasattr(member, "bases"):
        for base in member.resolved_bases:
            if _base_agent_class == base.path:
                return True
            elif isinstance(base, Class):
                return _inherits_agent(base)
    return False


def _scan_module_for_agents(module: Module | Object | Alias) -> List[Class]:
    """
    Scans a module for agents and imports them.
    """
    all_agents = []
    if module.is_module:
        for name in module.all_members:
            member = module.get_member(name)
            if member.is_alias:
                continue
            elif member.is_module:
                new_agents = _scan_module_for_agents(member)
                all_agents.extend(new_agents)
            elif member.is_class and isinstance(member, Class):
                if _inherits_agent(member):
                    all_agents.append(member)

    return all_agents


_load_agents()


@router.get("/registry/agents/", response_model=Dict[str, dict], operation_id="getAgentsByClass")
def get_agents(agent_class: Optional[str] = None):
    if agent_class:
        agent = AgentRegistry.get_agent(agent_class)
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {agent.qualified_class_name: agent.model_dump()}
    else:
        hidden_agents = ["GuildManagerAgent", "ProbeAgent", "EssentialProbeAgent"]
        agents = AgentRegistry.list_agents()
        all_agents = {name: agent.model_dump() for name, agent in agents.items() if name not in hidden_agents}
        return JSONResponse(content=all_agents, media_type="application/json")


@router.get("/registry/message_schema/", response_model=dict, operation_id="getMessageSchemaByClass")
def get_message_types(message_class: str):
    try:
        class_instance = get_class_from_name(message_class)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(f"Class {message_class} not found: " + str(e)))

    if issubclass(class_instance, BaseModel):
        return class_instance.model_json_schema()
    else:
        raise HTTPException(status_code=400, detail="Class is not a subclass of pydantic.BaseModel")
