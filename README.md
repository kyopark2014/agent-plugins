# Plugin의 활용

여기에서는 Anthropic의 Plugin을 LangGraph로 구현하는 방법에 대해 설명합니다.

## Anthropic의 Plugin

Plugin은 아래와 같이 skill을 이용해 동작하는데 외부의 연결은 MCP를 포함한 connector로 구현하고 sub-agent를 활용할 수 있습니다.

```text
Plugin = Skills(행동 방식) + Connectors(외부 연결) + Slash Commands(명령어) + Sub-agents(하위 에이전트) 
```

| 구성 요소 | 역할 |
|----------|------|
| Skills | 특정 직무에 맞는 출력 형식과 행동 방식 정의 |
| Connectors | Google Drive, Slack, Salesforce 등 외부 도구 연결 |
| Slash Commands | /sales:call-prep, /generate-report 등 구조화된 워크플로우 실행 |
| Sub-agents | 복잡한 작업을 처리하는 하위 에이전트 |



## knowledge-work-plugins

Anthropic의 [knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)은 특정 직무 전문가로 만들어주는 오픈소스 플러그인입니다.

제공하는 plugin은 아래와 같습니다.


| 플러그인 | 주요 기능 | 연동 도구 |
|----------|----------|-----------|
| 🗓️ productivity | 작업/캘린더/워크플로우 관리 | Slack, Notion, Jira, Asana 등 |
| 💼 sales | 영업 리서치, 콜 준비, 파이프라인 | HubSpot, Clay, ZoomInfo 등 |
| 🎧 customer-support | 티켓 분류, 응답 초안, 지식베이스 | Intercom, HubSpot, Guru 등 |
| 📋 product-management | 스펙 작성, 로드맵, 사용자 리서치 | Figma, Amplitude, Linear 등 |
| 📣 marketing | 콘텐츠 초안, 캠페인, 브랜드 관리 | Canva, Ahrefs, Klaviyo 등 |
| ⚖️ legal | 계약서 검토, NDA, 리스크 평가 | Box, Egnyte, Microsoft 365 |
| 💰 finance | 분개, 재무제표, 결산 관리 | Snowflake, BigQuery, Databricks |
| 📊 data | SQL 작성, 시각화, 통계 분석 | Snowflake, Hex, Amplitude |
| 🔍 enterprise-search | 이메일/채팅/문서 통합 검색 | Slack, Notion, Jira, Asana |
| 🧬 bio-research | 생명과학 R&D 가속화 | PubMed, ClinicalTrials.gov, ChEMBL |
| 🔧 cowork-plugin-management | 새 플러그인 생성 및 커스터마이징 | — |


claude에서 설치는 아래와 같습니다. 

```text
claude plugin install enterprise-search@knowledge-work-plugins
```



하지만 LangChain/LangGraph에서 활용하기 위해서는 해당 git을 다운로드한 후에 application/plugins에 복사합니다.

```python
https://github.com/anthropics/knowledge-work-plugins
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

## 실행결과


왼쪽 메뉴에서 "frontend-design"을 선택한 후에 아래와 같이 "LLM에 맞는 챗봇 UI를 디자인해주세요."라고 입력하면, get_skill_instructions이 frontend-design의 description을 읽어오고, 이를 바탕으로 챗봇 UI를 생성합니다.

<img width="902" height="656" alt="image" src="https://github.com/user-attachments/assets/04a25576-578d-4299-af0e-ec7b80411e1f" />


생성된 Frontend UI는 아래와 같습니다.

<img width="1159" height="893" alt="image" src="https://github.com/user-attachments/assets/62e78ab0-5ce8-41c1-9674-1ef1ce2186d3" />

- Notion Integration

```text
claude mcp add notion -e NOTION_API_KEY=secret_your_actual_key -- npx @modelcontextprotocol/server-notion
```
