# plugin의 활용

Plugin은 아래와 같이 skill을 이용해 동작하는데 외부의 연결은 MCP를 포함한 connector로 구현하고 sub-agent를 활용할 수 있습니다.

```text
Plugin = Skills(행동 방식) + Connectors(외부 연결) + Slash Commands(명령어) + Sub-agents(하위 에이전트) 
```






설치

```text
claude plugin install enterprise-search@knowledge-work-plugins
```


## MCP 설정

- GitHub 설정

```text
claude mcp add github -e GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_actual_token -- npx @modelcontextprotocol/server-github
```

- Slack Bot 

```text
claude mcp add slack -e SLACK_BOT_TOKEN=xoxb-your-actual-token -- npx @modelcontextprotocol/server-slack
```

- Notion Integration

```text
claude mcp add notion -e NOTION_API_KEY=secret_your_actual_key -- npx @modelcontextprotocol/server-notion
```
