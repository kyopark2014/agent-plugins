---
name: ppt-translator
description: >-
  Amazon Bedrock 기반 PowerPoint(.pptx) 번역. 서식·레이아웃·차트 메타(제목/축 등)를 보존하며
  텍스트를 한국어(ko) 등 대상 언어로 변환. CLI(`ppt-translate`)·MCP(FastMCP) 지원, SQLite 캐시·
  용어집·원문 언어 자동 감지. PPT/슬라이드 번역, pptx 한국어, Bedrock 프레젠테이션 번역,
  batch translate, dry-run 비용 추정, MCP `translate_powerpoint` 요청 시 사용.
---

# PPT Translator (한국어 변환)

번역기 **소스·실행 기준 경로**는 저장소 내 **`application/skills/ppt-translator/`** 한 곳이다. (`ref/` 의존 없음.)

## 번들 구성 (필수만)

| 항목 | 경로 (저장소 루트 기준) |
|------|-------------------------|
| 패키지 | `application/skills/ppt-translator/ppt_translator/` |
| CLI | `ppt_translator/cli.py` → 설치 후 `ppt-translate` |
| MCP | `application/skills/ppt-translator/mcp_server.py` |
| 프로젝트 | `pyproject.toml`, `requirements.txt` |
| 용어집 예시 | `glossary.yaml` (작업 디렉터리 `./glossary.yaml` 도 자동 탐색) |
| 샘플 | `samples/en.pptx` |
| 옵션·구조 참고 | `docs/cheatsheet.md`, `docs/ppt_handler_structure.md` |
| 패키지 메타 | `README.md` |

이미지·장문 README 등은 번들에 넣지 않았다. 추가 설명은 upstream [ppt-translator](https://github.com/daekeun-ml/ppt-translator) 저장소를 참고한다.

## 데이터 흐름 (수정 시 이 순서 유지)

1. **진입**: `cli.py` (Click) 또는 `mcp_server.py` (FastMCP 도구).
2. **오케스트레이션**: `ppt_handler.PowerPointTranslator` — 슬라이드·도형·노트·차트 대상, 서식 보존 번역.
3. **LLM**: `translation_engine.py` + `bedrock_client.py`, `config.Config` 의 모델·토큰 한도.
4. **원문**: `language_detection.py` — 자동 감지(옵션); 원문==대상이면 API 생략.
5. **차트**: `chart_handler.py` — 메타 텍스트만 번역, 수치 유지.
6. **후처리**: `post_processing.py` — `PowerPointPostProcessor` 등.
7. **캐시·비용**: `cache.py`, `pricing.py`.
8. **용어·프롬프트**: `glossary.py`, `prompts.py`.

별도 스크립트로 “간단 번역” 파이프라인을 만들지 말고 위 모듈을 확장한다.

## 한국어(ko) 기본값

`ppt_translator/config.py` 의 `Config.DEFAULT_TARGET_LANGUAGE` 는 기본 **`ko`**. 언어 미지정 시 대상은 한국어로 둔다. 한국어 폰트는 `FONT_KOREAN` / `FONT_MAP['ko']`.

## CLI (이 디렉터리를 프로젝트 루트로)

```bash
cd application/skills/ppt-translator
uv sync   # 또는: pip install -e .
uv run ppt-translate translate path/to/slides.pptx --target-language ko
```

자주 쓰는 옵션(상세는 `docs/cheatsheet.md`):

- 슬라이드만: `translate-slides ... --slides "1,3" -t ko`
- 폴더 일괄: `batch-translate samples/ -t ko`
- 메타만: `info samples/en.pptx`
- 비용만: `--dry-run`
- 캐시: 기본 `~/.ppt-translator/cache.db` — `--no-cache` / `--cache-backend memory`
- 용어집: `./glossary.yaml` 또는 `-g path.yaml`
- 차트 제외: `--no-charts`

## MCP 서버

```bash
cd application/skills/ppt-translator
uv run python mcp_server.py
```

도구 이름: `translate_powerpoint`, `translate_specific_slides`, `get_slide_info`, `get_slide_preview`, `list_supported_languages`, `list_supported_models`, `get_translation_help`, `batch_translate_powerpoint`, `post_process_powerpoint`. 경로 검증은 MCP 내부 `validate_input_path` 참고.

## 사전 조건

- Python 3.11+
- AWS 자격 증명 + Bedrock 모델 액세스 (`AWS_REGION`, `BEDROCK_MODEL_ID` 등 — `ppt_translator/config.py`)
- 선택: 이 디렉터리 루트에 `.env` ( `config` 가 `parent.parent/.env` 로 로드)

## ppt_handler 심화

클래스·흐름은 `docs/ppt_handler_structure.md` 와 `ppt_translator/ppt_handler.py` 를 함께 본다.
