import logging
import sys
import os
import traceback
import chat
import utils
import skill
import mcp_config

from typing import Literal, Optional

from langgraph.prebuilt import ToolNode
from langgraph.graph import START, END, StateGraph
from typing_extensions import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, AIMessageChunk
from langchain_mcp_adapters.client import MultiServerMCPClient

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d | %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("agent")

config = utils.load_config()
sharing_url = config.get("sharing_url")
s3_prefix = "docs"
capture_prefix = "captures"
user_id = "langgraph"

# ═══════════════════════════════════════════════════════════════════
#  Agent State & System Prompt
# ═══════════════════════════════════════════════════════════════════
class State(TypedDict):
    messages: Annotated[list, add_messages]
    image_url: list

BASE_SYSTEM_PROMPT = (
    "당신의 이름은 서연이고, 질문에 친근한 방식으로 대답하도록 설계된 대화형 AI입니다.\n"
    "상황에 맞는 구체적인 세부 정보를 충분히 제공합니다.\n"
    "모르는 질문을 받으면 솔직히 모른다고 말합니다.\n"
    "한국어로 답변하세요.\n"

    "An agent orchestrates the following workflow:\n"
    "1. Receives user input\n"
    "2. Processes the input using a language model\n"
    "3. Decides whether to use tools to gather information or perform actions\n"
    "4. Executes those tools and receives results\n"
    "5. Continues reasoning with the new information\n"
    "6. Produces a final response\n"
)

MEMORY_SYSTEM_PROMPT = (
    "## 메모리 관리\n"
    "사용자에 대한 정보를 기억하거나, 과거 대화/결정/선호를 찾을 때는 반드시 메모리 도구를 사용하세요:\n"
    "- memory_search: 메모리 파일(MEMORY.md, memory/*.md)에서 키워드 검색\n"
    "- memory_get: 특정 메모리 파일 읽기 (예: memory_get(path='MEMORY.md'))\n"
    "- write_file: filepath와 content를 반드시 함께 전달. content 생략 시 실패. 절대 content 없이 호출하지 말 것\n\n"
    "정보를 기억해달라는 요청 시:\n"
    "1. memory_get으로 MEMORY.md와 오늘의 일일 로그를 읽는다\n"
    "2. write_file로 MEMORY.md(장기 메모리)와 memory/YYYY-MM-DD.md(일일 로그) 모두에 저장한다\n"
    "3. execute_code로 파일을 직접 쓰지 말고, 반드시 write_file 도구를 사용한다\n\n"
    "과거 정보를 질문받을 때:\n"
    "1. 먼저 memory_search로 관련 정보를 검색한다\n"
    "2. memory_get으로 상세 내용을 확인한 뒤 답변한다\n"
)

def build_system_prompt(custom_prompt: Optional[str] = None, plugin_name: Optional[str] = None) -> str:
    """Assemble the full system prompt with available skills metadata."""
    if custom_prompt:
        base = custom_prompt
    elif plugin_name:
        base = skill.build_skill_prompt(plugin_name)
    else:
        base = BASE_SYSTEM_PROMPT

    return base

# ═══════════════════════════════════════════════════════════════════
#  LangGraph Nodes
# ═══════════════════════════════════════════════════════════════════
async def call_model(state: State, config):
    logger.info(f"###### call_model ######")

    last_message = state['messages'][-1]
    # logger.info(f"last message: {last_message}")

    image_url = state.get('image_url', [])

    tools = config.get("configurable", {}).get("tools", None)
    custom_prompt = config.get("configurable", {}).get("system_prompt", None)
    plugin_name = config.get("configurable", {}).get("plugin_name", None)
    logger.info(f"plugin_name: {plugin_name}")
    
    system = build_system_prompt(custom_prompt, plugin_name)
    logger.info(f"system prompt: {system}")

    reasoning_mode = getattr(chat, 'reasoning_mode', 'Disable')
    chatModel = chat.get_chat(extended_thinking=reasoning_mode)

    if tools is None:
        logger.warning("tools is None, using empty list")
        tools = []

    model = chatModel.bind_tools(tools)

    try:
        messages = []
        for msg in state["messages"]:
            if isinstance(msg, ToolMessage):
                content = msg.content
                if isinstance(content, list):
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict):
                            item_clean = {k: v for k, v in item.items() if k != 'id'}
                            if 'text' in item_clean:
                                text_parts.append(item_clean['text'])
                            elif 'content' in item_clean:
                                text_parts.append(str(item_clean['content']))
                        elif isinstance(item, str):
                            text_parts.append(item)
                    content = '\n'.join(text_parts) if text_parts else str(content)
                elif not isinstance(content, str):
                    content = str(content)

                tool_msg = ToolMessage(
                    content=content,
                    tool_call_id=msg.tool_call_id
                )
                messages.append(tool_msg)
            else:
                messages.append(msg)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system),
            MessagesPlaceholder(variable_name="messages"),
        ])
        chain = prompt | model

        response = await chain.ainvoke(messages)
        logger.info(f"response of call_model: {response}")

    except Exception:
        response = AIMessage(content="답변을 찾지 못하였습니다.")
        err_msg = traceback.format_exc()
        logger.info(f"error message: {err_msg}")

    return {"messages": [response], "image_url": image_url}


