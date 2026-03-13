# Using Plugins with LangGraph

This repository shows how to use [Anthropic's Plugins](https://code.claude.com/docs/en/plugins) with [LangGraph](https://github.com/langchain-ai/langgraph). The agent processes user requests using the [Skill](https://code.claude.com/docs/en/skills) of the selected plugin, and fetches external data via MCP in [Connectors](https://claude.com/connectors#connectors). Data sources used here include [Notion](https://developers.notion.com/guides/mcp/mcp), [Tavily](https://docs.tavily.com/documentation/mcp), [Slack](https://github.com/kyopark2014/mcp/blob/main/mcp-slack.md), and [RAG](./application/mcp_server_retrieve.py). The UI uses Streamlit for convenience, and external access is configured as CloudFront - ALB - EC2. In production, EC2 can be replaced with ECS/EKS for scalability, or a serverless setup such as [AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html) can be used.

<img width="1200" alt="image" src="https://github.com/user-attachments/assets/8bd9b991-f577-4bee-8c5f-520caecb041d" />


## Plugin

Plugins operate using Skills, with external connections implemented through Connectors including MCP, and can leverage sub-agents.

```text
Plugin = Skills(behavior patterns) + Connectors(external connections) + Slash Commands(commands) + Sub-agents(sub-agents)
```

| Component | Role |
|----------|------|
| Skills | Define output formats and behavior patterns for specific job functions |
| Connectors | Connect to external tools such as Google Drive, Slack, Salesforce |
| Slash Commands | Execute structured workflows like /sales:call-prep, /generate-report |
| Sub-agents | Sub-agents that handle complex tasks |

The following describes the plugin repositories provided by Anthropic.

### knowledge-work-plugins

Anthropic's [knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) is an open-source plugin that turns you into a domain expert for specific job functions. The plugins provided are as follows.


| Plugin | Main Features | Integrated Tools |
|----------|----------|-----------|
| 🗓️ productivity | Task/calendar/workflow management | Slack, Notion, Jira, Asana, etc. |
| 💼 sales | Sales research, call prep, pipeline | HubSpot, Clay, ZoomInfo, etc. |
| 🎧 customer-support | Ticket classification, response drafts, knowledge base | Intercom, HubSpot, Guru, etc. |
| 📋 product-management | Spec writing, roadmap, user research | Figma, Amplitude, Linear, etc. |
| 📣 marketing | Content drafts, campaigns, brand management | Canva, Ahrefs, Klaviyo, etc. |
| ⚖️ legal | Contract review, NDA, risk assessment | Box, Egnyte, Microsoft 365 |
| 💰 finance | Financial statements, closing management | Snowflake, BigQuery, Databricks |
| 📊 data | SQL writing, visualization, statistical analysis | Snowflake, Hex, Amplitude |
| 🔍 enterprise-search | Integrated search across email/chat/documents | Slack, Notion, Jira, Asana |
| 🧬 bio-research | Life sciences R&D acceleration | PubMed, ClinicalTrials.gov, ChEMBL |
| 🔧 cowork-plugin-management | Create and customize new plugins | — |

Download the repository and copy it to application/plugins.

```python
https://github.com/anthropics/knowledge-work-plugins
```

### claude-plugins-official

[claude-plugins-official](https://github.com/anthropics/claude-plugins-official) provides various plugins for use in Claude Code. [frontend-design](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/frontend-design) is a tool that automatically generates frontend interfaces.


## Plugin Implementation

[app.py](./application) enables plugin selection from the Streamlit UI to use the agent. [application/plugins](https://github.com/kyopark2014/agent-plugins/tree/main/application/plugins) contains plugins downloaded from knowledge-work-plugins and claude-plugins-official. When a user selects a plugin in Streamlit, `run_plugin_agent()` is executed in plugin_agent as follows.

```python
containers = {
    "tools": st.empty(),
    "status": st.empty(),
    "notification": [st.empty() for _ in range(500)]
}
response = asyncio.run(plugin_agent.run_plugin_agent(
    query=prompt, 
    plugin_name=plugin["name"],
    containers=containers))
logger.info(f"response: {response}")
st.session_state.messages.append({"role": "assistant", "content": response})
```

[plugin_agent.py](./application/plugin_agent.py) implements the agent using plugins. Anthropic specifies MCP data sources from [CONNECTORS.md]((./application/plugins/enterprise-search/CONNECTORS.md) in the plugin folder via [.mcp.json](./application/plugins/enterprise-search/.mcp.json), but here MCP servers are listed in [mcp_servers.list](./application/plugins/enterprise-search/mcp_servers.list) to fetch credentials from the secret manager, and [mcp_config.py](./application/mcp_config.py) dynamically generates mcp.json.

MCP tools and plugin skills are loaded, tools are defined, the agent is created, and results are obtained via astream as follows.

```python
mcp_servers = load_plugin_mcp_servers_from_list(plugin_path)
mcp_json = mcp_config.load_selected_config(mcp_servers)

server_params = langgraph_agent.load_multiple_mcp_server_parameters(mcp_json)
client = MultiServerMCPClient(server_params)

builtin_tools = get_builtin_tools()
plugin_skills = get_plugin_skills(plugin_name)
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

async for stream in app.astream(inputs, config, stream_mode="messages"):
    if content_item.get('type') == 'text':
    text_content = content_item.get('text', '')
```

[langgraph_agent.py](./application/langgraph_agent.py) defines internal tools required for skill behavior. Here, `get_skill_instructions` returns the skill description.

```python
@tool
def get_skill_instructions(skill_name: str) -> str:
    """Load the full instructions for a specific skill by name.

    Use this when you need detailed instructions for a task that matches
    one of the available skills listed in the system prompt.

    Args:
        skill_name: The name of the skill to load (e.g. 'pdf').

    Returns:
        The full skill instructions, or an error message if not found.
    """
    instructions = skill_manager.get_skill_instructions(skill_name)
    return instructions
```

In [langgraph_agent.py](./application/langgraph_agent.py), `call_model` generates the system_prompt using tool and skill information as follows.

```python
async def call_model(state: State, config):
    last_message = state['messages'][-1]

    tools = config.get("configurable", {}).get("tools", None)
    skills = config.get("configurable", {}).get("skills", None)
    custom_prompt = config.get("configurable", {}).get("system_prompt", None)
    system = build_system_prompt(custom_prompt, skills)

    chatModel = chat.get_chat(extended_thinking=reasoning_mode)
    model = chatModel.bind_tools(tools)
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        MessagesPlaceholder(variable_name="messages"),
    ])
    chain = prompt | model

    response = await chain.ainvoke(messages)
    return {"messages": [response]}
```

The system prompt includes paths such as WORKING_DIR and ARTIFACTS_DIR and skill information as follows.

```python
SKILL_USAGE_GUIDE = (
    "\n## Skill Usage Guide\n"
    "When a skill listed in <available_skills> above is relevant to the user's request:\n"
    "1. First load the detailed instructions for that skill using the get_skill_instructions tool.\n"
    "2. Execute the code patterns included in the instructions using the execute_code tool.\n"
    "3. For general questions without skill instructions, answer directly.\n"
)

def build_system_prompt(custom_prompt: Optional[str] = None, skills: Optional[list] = None) -> str:
    """Assemble the full system prompt with available skills metadata."""
    if custom_prompt:
        base = custom_prompt
    else:
        base = BASE_SYSTEM_PROMPT

    path_info = (
        f"\n## Paths (use absolute paths when calling write_file, read_file)\n"
        f"- WORKING_DIR: {WORKING_DIR}\n"
        f"- ARTIFACTS_DIR: {ARTIFACTS_DIR}\n"
        f"Example: write_file(filepath='{os.path.join(ARTIFACTS_DIR, 'report.drawio')}', content='...')\n\n"
        f"## write_file Rules (required)\n"
        f"When calling write_file, always pass both filepath and content. Calling without content will cause an error.\n"
        f"For large files such as diagrams (.drawio), include the full content in content and pass it in a single call.\n"
    )
    skills_xml = skill_manager.available_skills_xml(skills)
    if skills_xml:
        return f"{base}\n{path_info}\n\n{skills_xml}\n{SKILL_USAGE_GUIDE}"
    return f"{base}\n{path_info}"
```

Skill information includes name and description for each skill from SkillManager as follows.

```python
def available_skills_xml(self, skills: list[Skill]) -> str:
    """Generate <available_skills> XML for the system prompt (metadata only)."""
    if not self.registry:
        return ""
    lines = ["<available_skills>"]
    for s in self.registry.values():
        if s.name in skills:
            lines.append("  <skill>")
            lines.append(f"    <name>{s.name}</name>")
            lines.append(f"    <description>{s.description}</description>")
            lines.append("  </skill>")
    lines.append("</available_skills>")
    return "\n".join(lines)
```

## Execution Results


After selecting "frontend-design" from the left menu and entering "Design a chatbot UI suitable for LLMs.", `get_skill_instructions` loads the frontend-design description and generates the chatbot UI based on it.

<img width="800" alt="image" src="https://github.com/user-attachments/assets/04a25576-578d-4299-af0e-ec7b80411e1f" />


The generated Frontend UI is as follows.

<img width="1000" alt="image" src="https://github.com/user-attachments/assets/671180f0-dbc0-46eb-b3ee-cf73b2cde5c7" />
