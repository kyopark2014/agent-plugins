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

async def run_plugin_agent(query, mcp_servers, plugin_name, containers):
    """Run plugin agent with MCP tools and skills."""
    chat.index = 0
    chat.streaming_index = 0

    image_url = []
    references = []

    # mcp
    mcp_json = mcp_config.load_selected_config(mcp_servers)
    logger.info(f"plugin {plugin_name} mcp_json: {mcp_json}")

    if not mcp_json.get("mcpServers"):
        logger.warning(f"No MCP servers in plugin {plugin_name}, using empty tools")
        tools = []
    else:
        server_params = langgraph_agent.load_multiple_mcp_server_parameters(mcp_json)
        logger.info(f"server_params: {server_params}")

        try:
            client = MultiServerMCPClient(server_params)
            logger.info("MCP client created successfully")

            tools = await client.get_tools()
            # logger.info(f"get_tools() returned: {tools}")

            if tools is None:
                logger.error("tools is None - MCP client failed to get tools")
                tools = []

        except Exception as e:
            logger.error(f"Error creating MCP client or getting tools: {e}")
            tools = []

    # Use plugin-specific get_skill_instructions so plugin skills (e.g. frontend-design)
    # are found from plugins/<name>/skills/, not the global application/skills/
    builtin_tools = plugin.get_builtin_tools()
    skill_instruction = plugin.create_plugin_and_get_skill_instructions(plugin_name)

    # Replace with plugin-aware version that uses PluginManager in order to tool duplication
    tool_names = {t.name for t in tools}
    for bt in builtin_tools:
        if bt.name == "get_skill_instructions":            
            if "get_skill_instructions" not in tool_names:
                tools.append(skill_instruction)
        elif bt.name not in tool_names:
            tools.append(bt)
        else:
            logger.info(f"builtin_tool {bt.name} already in tools")

    # Get plugin-specific skills and register them in SkillManager's registry
    skill.register_plugin_skills(plugin_name)

    plugin_skills = plugin.get_plugin_skills(plugin_name)
    logger.info(f"plugin: {plugin_name}, skills: {plugin_skills}")

    tool_list = [tool.name for tool in tools] if tools else []
    logger.info(f"tool_list: {tool_list}")

    if not tools:
        logger.warning("No tools available for plugin")
        result = "Check your MCP configuration. Ensure the plugin's mcp_servers.list has connected MCP servers."
        if containers is not None:
            containers['notification'][0].markdown(result)
        return result

    app = langgraph_agent.buildChatAgentWithHistory(tools)
    config = {
        "recursion_limit": 100,
        "configurable": {
            "thread_id": f"plugin-{plugin_name}",
            "tools": tools,
            "plugin_name": plugin_name,
            "system_prompt": None,
        }
    }

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

                            chat.update_streaming_result(containers, result, "markdown")

                        elif content_item.get('type') == 'tool_use':
                            if 'id' in content_item and 'name' in content_item:
                                toolUseId = content_item.get('id', '')
                                tool_name = content_item.get('name', '')
                                logger.info(f"tool_name: {tool_name}, toolUseId: {toolUseId}")
                                chat.streaming_index = chat.index
                                chat.index += 1

                            if 'partial_json' in content_item:
                                partial_json = content_item.get('partial_json', '')

                                if toolUseId not in chat.tool_input_list:
                                    chat.tool_input_list[toolUseId] = ""
                                chat.tool_input_list[toolUseId] += partial_json
                                input = chat.tool_input_list[toolUseId]

                                chat.update_streaming_result(containers, f"Tool: {tool_name}, Input: {input}", "info")

        elif isinstance(stream[0], ToolMessage):
            message = stream[0]
            logger.info(f"ToolMessage: {message.name}, {message.content}")
            tool_name = message.name
            toolResult = message.content
            toolUseId = message.tool_call_id
            logger.info(f"toolResult: {toolResult}, toolUseId: {toolUseId}")
            chat.add_notification(containers, f"Tool Result: {toolResult}")
            tool_used = True

            content, urls, refs = chat.get_tool_info(tool_name, toolResult)
            if refs:
                for r in refs:
                    references.append(r)
                logger.info(f"refs: {refs}")
            if urls:
                for url in urls:
                    image_url.append(url)
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

    if containers is not None:
        containers['notification'][chat.index].markdown(result)

    return result