async def should_continue(state: State, config) -> Literal["continue", "end"]:
    logger.info(f"###### should_continue ######")

    messages = state["messages"]
    last_message = messages[-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        tool_name = last_message.tool_calls[-1]['name']
        logger.info(f"--- CONTINUE: {tool_name} ---")

        tool_args = last_message.tool_calls[-1]['args']

        if last_message.content:
            logger.info(f"last_message: {last_message.content}")

        logger.info(f"tool_name: {tool_name}, tool_args: {tool_args}")
        return "continue"
    else:
        logger.info(f"--- END ---")
        return "end"

async def plan_node(state: State, config):
    logger.info(f"###### plan_node ######")
    containers = config.get("configurable", {}).get("containers", None)
    system = (
        "For the given objective, come up with a simple step by step plan."
        "This plan should involve individual tasks, that if executed correctly will yield the correct answer."
        "Do not add any superfluous steps."
        "The result of the final step should be the final answer. Make sure that each step has all the information needed."
        "The plan should be returned in <plan> tag."
    )

    chatModel = chat.get_chat(extended_thinking="Disable")

    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", system),
            MessagesPlaceholder(variable_name="messages"),
        ])
        chain = prompt | chatModel

        result = await chain.ainvoke(state["messages"])

        plan = result.content[result.content.find('<plan>')+6:result.content.find('</plan>')]
        logger.info(f"plan: {plan}")

        plan = plan.strip()
        response = HumanMessage(content="다음의 plan을 참고하여 답변하세요.\n" + plan)

        if containers is not None:
            chat.add_notification(containers, '계획:\n' + plan)

    except Exception:
        response = HumanMessage(content="")
        err_msg = traceback.format_exc()
        logger.info(f"error message: {err_msg}")

    return {"messages": [response]}


# ═══════════════════════════════════════════════════════════════════
#  Agent Builders
# ═══════════════════════════════════════════════════════════════════

def buildChatAgent(tools):
    tool_node = ToolNode(tools, handle_tool_errors=True)

    workflow = StateGraph(State)

    workflow.add_node("agent", call_model)
    workflow.add_node("action", tool_node)
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"continue": "action", "end": END},
    )
    workflow.add_edge("action", "agent")

    return workflow.compile()


def buildChatAgentWithPlan(tools):
    tool_node = ToolNode(tools)

    workflow = StateGraph(State)

    workflow.add_node("plan", plan_node)
    workflow.add_node("agent", call_model)
    workflow.add_node("action", tool_node)
    workflow.add_edge(START, "plan")
    workflow.add_edge("plan", "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"continue": "action", "end": END},
    )
    workflow.add_edge("action", "agent")

    return workflow.compile()


def buildChatAgentWithHistory(tools):
    tool_node = ToolNode(tools, handle_tool_errors=True)

    workflow = StateGraph(State)

    workflow.add_node("agent", call_model)
    workflow.add_node("action", tool_node)
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"continue": "action", "end": END},
    )
    workflow.add_edge("action", "agent")

    return workflow.compile(
        checkpointer=chat.checkpointer,
        store=chat.memorystore
    )

