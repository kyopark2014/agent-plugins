import os
import json
import yaml
import langgraph_agent
import mcp_config
import chat
import logging
import sys
import langgraph_agent

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, AIMessageChunk
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from dataclasses import dataclass, field
from typing import Literal, Optional

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


# ═══════════════════════════════════════════════════════════════════
#  PluginManager – load skills per plugin (see langgraph_agent.SkillManager)
# ═══════════════════════════════════════════════════════════════════

@dataclass
class PluginSkill:
    """Plugin skill metadata (Anthropic Agent Skills spec)."""
    name: str
    description: str
    instructions: str
    path: str


class PluginManager:
    """Manager that discovers and loads skills from the plugin directory."""

    def __init__(self, skills_dir: str):
        self.skills_dir = skills_dir
        self.registry: dict[str, PluginSkill] = {}
        self._discover(skills_dir)

    def _discover(self, skills_dir: str):
        """Scan the skills directory and load SKILL.md metadata into the registry."""
        if not os.path.isdir(skills_dir):
            return

        for entry in os.listdir(skills_dir):
            skill_md = os.path.join(skills_dir, entry, "SKILL.md")
            if os.path.isfile(skill_md):
                try:
                    meta, instructions = self._parse_skill_md(skill_md)
                    skill = PluginSkill(
                        name=meta.get("name", entry),
                        description=meta.get("description", ""),
                        instructions=instructions,
                        path=os.path.join(skills_dir, entry),
                    )
                    self.registry[skill.name] = skill
                    logger.info(f"Plugin skill discovered: {skill.name}")
                except Exception as e:
                    logger.warning(f"Failed to load plugin skill '{entry}': {e}")

    @staticmethod
    def _parse_skill_md(filepath: str) -> tuple[dict, str]:
        """Parse YAML frontmatter and markdown body from SKILL.md."""
        with open(filepath, "r", encoding="utf-8") as f:
            raw = f.read()

        if not raw.startswith("---"):
            return {}, raw

        parts = raw.split("---", 2)
        if len(parts) < 3:
            return {}, raw

        frontmatter = yaml.safe_load(parts[1]) or {}
        body = parts[2].strip()
        return frontmatter, body

    def get_skill_instructions(self, name: str) -> Optional[str]:
        """Return full instructions for the skill by name."""
        skill = self.registry.get(name)
        return skill.instructions if skill else None

    def available_skills_xml(self, skill_names: list[str]) -> str:
        """Generate <available_skills> XML for system prompt (metadata only)."""
        if not self.registry:
            return ""
        lines = ["<available_skills>"]
        for s in self.registry.values():
            if s.name in skill_names:
                lines.append("  <skill>")
                lines.append(f"    <name>{s.name}</name>")
                lines.append(f"    <description>{s.description}</description>")
                lines.append("  </skill>")
        lines.append("</available_skills>")
        return "\n".join(lines)


# Cache of PluginManager per plugin (plugin_name -> PluginManager)
_plugin_managers: dict[str, PluginManager] = {}

def available_plugins_list():
    plugin_dir = PLUGINS_DIR
    if not os.path.isdir(plugin_dir):
        return []
    
    plugin_list = []
    for plugin in os.listdir(plugin_dir):
        plugin_list.append({"name": plugin})
        
    return plugin_list


def load_plugin_mcp_servers_from_list(plugin_path: str) -> list:
    """Load MCP server names from plugin's mcp_servers.list file.

    Args:
        plugin_path: Absolute path to plugin directory (e.g. application/plugins/enterprise-search)

    Returns:
        List of MCP server names, or empty list if file not found.
    """
    list_path = os.path.join(plugin_path, "mcp_servers.list")
    if not os.path.isfile(list_path):
        logger.info(f"mcp_servers.list not found: {list_path}")
        return []
    try:
        with open(list_path, "r", encoding="utf-8") as f:
            servers = json.load(f)
        return servers if isinstance(servers, list) else []
    except Exception as e:
        logger.error(f"Failed to load mcp_servers.list from {list_path}: {e}")
        return []


def get_plugin_skills(plugin_name: str) -> list:
    """Return skill names that belong to the given plugin (from plugins/<name>/skills/)."""
    if plugin_name not in _plugin_managers:
        skills_dir = os.path.join(PLUGINS_DIR, plugin_name, "skills")
        _plugin_managers[plugin_name] = PluginManager(skills_dir)

    registry = _plugin_managers[plugin_name].registry

    if not registry:
        return []

    return [{"name": s.name, "description": s.description} for s in registry.values()]


