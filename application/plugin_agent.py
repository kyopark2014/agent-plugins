import os
import json
import yaml
import langgraph_agent
import mcp_config
import chat
import logging
import sys
import langgraph_agent
import plugin
import skill

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, AIMessageChunk
from langchain_mcp_adapters.client import MultiServerMCPClient

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger("plugin-agent")


WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(WORKING_DIR, "artifacts")
PLUGINS_DIR = os.path.join(WORKING_DIR, "plugins")

from typing import Literal, Optional

async def create_agent(mcp_servers: list, plugin_name: Optional[str]=None, command: Optional[str]=None, history_mode: str="Disable") -> tuple[str, list]:
    # builtin tools
    tools = langgraph_agent.get_builtin_tools()
    logger.info(f"builtin_tools count: {len(tools)}")
        
    # mcp
    mcp_json = mcp_config.load_selected_config(mcp_servers)
    # logger.info(f"mcp_json: {mcp_json}")

    server_params = langgraph_agent.load_multiple_mcp_server_parameters(mcp_json)
    # logger.info(f"server_params: {server_params}")    

    try:
        client = MultiServerMCPClient(server_params)
        logger.info(f"MCP client is initialized successfully")
        
        mcp_tools = await client.get_tools()        # add MCP tools
        # logger.info(f"mcp_tools: {mcp_tools}")        
        for tool in mcp_tools:
            logger.info(f"mcp_tool: {tool.name}")
            if tool.name not in tools:
                tools.append(tool)
            else:
                logger.info(f"mcp_tool of {tool.name} already in tools")
        
    except Exception as e:
        logger.error(f"Error creating MCP client or getting tools: {e}")
        logger.info(f"Falling back to builtin tools only (count: {len(tools)})")

    if chat.skill_mode == "Enable":       
        tools.extend(skill.get_skill_tools())

        skill_info = skill.selected_skill_info("base")
        plugin_skill_info = skill.selected_skill_info(plugin_name)
        logger.info(f"skill_info: {skill_info}, plugin_skill_info: {plugin_skill_info}")        
        skill_info.extend(plugin_skill_info)

        if command:
            system_prompt = skill.build_command_prompt(plugin_name, skill_info, command)
        else:
            system_prompt = skill.build_skill_prompt(skill_info)        
        logger.info(f"system prompt: {system_prompt}")

    else:
        system_prompt = langgraph_agent.BASE_SYSTEM_PROMPT

    tool_list = [tool.name for tool in tools] if tools else []
    logger.info(f"tool_list: {tool_list}")
    
    if history_mode == "Enable":
        app = langgraph_agent.buildChatAgentWithHistory(tools)
        config = {
            "recursion_limit": 100,
            "configurable": {"thread_id": chat.user_id},
            "tools": tools,
            "system_prompt": system_prompt
        }
    else:
        app = langgraph_agent.buildChatAgent(tools)
        config = {
            "recursion_limit": 100,
            "configurable": {"thread_id": chat.user_id},
            "tools": tools,
            "system_prompt": system_prompt
        }        
    
    return app, config

app = config = None
active_mcp_servers = []
active_plugin_name = None
last_command = None

async def run_plugin_agent(query, mcp_servers, plugin_name, history_mode, notification_queue):
    """Run plugin agent with MCP tools and skills."""
    global app, config, active_mcp_servers, active_skills, last_command

    queue = notification_queue if notification_queue else None
    if queue:
        queue.reset()

    artifacts = []
    references = []

    command = None
    if plugin.is_command(query, plugin_name):
        command = query.split(" ")[0].lstrip("/")
        logger.info(f"command: {command}")

    selected_skill_info = skill.selected_skill_info("base")

    if app is None or mcp_servers != active_mcp_servers or active_skills != selected_skill_info or last_command != command:
        active_mcp_servers = mcp_servers
        active_skills = selected_skill_info
        last_command = command

        app, config = await create_agent(mcp_servers, plugin_name, command, history_mode)
    
    if app is None:
        logger.error("Failed to create agent - app is None")
        return "에이전트를 생성할 수 없습니다. MCP 서버 설정 또는 도구 구성을 확인해주세요.", []
    
    inputs = {
        "messages": [HumanMessage(content=query)]
    }

    result = ""
    tool_used = False
    tool_name = toolUseId = ""
    async for stream in app.astream(inputs, config, stream_mode="messages"):
        if isinstance(stream[0], AIMessageChunk):
            message = stream[0]
            input = {}
            if isinstance(message.content, list):
                for content_item in message.content:
                    if isinstance(content_item, dict):
                        if content_item.get('type') == 'text':
                            text_content = content_item.get('text', '')

                            if tool_used:
                                result = text_content
                                tool_used = False
                            else:
                                result += text_content

                            chat.update_streaming_result(notification_queue, result, "markdown")

                        elif content_item.get('type') == 'tool_use':
                            if 'id' in content_item and 'name' in content_item:
                                toolUseId = content_item.get('id', '')
                                tool_name = content_item.get('name', '')
                                logger.info(f"tool_name: {tool_name}, toolUseId: {toolUseId}")
                                if queue:
                                    queue.register_tool(toolUseId, tool_name)

                            if 'partial_json' in content_item:
                                partial_json = content_item.get('partial_json', '')

                                if toolUseId not in chat.tool_input_list:
                                    chat.tool_input_list[toolUseId] = ""
                                chat.tool_input_list[toolUseId] += partial_json
                                input = chat.tool_input_list[toolUseId]

                                if queue:
                                    queue.tool_update(toolUseId, f"Tool: {tool_name}, Input: {input}")

        elif isinstance(stream[0], ToolMessage):
            message = stream[0]
            logger.info(f"ToolMessage: {message.name}, {message.content}")
            tool_name = message.name
            toolResult = message.content
            toolUseId = message.tool_call_id
            logger.info(f"toolResult: {toolResult}, toolUseId: {toolUseId}")
            chat.add_notification(notification_queue, f"Tool Result: {toolResult}")
            tool_used = True

            content, urls, refs = chat.get_tool_info(tool_name, toolResult)
            if refs:
                for r in refs:
                    references.append(r)
                logger.info(f"refs: {refs}")
            if urls:
                for url in urls:
                    artifacts.append(url)
                logger.info(f"urls: {urls}")

            if content:
                logger.info(f"content: {content}")

    if not result:
        result = "답변을 찾지 못하였습니다."
    logger.info(f"result: {result}")

    if references:
        ref = "\n\n### Reference\n"
        for i, reference in enumerate(references):
            page_content = reference['content'][:100].replace("\n", "")
            ref += f"{i+1}. [{reference['title']}]({reference['url']}), {page_content}...\n"
        result += ref

    chat.update_final_result(notification_queue, result)

    return result