# ═══════════════════════════════════════════════════════════════════
#  MCP Server Utilities
# ═══════════════════════════════════════════════════════════════════
def load_multiple_mcp_server_parameters(mcp_json: dict):
    mcpServers = mcp_json.get("mcpServers")

    server_info = {}
    if mcpServers is not None:
        for server_name, cfg in mcpServers.items():
            if cfg.get("type") in ("streamable_http", "http"):
                server_info[server_name] = {
                    "transport": "streamable_http",
                    "url": cfg.get("url"),
                    "headers": cfg.get("headers", {})
                }
            else:
                server_info[server_name] = {
                    "transport": "stdio",
                    "command": cfg.get("command", ""),
                    "args": cfg.get("args", []),
                    "env": cfg.get("env", {})
                }
    return server_info

async def run_langgraph_agent(query: str, mcp_servers: list, plugin_name: Optional[str]=None, history_mode: str="Disable", containers: Optional[dict]=None) -> tuple[str, list]:
    chat.index = 0
    chat.streaming_index = 0

    image_url = []
    references = []

    # mcp
    mcp_json = mcp_config.load_selected_config(mcp_servers)
    logger.info(f"mcp_json: {mcp_json}")

    server_params = load_multiple_mcp_server_parameters(mcp_json)
    logger.info(f"server_params: {server_params}")    

    try:
        client = MultiServerMCPClient(server_params)
        logger.info(f"MCP client created successfully")
        
        tools = await client.get_tools()
        # logger.info(f"get_tools() returned: {tools}")

        # skill
        builtin_tools = skill.get_builtin_tools()
        # logger.info(f"builtin_tools: {builtin_tools}")

        if chat.skill_mode == "Enable":        
            tool_names = {tool.name for tool in tools}
            for bt in builtin_tools:
                if bt.name not in tool_names:
                    tools.append(bt)
                else:
                    logger.info(f"builtin_tool {bt.name} already in tools")
            
        if tools is None:
            logger.error("tools is None - MCP client failed to get tools")
            tools = []
        
        tool_list = [tool.name for tool in tools] if tools else []
        logger.info(f"tool_list: {tool_list}")
        
    except Exception as e:
        logger.error(f"Error creating MCP client or getting tools: {e}")                        
        tools = []
        tool_list = []        

    # If no tools available, use general conversation
    if not tools:
        logger.warning("No tools available, using general conversation mode")
        result = "MCP 설정을 확인하세요."
        if containers is not None:
            containers['notification'][0].markdown(result)
        return result, image_url
    
    if history_mode == "Enable":
        app = buildChatAgentWithHistory(tools)
        config = {
            "recursion_limit": 100,
            "configurable": {"thread_id": user_id},
            "tools": tools,
            "plugin_name": plugin_name,
            "system_prompt": None
        }
    else:
        app = buildChatAgent(tools)
        config = {
            "recursion_limit": 100,
            "configurable": {"thread_id": user_id},
            "tools": tools,
            "plugin_name": plugin_name,
            "system_prompt": None
        }        
    
    inputs = {
        "messages": [HumanMessage(content=query)]
    }
            
    result = ""
    tool_used = False  # Track if tool was used
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
                            # logger.info(f"text_content: {text_content}")
                            
                            # If tool was used, start fresh result
                            if tool_used:
                                result = text_content
                                tool_used = False
                            else:
                                result += text_content
                                
                            # logger.info(f"result: {result}")                
                            chat.update_streaming_result(containers, result, "markdown")

                        elif content_item.get('type') == 'tool_use':
                            # logger.info(f"content_item: {content_item}")      
                            if 'id' in content_item and 'name' in content_item:
                                toolUseId = content_item.get('id', '')
                                tool_name = content_item.get('name', '')
                                logger.info(f"tool_name: {tool_name}, toolUseId: {toolUseId}")
                                chat.streaming_index = chat.index
                                chat.index += 1
                                                                    
                            if 'partial_json' in content_item:
                                partial_json = content_item.get('partial_json', '')
                                #logger.info(f"partial_json: {partial_json}")
                                
                                if toolUseId not in chat.tool_input_list:
                                    chat.tool_input_list[toolUseId] = ""                                
                                chat.tool_input_list[toolUseId] += partial_json
                                input = chat.tool_input_list[toolUseId]
                                # logger.info(f"input: {input}")

                                # logger.info(f"tool_name: {tool_name}, input: {input}, toolUseId: {toolUseId}")
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
    
    return result, image_url
