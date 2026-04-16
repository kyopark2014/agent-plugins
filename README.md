# LangGraph에서 Plugin 활용하기

여기에서는 [Anthropic의 Plugin](https://code.claude.com/docs/en/plugins)을 [LangGraph](https://github.com/langchain-ai/langgraph)에서 활용하는 방법에 대해 설명합니다. Agent에서는 선택된 plugin의 [Skill](https://code.claude.com/docs/en/skills)을 이용해 사용자의 요청을 처리하는데, 외부의 데이터는 [Connector](https://platform.claude.com/docs/ko/agents-and-tools/mcp-connector)의 MCP를 이용해 가져옵니다. 여기에서는 [Notion](https://developers.notion.com/guides/mcp/mcp), [Tavily](https://docs.tavily.com/documentation/mcp), [Slack](https://github.com/kyopark2014/mcp/blob/main/mcp-slack.md), [RAG](./application/mcp_server_retrieve.py)와 같은 데이터 소스를 활용합니다. UI는 편의상 streamlit을 사용하고 있으며 외부와 접속시 CloudFront - ALB - EC2로 구성합니다. Production에서는 EC2를 ECS/EKS로 대체하여 scalability를 확보하거나, [AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html)와 같은 서버리스 형태로 구성할 수 있습니다.

<img width="1200" alt="image" src="https://github.com/user-attachments/assets/8bd9b991-f577-4bee-8c5f-520caecb041d" />



## Skills

[Agent Skills](https://agentskills.io/specification)은 AI agent에게 특정 작업 수행 방법을 가르치는 재사용 가능한 지침 패키지입니다. Agent skills는 효과적으로 context를 관리하기 위하여 discovery, activation, execution의 과정을 거칩니다. 정리하면 agent가 관련된 skill의 name과 description을 읽는 discovery를 수행한 후에, SKILL.md에 포함된 instruction을 읽는 activation을 수행합니다. Agent는 instruction을 수행하는데 필요하다면 관련된 파일(referenced file)을 읽거나 포함된 코드(bundled code)를 실행합니다. 각 스킬은 `SKILL.md` 파일로 구성되며, YAML 프론트매터(name, description)와 상세 지침(워크플로, 코드 패턴 등)으로 이루어져 있습니다.

### Progressive Disclosure

시스템 프롬프트에는 스킬의 **이름과 설명만** XML 형태로 포함하고, 상세 지침은 agent가 `get_skill_instructions` 도구를 호출하여 **필요할 때만** 로드합니다. 이를 통해 프롬프트 크기를 최소화하면서도 agent가 다양한 스킬을 활용할 수 있습니다.

```xml
<available_skills>
  <skill>
    <name>pdf</name>
    <description>PDF 파일 읽기/병합/분할/OCR/폼 처리 등</description>
  </skill>
  ...
</available_skills>
```

### 스킬의 구조

각 스킬은 `SKILL.md` 파일 하나가 핵심이며, 필요에 따라 `scripts/`, `references/`, `assets/` 등의 보조 폴더를 포함할 수 있습니다.

```text
application/skills/
├── pdf/
│   └── SKILL.md          # YAML 프론트매터 + 상세 지침
├── notion/
│   └── SKILL.md
└── retrieve/
    ├── SKILL.md
    └── scripts/          # 예: 보조 스크립트(execute_code 등에서 호출)
```

`SKILL.md`는 아래와 같이 YAML 프론트매터와 마크다운 본문으로 구성됩니다.

```markdown
---
name: pdf
description: PDF 파일 처리를 위한 스킬
---

# PDF Processing Guide

## Overview
이 가이드는 Python 라이브러리를 사용한 PDF 처리 작업을 다룹니다.
execute_code 도구로 아래의 Python 코드를 실행하세요.
...
```

### 스킬의 종류

스킬은 **베이스 스킬**과 **플러그인 스킬** 두 가지로 구분됩니다.

- **베이스 스킬** (`application/skills/`): **Agent** / **Agent (Chat)** 모드에서 사용합니다. 구현상 [`langgraph_agent.py`](./application/langgraph_agent.py)의 `selected_skill_info("base")`만 프롬프트에 넣습니다.

- **플러그인 스킬** (`application/plugins/<플러그인명>/skills/`): **해당 플러그인 이름의 모드**에서 선택됩니다. [`plugin_agent.py`](./application/plugin_agent.py)에서 베이스 스킬 목록과 `selected_skill_info(<플러그인명>)` 결과를 **합쳐** `<available_skills>`에 포함합니다 (`skill_mode`가 활성일 때).

| 스킬 (베이스) | 설명 |
|------|------|
| pdf | PDF 읽기/병합/분할/OCR/폼 처리 등 |
| notion | Notion API 페이지/DB/블록 관리 |
| memory-manager | MEMORY.md·memory/*.md 등 에이전트 메모리 관리 |
| pptx | .pptx 생성·편집·텍스트 추출 등 |
| myslide | AWS 테마 프레젠테이션 생성 |
| retrieve | Amazon Bedrock Knowledge Base RAG 검색 |
| skill-creator | 스킬 설계·구조화·패키징 가이드 |
| browser-use | 브라우저 자동화(탐색, 폼, 스크린샷, 추출) |
| graphify | 입력 → 지식 그래프·클러스터 → HTML/JSON/감사 리포트 |
| gog | Google Workspace CLI(Gmail, Calendar, Drive 등) |

| 플러그인 | 스킬 | 설명 |
|----------|------|------|
| productivity | memory-management | 이중 계층 메모리(CLAUDE.md + memory/)·내부 용어 해석 |
| productivity | task-management | 공유 `TASKS.md` 기반 작업 관리 |
| frontend-design | frontend-design | 고품질 프론트엔드 UI·컴포넌트 구현 가이드 |
| enterprise-search | search-strategy | 질의 분해·다중 소스 검색 오케스트레이션 |
| enterprise-search | knowledge-synthesis | 다중 소스 결과 통합·출처·신뢰도 요약 |
| enterprise-search | source-management | MCP 검색 소스 연결·우선순위·레이트 리밋 인지 |

### 스킬의 동작 흐름

[skill.py](./application/skill.py)에서 구현된 스킬의 동작 흐름은 다음과 같습니다.

1. **스킬 탐색**: `SkillManager`가 `application/skills/<스킬명>/SKILL.md`(베이스) 또는 `application/plugins/<플러그인>/skills/<스킬명>/SKILL.md`(플러그인)를 스캔해 레지스트리에 등록합니다. 메타데이터와 본문은 `Skill` 객체에 보관되며, 플러그인별로 `skill_managers`에 분리 저장됩니다.
2. **선택 필터**: `selected_skill_info()`가 [`application/config.json`](./application/config.json)의 `default_skills`(베이스)와 `plugin_skills.<플러그인명>`(플러그인 모드)에 따라 노출할 스킬만 고릅니다.
3. **프롬프트 구성**: `build_skill_prompt()`가 선택된 스킬의 이름·설명만 `<available_skills>` XML로 넣고, `WORKING_DIR`·`ARTIFACTS_DIR` 경로 안내를 덧붙입니다. 플러그인 **슬래시 커맨드** 모드에서는 `build_command_prompt()`가 `commands/<이름>.md`를 `get_command_instructions()`로 읽어 옵니다.
4. **지침 로드**: 모델이 `get_skill_instructions` 도구로 본문 지침을 요청하면, 등록된 `SkillManager`들에서 해당 이름을 찾아 반환합니다.
5. **작업 수행**: 지침에 따라 `execute_code`, `write_file` 등 에이전트 도구를 사용합니다.
6. **결과 전달**: 생성물이 있으면 S3 업로드 등 기존 도구 흐름으로 URL을 제공합니다.

`default_skills` / `plugin_skills`는 Streamlit UI에서도 체크박스로 바꿀 수 있으며, 앱은 설정을 `application/config.json`에 저장합니다. UI에서 **스킬 모드**(`chat.skill_mode`)가 꺼져 있으면 베이스/플러그인 모두 [`langgraph_agent.py`](./application/langgraph_agent.py)의 일반 시스템 프롬프트만 사용하고 스킬 XML·`get_skill_instructions`는 붙지 않습니다. 베이스 스킬 레지스트리는 Agent 모드 진입 시 `register_plugin_skills("base")`로 한 번 올려 둡니다([`app.py`](./application/app.py)).


## Plugin

Plugin은 아래와 같이 Skill을 이용해 동작하는데 외부의 연결은 MCP를 포함한 Connector로 구현하고 sub-agent를 활용할 수 있습니다.

```text
Plugin = Skills(행동 방식) + Connectors(외부 연결) + Slash Commands(명령어) + Sub-agents(하위 에이전트) 
```

| 구성 요소 | 역할 |
|----------|------|
| Skills | 특정 직무에 맞는 출력 형식과 행동 방식 정의 |
| Connectors | Google Drive, Slack, Salesforce 등 외부 도구 연결 |
| Slash Commands | 플러그인 `commands/*.md` 기반(예: enterprise-search의 `/search`) 구조화된 워크플로우 |
| Sub-agents | 복잡한 작업을 처리하는 하위 에이전트 |

### 플러그인 디렉터리 구조

각 플러그인은 `application/plugins/<플러그인명>/` 아래에 두며, 베이스 스킬과 동일하게 **`skills/<스킬명>/SKILL.md`**로 플러그인 전용 스킬을 둡니다. 추가로 MCP·슬래시 커맨드·문서를 같은 폴더에 함께 둡니다.

```text
application/plugins/
└── enterprise-search/
    ├── skills/                    # 플러그인 스킬 (베이스와 동일한 SKILL.md 규약)
    │   ├── search-strategy/
    │   │   └── SKILL.md
    │   └── knowledge-synthesis/
    │       └── SKILL.md
    ├── commands/                  # 슬래시 커맨드(파일명이 /search → search.md)
    │   ├── search.md
    │   └── digest.md
    ├── .mcp.json                  # Anthropic 플러그인 규약의 MCP 서버 정의(참고용)
    ├── mcp_servers.list           # 이 앱에서 선택할 MCP 서버 목록([mcp_config.py](./application/mcp_config.py) 연동)
    ├── CONNECTORS.md              # 연결 가능한 데이터 소스·커넥터 설명
    ├── .claude-plugin/
    │   └── plugin.json            # Claude Code 플러그인 메타데이터(upstream 호환)
    └── README.md
```

- **skills/**: 베이스와 같이 YAML 프론트매터 + 본문; [`plugin.py`](./application/plugin.py)의 `PluginManager`가 스캔합니다.
- **commands/**: `/<이름>` 입력 시 `get_command_instructions()`가 `commands/<이름>.md`를 읽습니다([`skill.py`](./application/skill.py)).
- **mcp_servers.list / .mcp.json**: 런타임에서는 UI에서 고른 MCP와 Secret Manager 등을 반영해 [`mcp_config.py`](./application/mcp_config.py)가 서버 파라미터를 구성합니다.
- **CONNECTORS.md**: 사람이 읽는 커넥터·도구 안내입니다.

### knowledge-work-plugins

Anthropic의 [knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)은 특정 직무 전문가로 만들어주는 오픈소스 플러그인입니다. 여기에서 제공하는 plugin은 아래와 같습니다.


| 플러그인 | 주요 기능 | 연동 도구 |
|----------|----------|-----------|
| 🗓️ productivity | 작업/캘린더/워크플로우 관리 | Slack, Notion, Jira, Asana 등 |
| 💼 sales | 영업 리서치, 콜 준비, 파이프라인 | HubSpot, Clay, ZoomInfo 등 |
| 🎧 customer-support | 티켓 분류, 응답 초안, 지식베이스 | Intercom, HubSpot, Guru 등 |
| 📋 product-management | 스펙 작성, 로드맵, 사용자 리서치 | Figma, Amplitude, Linear 등 |
| 📣 marketing | 콘텐츠 초안, 캠페인, 브랜드 관리 | Canva, Ahrefs, Klaviyo 등 |
| ⚖️ legal | 계약서 검토, NDA, 리스크 평가 | Box, Egnyte, Microsoft 365 |
| 💰 finance | 재무제표, 결산 관리 | Snowflake, BigQuery, Databricks |
| 📊 data | SQL 작성, 시각화, 통계 분석 | Snowflake, Hex, Amplitude |
| 🔍 enterprise-search | 이메일/채팅/문서 통합 검색 | Slack, Notion, Jira, Asana |
| 🧬 bio-research | 생명과학 R&D 가속화 | PubMed, ClinicalTrials.gov, ChEMBL |
| 🔧 cowork-plugin-management | 새 플러그인 생성 및 커스터마이징 | — |

해당 git을 다운로드한 후 `application/plugins`에 플러그인 폴더를 두는 방식으로 확장합니다.

```text
https://github.com/anthropics/knowledge-work-plugins
```

이 저장소에는 현재 **productivity**, **enterprise-search**, **frontend-design** 플러그인만 포함되어 있으며, 위 표의 나머지는 upstream 저장소에서 가져와 동일한 방식으로 추가할 수 있습니다.

### claude-plugins-official

[claude-plugins-official](https://github.com/anthropics/claude-plugins-official)에서 Claude Code에서 사용할 수 있는 다양한 플러그인을 활용할 수 있습니다. 여기에서 [frontend-design](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/frontend-design)는 프론트엔드 인터페이스를 자동으로 생성해주는 도구입니다.







## Plugin 기능 구현

[app.py](./application)은 streamlit UI에서 plugin을 선택하여 agent를 활용할 수 있도록 합니다. [application/plugins](https://github.com/kyopark2014/agent-plugins/tree/main/application/plugins)에는 knowledge-work-plugins와 claude-plugins-official에서 다운로드한 plugin들이 있습니다. 사용자가 streamlit에서 plugin을 선택하면 아래와 같이 plugin_agent에서 run_plugin_agent()가 실행됩니다.

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

[plugin_agent.py](./application/plugin_agent.py)에서는 plugin을 활용하여 agnet를 구현합니다. Anthropic에서는 plugin 폴더에 [.mcp.json](./application/plugins/enterprise-search/.mcp.json)와 같이 [CONNECTORS.md]((./application/plugins/enterprise-search/CONNECTORS.md)의 데이터 소스인 MCP를 지정하게 되어 있지만, 여기에서는 credential을 secret manager에서 가져오도록 [mcp_servers.list](./application/plugins/enterprise-search/mcp_servers.list)와 같이 MCP 서버를 리스트하고, [mcp_config.py](./application/mcp_config.py)에서 동적으로 mcp.json을 생성합니다. 

아래와 같이 MCP tool과 plugin skill를 가져와서 tool을 정의한 다음에 agent를 생성하고 astream을 이용해 결과를 얻습니다.

```python
mcp_servers = load_plugin_mcp_servers_from_list(plugin_path)
mcp_json = mcp_config.load_selected_config(mcp_servers)

server_params = langgraph_agent.load_multiple_mcp_server_parameters(mcp_json)
client = MultiServerMCPClient(server_params)
tools = await client.get_tools()

builtin_tools = plugin.get_builtin_tools()
tool_names = {tool.name for tool in tools}
for bt in builtin_tools:
    if bt.name not in tool_names:
        tools.append(bt)
    else:
        logger.info(f"builtin_tool {bt.name} already in tools")

app = langgraph_agent.buildChatAgent(tools)
config = {
    "recursion_limit": 100,
    "configurable": {
        "thread_id": f"plugin-{plugin_name}",
        "tools": tools,
        "system_prompt": None,            
        "plugin_name": plugin_name,
        "command": command
    }
}

inputs = {
    "messages": [HumanMessage(content=query)]
}

async for stream in app.astream(inputs, config, stream_mode="messages"):
    if content_item.get('type') == 'text':
    text_content = content_item.get('text', '')
```

[langgraph_agent.py](./application/langgraph_agent.py)에서는 skill 동작에 필요한 internal tool을 정의하고 있습니다. 여기에서 get_skill_instructions은 skill의 description을 리턴합니다.

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

[langgraph_agent.py](./application/langgraph_agent.py)의 call_model은 아래와 같이 tool가 skill에 대한 정보를 가지고 system_prompt를 생성합니다.

```python
async def call_model(state: State, config):
    last_message = state['messages'][-1]

    tools = config.get("configurable", {}).get("tools", None)
    custom_prompt = config.get("configurable", {}).get("system_prompt", None)
    plugin_name = config.get("configurable", {}).get("plugin_name", None)    
    command = config.get("configurable", {}).get("command", None)    
    system = build_system_prompt(custom_prompt, plugin_name, command)
    
    reasoning_mode = getattr(chat, 'reasoning_mode', 'Disable')
    chatModel = chat.get_chat(extended_thinking=reasoning_mode)
    model = chatModel.bind_tools(tools)
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        MessagesPlaceholder(variable_name="messages"),
    ])
    chain = prompt | model
    response = await chain.ainvoke({"messages": messages})

    return {"messages": [response], "image_url": image_url}
```

아래와 같이 system prompt에는 WORKING_DIR와 ARTIFACTS_DIR와 같은 path를 포함하고 skill 정보를 포함합니다.

```python
SKILL_USAGE_GUIDE = (
    "\n## Skill 사용 가이드\n"
    "위의 <available_skills>에 나열된 skill이 사용자의 요청과 관련될 때:\n"
    "1. 먼저 get_skill_instructions 도구로 해당 skill의 상세 지침을 로드하세요.\n"
    "2. 지침에 포함된 코드 패턴을 execute_code 도구로 실행하세요.\n"
    "3. skill 지침이 없는 일반 질문은 직접 답변하세요.\n"
)

def build_system_prompt(custom_prompt: Optional[str] = None, skills: Optional[list] = None) -> str:
    """Assemble the full system prompt with available skills metadata."""
    if custom_prompt:
        base = custom_prompt
    else:
        base = BASE_SYSTEM_PROMPT

    path_info = (
        f"\n## 경로 (write_file, read_file 시 절대 경로 사용 권장)\n"
        f"- WORKING_DIR: {WORKING_DIR}\n"
        f"- ARTIFACTS_DIR: {ARTIFACTS_DIR}\n"
        f"예: write_file(filepath='{os.path.join(ARTIFACTS_DIR, 'report.drawio')}', content='...')\n\n"
        f"## write_file 규칙 (필수)\n"
        f"write_file 호출 시 filepath와 content를 반드시 함께 전달하세요. content 없이 호출하면 오류가 발생합니다.\n"
        f"다이어그램(.drawio) 등 대용량 파일도 content에 전체 내용을 담아 한 번에 전달해야 합니다.\n"
    )
    skills_xml = skill_manager.available_skills_xml(skills)
    if skills_xml:
        return f"{base}\n{path_info}\n\n{skills_xml}\n{SKILL_USAGE_GUIDE}"
    return f"{base}\n{path_info}"
```

Skill 정보는 아래와 같이 SkillManager에서 skill에 대한 name과 description 정보를 포함합니다.

```python
def get_skills_xml(skill_info: list) -> str:
    lines = ["<available_skills>"]
    for s in skill_info:
        lines.append("  <skill>")
        lines.append(f"    <name>{s['name']}</name>")
        lines.append(f"    <description>{s['description']}</description>")
        lines.append("  </skill>")
    lines.append("</available_skills>")
    return "\n".join(lines)
```

### Command 구현

Claude Pluggin의 주요기능중 하나인 Command는 슬랙시(/)을 통해 command와 명령을 전달할 수 있습니다. [knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)의 enterprise-search에는 [search.md](./application/plugins/enterprise-search/commands/search.md)에서는 한번의 query로 연결된 모든 MCP를 조회하는 기능을 제공합니다. 또한 [digest.md](./application/plugins/enterprise-search/commands/digest.md)에서는 Connector에 연결된 데이터소스들의 최근 활동을 모아서 보여주는 기능을 제공합니다. 이런 기능을 활용하기 위하여 [plugin.py](./application/plugin.py)와 같이 query에 슬랙시(/)가 있는 경우에 첫번째 단어가 command인지 확인합니다. 이때 선택된 plugin에 실제 command에 해당하는 md 파일이 있는지 확인합니다.

```python
command = None
if plugin.is_command(query, plugin_name):
    command = query.split(" ")[0].lstrip("/")
    logger.info(f"command: {command}")

def is_command(query: str, plugin_name: str) -> bool:
    """Check if the query is a command."""
    if plugin_name == "base":
        return False
    if not query.startswith("/"):
        return False
    command = query.split(" ")[0]
    command_name = command.lstrip("/").lower()  
    commands_dir = os.path.join(PLUGINS_DIR, plugin_name, "commands")
    if not os.path.isdir(commands_dir):
        return False
    commands = os.listdir(commands_dir)
    if command_name + ".md" not in commands:
        return False
    else:
        return True
```

[plugin_agent.py](./application/plugin_agent.py)와 같이 Command를 가지고 있으면 아래와 같이 agent를 생성할 때에 command를 전달합니다.

```python
app = langgraph_agent.buildChatAgentWithHistory(tools)
config = {
    "recursion_limit": 100,
    "configurable": {
        "thread_id": f"plugin-{plugin_name}",
        "tools": tools,
        "system_prompt": None,            
        "plugin_name": plugin_name,
        "command": command
    }
}
```

[langgraph_agent.py](./application/langgraph_agent.py)의 call_model에서는 command를 가지고 system prompt를 생성합니다.

```python
async def call_model(state: State, config):
    last_message = state['messages'][-1]

    plugin_name = config.get("configurable", {}).get("plugin_name", None)    
    command = config.get("configurable", {}).get("command", None)    
    system = build_system_prompt(custom_prompt, plugin_name, command)
    
    reasoning_mode = getattr(chat, 'reasoning_mode', 'Disable')
    chatModel = chat.get_chat(extended_thinking=reasoning_mode)
    model = chatModel.bind_tools(tools)

     prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        MessagesPlaceholder(variable_name="messages"),
    ])
    chain = prompt | model
    response = await chain.ainvoke({"messages": messages})
```    

Command를 위한 system prompt는 plugin으로 부터 command에 대한 description을 추가하고 COMMAND_USAGE_GUIDE를 추가하는 방법으로 아래와 같이 구현합니다.

```python
COMMAND_USAGE_GUIDE = (
    "\n## Command 사용 가이드\n"
    "위의 <command_instructions>에 따라 사용자 요청을 처리하세요.\n"
    "필요한 경우 get_skill_instructions로 skill 지침을 추가 로드하거나, execute_code, write_file 등 도구를 사용하세요.\n"
)

def build_command_prompt(plugin_name: str, command: str) -> str:
    """Build prompt for command mode: path info, command instructions, and available skills."""
    skill_info = selected_skill_info(plugin_name)

    if plugin_name != "base":
        default_skill_info = selected_skill_info("base")
        if default_skill_info:
            skill_info.extend(default_skill_info)

    path_info = (
        f"## Paths (use absolute paths for write_file, read_file)\n"
        f"- WORKING_DIR: {WORKING_DIR}\n"
        f"- ARTIFACTS_DIR: {ARTIFACTS_DIR}\n"
        f"Example: write_file(filepath='{os.path.join(ARTIFACTS_DIR, 'report.drawio')}', content='...')\n\n"
    )

    command_instructions = get_command_instructions(plugin_name, command)
    command_section = f"## Command Instructions\n<command_instructions>\n{command_instructions}\n</command_instructions>\n\n"

    skills_xml = get_skills_xml(skill_info)
    skills_section = f"{skills_xml}\n" if skills_xml else ""

    return f"{SKILL_SYSTEM_PROMPT}\n{path_info}\n{command_section}\n{skills_section}\n{COMMAND_USAGE_GUIDE}"
```

### MCP

Plugin의 Connector는 MCP를 이용해 구현합니다. 이때 필요한 MCP 설정은 아래를 참조합니다. 

- [Slack](https://github.com/kyopark2014/mcp/blob/main/mcp-slack.md): Slack 내용을 조회하고 메시지를 보낼 수 있습니다. SLACK_TEAM_ID, SLACK_BOT_TOKEN으로 설정합니다.

- [Tavily](https://github.com/kyopark2014/mcp/blob/main/mcp-tavily.md): Tavily를 이용해 인터넷을 검색합니다. [installer.py](./installer.py)에서 secret으로 설정후에 [utils.py](./application/utils.py)에서 TAVILY_API_KEY로 등록하여 활용합니다.

- [RAG](https://github.com/kyopark2014/mcp/blob/main/mcp-rag.md): Knowledge Base를 이용해 RAG를 활용합니다. IAM 인증을 이용하므로 별도로 credential 설정하지 않습니다.

- [web_fetch](https://github.com/kyopark2014/mcp/blob/main/mcp-web-fetch.md): playwright기반으로 url의 문서를 markdown으로 불러올 수 있습니다. 별도 인증이 필요하지 않습니다.

- [Google 메일/캘린더](https://github.com/kyopark2014/mcp/blob/main/mcp-gog.md): 구글 메일을 조회하거나 보낼 수 있습니다. Gog CLI를 설치하여 google 인증을 통해 활용합니다.

- [Notion](https://github.com/kyopark2014/mcp/blob/main/mcp-notion.md): Notion을 읽거나 쓸 수 있습니다. [installer.py](./installer.py)에서 secret으로 설정후에 [utils.py](./application/utils.py)에서 NOTION_TOKEN을 등록하여 활용합니다.

- [text_extraction](https://github.com/kyopark2014/mcp/blob/main/mcp-text-extraction.md): 이미지의 텍스트를 추출합니다. 별도 인증이 필요하지 않습니다.

  

### 배포하기

AWS console의 EC2로 접속하여 [Launch an instance](https://us-west-2.console.aws.amazon.com/ec2/home?region=us-west-2#Instances:)를 선택합니다. [Launch instance]를 선택한 후에 적당한 Name을 입력합니다. (예: es) key pair은 "Proceed without key pair"을 선택하고 넘어갑니다. 

<img width="700" alt="ec2이름입력" src="https://github.com/user-attachments/assets/c551f4f3-186d-4256-8a7e-55b1a0a71a01" />

Instance가 준비되면 [Connet] - [EC2 Instance Connect]를 선택하여 아래처럼 접속합니다. 

<img width="700" alt="image" src="https://github.com/user-attachments/assets/e8a72859-4ac7-46af-b7ae-8546ea19e7a6" />

이후 아래와 같이 python, pip, git, boto3를 설치합니다.

```text
sudo yum install python3 python3-pip git docker -y
pip install boto3
```

Workshop의 경우에 아래 형태로 된 Credential을 복사하여 EC2 터미널에 입력합니다.

<img width="700" alt="credential" src="https://github.com/user-attachments/assets/261a24c4-8a02-46cb-892a-02fb4eec4551" />

아래와 같이 git source를 가져옵니다.

```python
git clone https://github.com/kyopark2014/agent-plugins
```

아래와 같이 installer.py를 이용해 설치를 시작합니다.

```python
cd agent-plugins && python3 installer.py
```

API 구현에 필요한 credential은 secret으로 관리합니다. 따라서 설치시 필요한 credential 입력이 필요한데 아래와 같은 방식을 활용하여 미리 credential을 준비합니다. 

- 일반 인터넷 검색: [Tavily Search](https://app.tavily.com/sign-in)에 접속하여 가입 후 API Key를 발급합니다. 이것은 tvly-로 시작합니다.  
- 날씨 검색: [openweathermap](https://home.openweathermap.org/api_keys)에 접속하여 API Key를 발급합니다. 이때 price plan은 "Free"를 선택합니다.

설치가 완료되면 CloudFront로 접속하여 Agent를 실행합니다.

<img width="500" alt="cloudfront_address" src="https://github.com/user-attachments/assets/7ab1a699-eefb-4b55-b214-23cbeeeb7249" />

인프라가 더이상 필요없을 때에는 uninstaller.py를 이용해 제거합니다.

```text
python uninstaller.py
```


## 실행결과


왼쪽 메뉴에서 "frontend-design"을 선택한 후에 아래와 같이 "LLM에 맞는 챗봇 UI를 디자인해주세요."라고 입력하면, get_skill_instructions이 frontend-design의 description을 읽어오고, 이를 바탕으로 챗봇 UI를 생성합니다.

<img width="800" alt="image" src="https://github.com/user-attachments/assets/04a25576-578d-4299-af0e-ec7b80411e1f" />


생성된 Frontend UI는 아래와 같습니다.

<img width="1000" alt="image" src="https://github.com/user-attachments/assets/671180f0-dbc0-46eb-b3ee-cf73b2cde5c7" />



Plugin의 command을 쓰고자 할 때에는 enterprise-search와 같은 plugin을 선택한 후에 아래와 같이 "/search claude의 cowork에서 활용하는 plugin 기능에 대해 설명하고 이를 ppt로 정리하세요."라고 입력합니다. 이렇게 하면 [search.md](./application/plugins/enterprise-search/commands/search.md)에 정의된 search를 이용해 Connector에 있는 MCP들을 조회한 후에 ppt를 생성할 수 있습니다.

