# plugin의 활용


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