def create_plugin_and_get_skill_instructions(plugin_name: str):
    """Create get_skill_instructions tool that uses the plugin's PluginManager.

    The builtin get_skill_instructions from langgraph_agent uses the global SkillManager
    (application/skills/), which does not include plugin skills (plugins/<name>/skills/).
    This tool uses the plugin's PluginManager so frontend-design and other plugin skills
    are found correctly.
    """
    plugin_manager = _plugin_managers.get(plugin_name)
    if plugin_name not in _plugin_managers:
        skills_dir = os.path.join(PLUGINS_DIR, plugin_name, "skills")
        _plugin_managers[plugin_name] = PluginManager(skills_dir)
        plugin_manager = _plugin_managers[plugin_name]

    @tool
    def get_skill_instructions(skill_name: str) -> str:
        """Load the full instructions for a specific skill by name.

        Use this when you need detailed instructions for a task that matches
        one of the available skills listed in the system prompt.

        Args:
            skill_name: The name of the skill to load (e.g. 'frontend-design').

        Returns:
            The full skill instructions, or an error message if not found.
        """
        logger.info(f"###### get_skill_instructions (plugin={plugin_name}): {skill_name} ######")
        instructions = plugin_manager.get_skill_instructions(skill_name)
        if instructions:
            return instructions
        available = ", ".join(plugin_manager.registry.keys())
        return f"Skill '{skill_name}' not found. Available skills: {available}"

    return get_skill_instructions


def load_plugin_mcp_config_from_json(plugin_path: str) -> dict:
    """Load MCP config from plugin's .mcp.json file.
    
    Args:
        plugin_path: Absolute path to plugin directory (e.g. application/plugins/enterprise-search)
    
    Returns:
        MCP config dict with mcpServers key, or empty dict if file not found.
    """
    import json
    mcp_path = os.path.join(plugin_path, ".mcp.json")
    if not os.path.isfile(mcp_path):
        logger.warning(f"Plugin MCP config not found: {mcp_path}")
        return {"mcpServers": {}}
    try:
        with open(mcp_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config if isinstance(config.get("mcpServers"), dict) else {"mcpServers": {}}
    except Exception as e:
        logger.error(f"Failed to load plugin MCP config from {mcp_path}: {e}")
        return {"mcpServers": {}}

def get_builtin_tools():
    """Return the list of built-in tools for the skill-aware agent."""
    return [langgraph_agent.execute_code, langgraph_agent.write_file, langgraph_agent.read_file, langgraph_agent.upload_file_to_s3, langgraph_agent.get_skill_instructions]

LOAD_MCP_CONFIG_WITH_SECRET_MANAGER = True  # use mcp_config.py to load MCP config where load credentials from secret manager

async def run_plugin_agent(query, plugin_name, containers):
    """Run plugin agent with MCP tools and skills."""
    chat.index = 0
    chat.streaming_index = 0

    image_url = []
    references = []

    # Load plugin MCP config from plugins/<plugin_name>/.mcp.json
    plugin_path = os.path.join(PLUGINS_DIR, plugin_name)
    
    # Load MCP servers for plugin
    if LOAD_MCP_CONFIG_WITH_SECRET_MANAGER:
        mcp_servers = load_plugin_mcp_servers_from_list(plugin_path)
        mcp_json = mcp_config.load_selected_config(mcp_servers)
        logger.info(f"plugin {plugin_name} mcp_json (from mcp_servers.list): {mcp_json}")
    else:
        mcp_json = load_plugin_mcp_config_from_json(plugin_path)
        logger.info(f"plugin {plugin_name} mcp_json (from .mcp.json): {mcp_json}")

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
            logger.info(f"get_tools() returned: {tools}")

            if tools is None:
                logger.error("tools is None - MCP client failed to get tools")
                tools = []

        except Exception as e:
            logger.error(f"Error creating MCP client or getting tools: {e}")
            tools = []

    # Use plugin-specific get_skill_instructions so plugin skills (e.g. frontend-design)
    # are found from plugins/<name>/skills/, not the global application/skills/
    builtin_tools = get_builtin_tools()
    skill_instruction = create_plugin_and_get_skill_instructions(plugin_name)

    # Replace with plugin-aware version that uses PluginManager in order to tool duplication
    tool_names = {t.name for t in tools}
    for bt in builtin_tools:
        if bt.name == "get_skill_instructions":            
            if "get_skill_instructions" not in tool_names:
                tools.append(skill_instruction)
                logger.info("Using plugin-specific get_skill_instructions")
        elif bt.name not in tool_names:
            tools.append(bt)
        else:
            logger.info(f"builtin_tool {bt.name} already in tools")

    # Get plugin-specific skills
    plugin_skills = get_plugin_skills(plugin_name)
    logger.info(f"plugin: {plugin_name}, skills: {plugin_skills}")

    tool_list = [tool.name for tool in tools] if tools else []
    logger.info(f"tool_list: {tool_list}")

    if not tools:
        logger.warning("No tools available for plugin")
        result = "MCP 설정을 확인하세요. 플러그인의 mcp_servers.list에 연결된 MCP 서버가 있는지 확인하세요."
        if containers is not None:
            containers['notification'][0].markdown(result)
        return result

    app = langgraph_agent.buildChatAgent(tools)
    config = {
        "recursion_limit": 100,
        "configurable": {
            "thread_id": f"plugin-{plugin_name}",
            "tools": tools,
            "skills": plugin_skills,
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
