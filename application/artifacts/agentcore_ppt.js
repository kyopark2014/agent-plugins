
const pptxgen = require("pptxgenjs");

let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.title = 'Amazon Bedrock AgentCore';

// ─── Color Palette (Ocean Gradient + Dark) ───────────────────────────────────
const C = {
  darkBg:    "0A1628",   // very dark navy (title/conclusion bg)
  deepBlue:  "065A82",   // deep blue
  teal:      "1C7293",   // teal
  midBlue:   "21295C",   // midnight blue
  accent:    "02C39A",   // mint accent
  white:     "FFFFFF",
  offWhite:  "EAF4FB",
  lightGray: "D0E8F2",
  textDark:  "0A1628",
  textMid:   "1C4A6E",
  muted:     "6B8FA8",
};

const makeShadow = () => ({ type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.18 });

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 1 — Title Slide
// ═══════════════════════════════════════════════════════════════════════════════
{
  let s = pres.addSlide();
  s.background = { color: C.darkBg };

  // Decorative top bar
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.accent }, line: { color: C.accent } });

  // Left accent block
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0.08, w: 0.35, h: 5.545, fill: { color: C.deepBlue }, line: { color: C.deepBlue } });

  // Decorative circles (background)
  s.addShape(pres.shapes.OVAL, { x: 6.5, y: -0.8, w: 4.5, h: 4.5, fill: { color: C.deepBlue, transparency: 70 }, line: { color: C.deepBlue, transparency: 70 } });
  s.addShape(pres.shapes.OVAL, { x: 7.5, y: 2.5, w: 3.0, h: 3.0, fill: { color: C.teal, transparency: 75 }, line: { color: C.teal, transparency: 75 } });

  // AWS Badge
  s.addShape(pres.shapes.RECTANGLE, { x: 0.65, y: 0.45, w: 1.6, h: 0.38, fill: { color: C.accent }, line: { color: C.accent }, rectRadius: 0.05 });
  s.addText("Amazon Web Services", { x: 0.65, y: 0.45, w: 1.6, h: 0.38, fontSize: 8, color: C.darkBg, bold: true, align: "center", valign: "middle", margin: 0 });

  // Main Title
  s.addText("Amazon Bedrock", { x: 0.65, y: 1.1, w: 8.5, h: 0.75, fontSize: 38, color: C.white, bold: false, fontFace: "Calibri", margin: 0 });
  s.addText("AgentCore", { x: 0.65, y: 1.8, w: 8.5, h: 0.9, fontSize: 56, color: C.accent, bold: true, fontFace: "Calibri", margin: 0 });

  // Divider line
  s.addShape(pres.shapes.RECTANGLE, { x: 0.65, y: 2.85, w: 5.5, h: 0.04, fill: { color: C.teal }, line: { color: C.teal } });

  // Subtitle
  s.addText("AI 에이전트를 빠르게 구축·배포·운영하는\n완전 관리형 에이전트 플랫폼", {
    x: 0.65, y: 3.05, w: 8.0, h: 1.0,
    fontSize: 17, color: C.lightGray, fontFace: "Calibri", margin: 0
  });

  // Bottom bar
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.325, w: 10, h: 0.3, fill: { color: C.midBlue }, line: { color: C.midBlue } });
  s.addText("Build · Deploy · Operate  |  Any Framework · Any Model · Any Protocol", {
    x: 0.5, y: 5.325, w: 9, h: 0.3, fontSize: 9, color: C.lightGray, align: "center", valign: "middle", margin: 0
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 2 — What is AgentCore?
// ═══════════════════════════════════════════════════════════════════════════════
{
  let s = pres.addSlide();
  s.background = { color: C.offWhite };

  // Top accent bar
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.07, fill: { color: C.deepBlue }, line: { color: C.deepBlue } });

  // Title area
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0.07, w: 10, h: 0.85, fill: { color: C.deepBlue }, line: { color: C.deepBlue } });
  s.addText("Amazon Bedrock AgentCore란?", { x: 0.5, y: 0.07, w: 9, h: 0.85, fontSize: 24, color: C.white, bold: true, valign: "middle", margin: 0 });

  // Main definition card
  s.addShape(pres.shapes.RECTANGLE, { x: 0.4, y: 1.1, w: 9.2, h: 1.3, fill: { color: C.deepBlue }, line: { color: C.deepBlue }, shadow: makeShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.4, y: 1.1, w: 0.12, h: 1.3, fill: { color: C.accent }, line: { color: C.accent } });
  s.addText("어떤 프레임워크, 모델, 프로토콜을 사용하든 AI 에이전트를 안전하게 대규모로\n구축·배포·운영할 수 있는 완전 관리형 에이전트 플랫폼입니다.", {
    x: 0.7, y: 1.1, w: 8.7, h: 1.3, fontSize: 15, color: C.white, valign: "middle", margin: 0
  });

  // 4 key pillars
  const pillars = [
    { icon: "🚀", title: "빠른 구축", desc: "인프라 관리 없이\n에이전트 개발 가속화" },
    { icon: "🔧", title: "도구 연동", desc: "다양한 도구·데이터와\n원활한 연동" },
    { icon: "🔒", title: "안전한 실행", desc: "저지연·확장 가능한\n보안 실행 환경" },
    { icon: "📊", title: "운영 모니터링", desc: "프로덕션 환경에서\n실시간 모니터링" },
  ];

  pillars.forEach((p, i) => {
    const x = 0.4 + i * 2.35;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 2.65, w: 2.15, h: 2.5, fill: { color: C.white }, line: { color: C.lightGray }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 2.65, w: 2.15, h: 0.07, fill: { color: C.accent }, line: { color: C.accent } });
    s.addText(p.icon, { x, y: 2.8, w: 2.15, h: 0.7, fontSize: 28, align: "center", margin: 0 });
    s.addText(p.title, { x, y: 3.5, w: 2.15, h: 0.4, fontSize: 13, color: C.textDark, bold: true, align: "center", margin: 0 });
    s.addText(p.desc, { x, y: 3.9, w: 2.15, h: 0.9, fontSize: 10.5, color: C.textMid, align: "center", margin: 0 });
  });

  // Bottom bar
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.325, w: 10, h: 0.3, fill: { color: C.deepBlue }, line: { color: C.deepBlue } });
  s.addText("Amazon Bedrock AgentCore", { x: 0.3, y: 5.325, w: 9.4, h: 0.3, fontSize: 9, color: C.lightGray, align: "right", valign: "middle", margin: 0 });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 3 — Core Components (6 services)
// ═══════════════════════════════════════════════════════════════════════════════
{
  let s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.07, fill: { color: C.teal }, line: { color: C.teal } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0.07, w: 10, h: 0.85, fill: { color: C.deepBlue }, line: { color: C.deepBlue } });
  s.addText("핵심 구성 요소 (6대 서비스)", { x: 0.5, y: 0.07, w: 9, h: 0.85, fontSize: 24, color: C.white, bold: true, valign: "middle", margin: 0 });

  const services = [
    { emoji: "⚡", name: "Runtime", color: "065A82", desc: "서버리스 에이전트 호스팅\n격리된 microVM 환경\n최대 8시간 실행 지원" },
    { emoji: "🧠", name: "Memory", color: "1C7293", desc: "단기·장기 메모리 관리\n대화 맥락 유지\n개인화 경험 제공" },
    { emoji: "🔗", name: "Gateway", color: "21295C", desc: "API·Lambda를 MCP 도구로\n단일 보안 엔드포인트\n도구 검색 및 연동" },
    { emoji: "🪪", name: "Identity", color: "065A82", desc: "에이전트 고유 ID 부여\n기업 IdP 연동 지원\n세밀한 접근 제어" },
    { emoji: "🛠️", name: "Built-in Tools", color: "1C7293", desc: "코드 인터프리터 내장\n브라우저 도구 제공\n샌드박스 실행 환경" },
    { emoji: "📡", name: "Observability", color: "21295C", desc: "실시간 추적·디버깅\nCloudWatch 연동\n에이전트 성능 모니터링" },
  ];

  services.forEach((svc, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.35 + col * 3.15;
    const y = 1.15 + row * 2.1;

    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 2.95, h: 1.85, fill: { color: C.white }, line: { color: C.lightGray }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 2.95, h: 0.5, fill: { color: svc.color }, line: { color: svc.color } });
    s.addText(svc.emoji + "  " + svc.name, { x, y, w: 2.95, h: 0.5, fontSize: 13, color: C.white, bold: true, align: "center", valign: "middle", margin: 0 });
    s.addText(svc.desc, { x, y: y + 0.55, w: 2.95, h: 1.2, fontSize: 10, color: C.textMid, align: "center", valign: "top", margin: 0 });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.325, w: 10, h: 0.3, fill: { color: C.deepBlue }, line: { color: C.deepBlue } });
  s.addText("Amazon Bedrock AgentCore", { x: 0.3, y: 5.325, w: 9.4, h: 0.3, fontSize: 9, color: C.lightGray, align: "right", valign: "middle", margin: 0 });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 4 — AgentCore Runtime 상세
// ═══════════════════════════════════════════════════════════════════════════════
{
  let s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.07, fill: { color: C.accent }, line: { color: C.accent } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0.07, w: 10, h: 0.85, fill: { color: C.deepBlue }, line: { color: C.deepBlue } });
  s.addText("⚡ AgentCore Runtime — 서버리스 에이전트 호스팅", { x: 0.5, y: 0.07, w: 9, h: 0.85, fontSize: 21, color: C.white, bold: true, valign: "middle", margin: 0 });

  // Left column — features list
  const features = [
    ["🔒 세션 격리", "각 사용자 세션이 독립된 microVM에서 실행\n세션 간 데이터 오염 방지"],
    ["⏱️ 확장 실행", "최대 8시간 장시간 워크로드 지원\n복잡한 멀티 에이전트 협업 가능"],
    ["💰 소비 기반 과금", "실제 사용 리소스만 과금\nI/O 대기 시간 제외 CPU 과금"],
    ["🌐 프로토콜 지원", "MCP, A2A, AGUI, HTTP, WebSocket\n양방향 스트리밍 지원"],
    ["📦 대용량 페이로드", "100MB 페이로드 처리\n텍스트·이미지·오디오·비디오 지원"],
  ];

  features.forEach(([title, desc], i) => {
    const y = 1.1 + i * 0.85;
    s.addShape(pres.shapes.RECTANGLE, { x: 0.35, y, w: 5.5, h: 0.75, fill: { color: C.white }, line: { color: C.lightGray }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x: 0.35, y, w: 0.08, h: 0.75, fill: { color: C.accent }, line: { color: C.accent } });
    s.addText(title, { x: 0.55, y, w: 5.2, h: 0.3, fontSize: 12, color: C.textDark, bold: true, valign: "bottom", margin: 0 });
    s.addText(desc, { x: 0.55, y: y + 0.3, w: 5.2, h: 0.42, fontSize: 9.5, color: C.textMid, valign: "top", margin: 0 });
  });

  // Right column — framework support
  s.addShape(pres.shapes.RECTANGLE, { x: 6.1, y: 1.1, w: 3.55, h: 4.1, fill: { color: C.deepBlue }, line: { color: C.deepBlue }, shadow: makeShadow() });
  s.addText("지원 프레임워크", { x: 6.1, y: 1.1, w: 3.55, h: 0.45, fontSize: 13, color: C.accent, bold: true, align: "center", valign: "middle", margin: 0 });
  s.addShape(pres.shapes.RECTANGLE, { x: 6.1, y: 1.55, w: 3.55, h: 0.04, fill: { color: C.teal }, line: { color: C.teal } });

  const frameworks = ["Strands Agents", "LangGraph", "CrewAI", "Google ADK", "OpenAI Agents SDK", "Microsoft AutoGen"];
  frameworks.forEach((fw, i) => {
    const y = 1.7 + i * 0.55;
    s.addShape(pres.shapes.RECTANGLE, { x: 6.3, y, w: 3.15, h: 0.42, fill: { color: C.teal, transparency: 30 }, line: { color: C.teal, transparency: 50 } });
    s.addText("✓  " + fw, { x: 6.3, y, w: 3.15, h: 0.42, fontSize: 11, color: C.white, valign: "middle", margin: 0 });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.325, w: 10, h: 0.3, fill: { color: C.deepBlue }, line: { color: C.deepBlue } });
  s.addText("Amazon Bedrock AgentCore", { x: 0.3, y: 5.325, w: 9.4, h: 0.3, fontSize: 9, color: C.lightGray, align: "right", valign: "middle", margin: 0 });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 5 — Memory & Gateway
// ═══════════════════════════════════════════════════════════════════════════════
{
  let s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.07, fill: { color: C.accent }, line: { color: C.accent } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0.07, w: 10, h: 0.85, fill: { color: C.deepBlue }, line: { color: C.deepBlue } });
  s.addText("🧠 Memory  &  🔗 Gateway", { x: 0.5, y: 0.07, w: 9, h: 0.85, fontSize: 24, color: C.white, bold: true, valign: "middle", margin: 0 });

  // Memory section
  s.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 1.1, w: 4.45, h: 4.1, fill: { color: C.white }, line: { color: C.lightGray }, shadow: makeShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 1.1, w: 4.45, h: 0.5, fill: { color: C.deepBlue }, line: { color: C.deepBlue } });
  s.addText("🧠  AgentCore Memory", { x: 0.35, y: 1.1, w: 4.45, h: 0.5, fontSize: 14, color: C.white, bold: true, align: "center", valign: "middle", margin: 0 });

  const memItems = [
    ["단기 메모리 (Short-term)", "세션 내 대화 맥락 유지\n사용자가 정보를 반복하지 않아도 됨"],
    ["장기 메모리 (Long-term)", "세션 간 사용자 선호도·사실 저장\n개인화된 경험 자동 제공"],
    ["주요 활용 사례", "고객 지원 챗봇 / 멀티스텝 워크플로우\n멀티 에이전트 시스템 / 자율 에이전트"],
  ];
  memItems.forEach(([title, desc], i) => {
    const y = 1.75 + i * 1.1;
    s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y, w: 0.06, h: 0.85, fill: { color: C.accent }, line: { color: C.accent } });
    s.addText(title, { x: 0.7, y, w: 3.9, h: 0.35, fontSize: 11.5, color: C.textDark, bold: true, margin: 0 });
    s.addText(desc, { x: 0.7, y: y + 0.35, w: 3.9, h: 0.5, fontSize: 10, color: C.textMid, margin: 0 });
  });

  // Gateway section
  s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.1, w: 4.45, h: 4.1, fill: { color: C.white }, line: { color: C.lightGray }, shadow: makeShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.1, w: 4.45, h: 0.5, fill: { color: C.teal }, line: { color: C.teal } });
  s.addText("🔗  AgentCore Gateway", { x: 5.2, y: 1.1, w: 4.45, h: 0.5, fontSize: 14, color: C.white, bold: true, align: "center", valign: "middle", margin: 0 });

  const gwItems = [
    ["MCP 도구 변환", "API·Lambda·기존 서비스를\nMCP 호환 도구로 자동 변환"],
    ["단일 보안 엔드포인트", "에이전트가 도구를 검색·사용하는\n통합 보안 게이트웨이"],
    ["Policy 거버넌스", "Cedar 언어 또는 자연어로 정책 작성\nCloudWatch 감사 로그 연동"],
  ];
  gwItems.forEach(([title, desc], i) => {
    const y = 1.75 + i * 1.1;
    s.addShape(pres.shapes.RECTANGLE, { x: 5.35, y, w: 0.06, h: 0.85, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText(title, { x: 5.55, y, w: 3.9, h: 0.35, fontSize: 11.5, color: C.textDark, bold: true, margin: 0 });
    s.addText(desc, { x: 5.55, y: y + 0.35, w: 3.9, h: 0.5, fontSize: 10, color: C.textMid, margin: 0 });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.325, w: 10, h: 0.3, fill: { color: C.deepBlue }, line: { color: C.deepBlue } });
  s.addText("Amazon Bedrock AgentCore", { x: 0.3, y: 5.325, w: 9.4, h: 0.3, fontSize: 9, color: C.lightGray, align: "right", valign: "middle", margin: 0 });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 6 — Identity, Policy & Observability
// ═══════════════════════════════════════════════════════════════════════════════
{
  let s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.07, fill: { color: C.accent }, line: { color: C.accent } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0.07, w: 10, h: 0.85, fill: { color: C.deepBlue }, line: { color: C.deepBlue } });
  s.addText("🪪 Identity · Policy · 📡 Observability", { x: 0.5, y: 0.07, w: 9, h: 0.85, fontSize: 22, color: C.white, bold: true, valign: "middle", margin: 0 });

  const sections = [
    {
      title: "🪪 AgentCore Identity",
      color: C.deepBlue,
      items: [
        "에이전트에 고유하고 검증 가능한 ID 부여",
        "Okta, Microsoft Entra ID, Amazon Cognito 연동",
        "세밀한 접근 제어 (Fine-grained Access Control)",
        "OAuth 또는 API 키로 서드파티 서비스 인증",
        "Slack, Zoom, GitHub 등 외부 서비스 연동",
      ]
    },
    {
      title: "🛡️ AgentCore Policy",
      color: C.teal,
      items: [
        "에이전트-도구 상호작용 보안 정책 정의·집행",
        "Cedar 언어 또는 자연어로 정책 작성",
        "에이전트 코드 외부에서 결정론적 집행",
        "사용자 ID 및 도구 입력 기반 세밀한 제어",
        "CloudWatch 감사 로그로 컴플라이언스 지원",
      ]
    },
    {
      title: "📡 AgentCore Observability",
      color: C.midBlue,
      items: [
        "에이전트 추론 단계·도구 호출 추적",
        "CloudWatch Application Insights 연동",
        "OpenTelemetry 표준 텔레메트리 데이터",
        "실시간 대시보드로 성능 지표 모니터링",
        "Runtime·Memory·Gateway·Tools 통합 추적",
      ]
    },
  ];

  sections.forEach((sec, i) => {
    const x = 0.35 + i * 3.15;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.1, w: 2.95, h: 4.1, fill: { color: C.white }, line: { color: C.lightGray }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.1, w: 2.95, h: 0.5, fill: { color: sec.color }, line: { color: sec.color } });
    s.addText(sec.title, { x, y: 1.1, w: 2.95, h: 0.5, fontSize: 11.5, color: C.white, bold: true, align: "center", valign: "middle", margin: 0 });

    sec.items.forEach((item, j) => {
      const y = 1.75 + j * 0.65;
      s.addShape(pres.shapes.OVAL, { x: x + 0.18, y: y + 0.1, w: 0.18, h: 0.18, fill: { color: sec.color }, line: { color: sec.color } });
      s.addText(item, { x: x + 0.45, y, w: 2.35, h: 0.6, fontSize: 9.5, color: C.textMid, valign: "middle", margin: 0 });
    });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.325, w: 10, h: 0.3, fill: { color: C.deepBlue }, line: { color: C.deepBlue } });
  s.addText("Amazon Bedrock AgentCore", { x: 0.3, y: 5.325, w: 9.4, h: 0.3, fontSize: 9, color: C.lightGray, align: "right", valign: "middle", margin: 0 });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 7 — 주요 특징 & 차별점
// ═══════════════════════════════════════════════════════════════════════════════
{
  let s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.07, fill: { color: C.accent }, line: { color: C.accent } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0.07, w: 10, h: 0.85, fill: { color: C.deepBlue }, line: { color: C.deepBlue } });
  s.addText("주요 특징 & 차별점", { x: 0.5, y: 0.07, w: 9, h: 0.85, fontSize: 24, color: C.white, bold: true, valign: "middle", margin: 0 });

  const features = [
    { icon: "🔓", title: "프레임워크 독립성", desc: "LangGraph, CrewAI, Strands, LlamaIndex 등\n어떤 프레임워크도 지원" },
    { icon: "🤖", title: "모델 유연성", desc: "Amazon Bedrock, Anthropic Claude,\nGoogle Gemini, OpenAI 등 모든 LLM 지원" },
    { icon: "🔌", title: "프로토콜 다양성", desc: "MCP, A2A, AGUI, HTTP, WebSocket\n표준 프로토콜 완전 지원" },
    { icon: "☁️", title: "완전 관리형", desc: "인프라 관리 불필요\nAWS가 모든 인프라 운영·유지보수" },
    { icon: "🧩", title: "모듈형 설계", desc: "서비스를 독립적으로 또는 함께 사용\n필요한 기능만 선택적 도입" },
    { icon: "🏢", title: "엔터프라이즈 보안", desc: "데이터 암호화, IAM 연동\n컴플라이언스 및 감사 로그 지원" },
  ];

  features.forEach((f, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.35 + col * 3.15;
    const y = 1.15 + row * 2.05;

    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 2.95, h: 1.85, fill: { color: C.white }, line: { color: C.lightGray }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.08, h: 1.85, fill: { color: C.accent }, line: { color: C.accent } });
    s.addText(f.icon, { x: x + 0.15, y: y + 0.2, w: 0.6, h: 0.5, fontSize: 22, margin: 0 });
    s.addText(f.title, { x: x + 0.15, y: y + 0.7, w: 2.7, h: 0.38, fontSize: 12, color: C.textDark, bold: true, margin: 0 });
    s.addText(f.desc, { x: x + 0.15, y: y + 1.05, w: 2.7, h: 0.7, fontSize: 9.5, color: C.textMid, margin: 0 });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.325, w: 10, h: 0.3, fill: { color: C.deepBlue }, line: { color: C.deepBlue } });
  s.addText("Amazon Bedrock AgentCore", { x: 0.3, y: 5.325, w: 9.4, h: 0.3, fontSize: 9, color: C.lightGray, align: "right", valign: "middle", margin: 0 });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 8 — 활용 사례 & 도입 시나리오
// ═══════════════════════════════════════════════════════════════════════════════
{
  let s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.07, fill: { color: C.accent }, line: { color: C.accent } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0.07, w: 10, h: 0.85, fill: { color: C.deepBlue }, line: { color: C.deepBlue } });
  s.addText("활용 사례 & 도입 시나리오", { x: 0.5, y: 0.07, w: 9, h: 0.85, fontSize: 24, color: C.white, bold: true, valign: "middle", margin: 0 });

  // Use cases
  const useCases = [
    { icon: "🏦", title: "금융 서비스", desc: "초개인화 디지털 뱅킹\n고객 맞춤 금융 상담 에이전트\n(실제 사례: 중남미 최대 은행 도입)" },
    { icon: "🎧", title: "고객 지원", desc: "이전 문의 이력 기억하는 챗봇\n자동 에스컬레이션 및 해결\n24/7 무중단 지원" },
    { icon: "📋", title: "워크플로우 자동화", desc: "인보이스 승인 등 멀티스텝 프로세스\n진행 상태 추적 및 자동화\n복잡한 비즈니스 로직 처리" },
    { icon: "🔬", title: "연구 & 분석", desc: "장시간 데이터 분석 에이전트\n멀티 에이전트 협업 리서치\n코드 실행 및 결과 해석" },
  ];

  useCases.forEach((uc, i) => {
    const x = 0.35 + i * 2.35;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.1, w: 2.15, h: 3.0, fill: { color: C.white }, line: { color: C.lightGray }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.1, w: 2.15, h: 0.07, fill: { color: C.accent }, line: { color: C.accent } });
    s.addText(uc.icon, { x, y: 1.2, w: 2.15, h: 0.65, fontSize: 30, align: "center", margin: 0 });
    s.addText(uc.title, { x, y: 1.85, w: 2.15, h: 0.4, fontSize: 12.5, color: C.textDark, bold: true, align: "center", margin: 0 });
    s.addText(uc.desc, { x, y: 2.3, w: 2.15, h: 1.6, fontSize: 9.5, color: C.textMid, align: "center", margin: 0 });
  });

  // When to use box
  s.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 4.25, w: 9.3, h: 0.95, fill: { color: C.deepBlue }, line: { color: C.deepBlue }, shadow: makeShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 4.25, w: 0.1, h: 0.95, fill: { color: C.accent }, line: { color: C.accent } });
  s.addText("💡 도입 적합 시나리오", { x: 0.6, y: 4.25, w: 2.5, h: 0.45, fontSize: 11, color: C.accent, bold: true, valign: "bottom", margin: 0 });
  s.addText("인프라 관리 없이 빠른 개발 원하는 조직  |  다양한 프레임워크·모델 유연성 필요  |  상태 유지 대화형 에이전트  |  PoC → 프로덕션 빠른 전환", {
    x: 0.6, y: 4.65, w: 8.9, h: 0.45, fontSize: 9.5, color: C.lightGray, valign: "top", margin: 0
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.325, w: 10, h: 0.3, fill: { color: C.deepBlue }, line: { color: C.deepBlue } });
  s.addText("Amazon Bedrock AgentCore", { x: 0.3, y: 5.325, w: 9.4, h: 0.3, fontSize: 9, color: C.lightGray, align: "right", valign: "middle", margin: 0 });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 9 — 구현 접근 방식 (4단계)
// ═══════════════════════════════════════════════════════════════════════════════
{
  let s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.07, fill: { color: C.accent }, line: { color: C.accent } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0.07, w: 10, h: 0.85, fill: { color: C.deepBlue }, line: { color: C.deepBlue } });
  s.addText("구현 접근 방식 — PoC에서 프로덕션까지", { x: 0.5, y: 0.07, w: 9, h: 0.85, fontSize: 22, color: C.white, bold: true, valign: "middle", margin: 0 });

  const steps = [
    { num: "01", title: "안전한 배포", color: C.deepBlue, desc: "서버리스 인프라에 에이전트 배포\n세션 격리 + IAM 기반 보안\nStarter Toolkit으로 빠른 시작" },
    { num: "02", title: "기능 강화", color: C.teal, desc: "Memory로 대화 맥락 유지\nGateway로 도구 통합 간소화\n브라우저·코드 인터프리터 활용" },
    { num: "03", title: "모니터링", color: C.midBlue, desc: "Observability 대시보드 구성\nCloudWatch + OpenTelemetry\n핵심 지표 실시간 추적" },
    { num: "04", title: "확장 & 혁신", color: C.deepBlue, desc: "완전 관리형 모듈형 서비스\n어떤 프레임워크·모델과도 호환\n빠른 프로토타입 → 프로덕션 전환" },
  ];

  steps.forEach((step, i) => {
    const x = 0.35 + i * 2.35;
    // Arrow connector (except last)
    if (i < 3) {
      s.addShape(pres.shapes.RECTANGLE, { x: x + 2.15, y: 2.6, w: 0.2, h: 0.06, fill: { color: C.accent }, line: { color: C.accent } });
    }

    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.1, w: 2.15, h: 3.8, fill: { color: C.white }, line: { color: C.lightGray }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.1, w: 2.15, h: 0.85, fill: { color: step.color }, line: { color: step.color } });

    // Step number circle
    s.addShape(pres.shapes.OVAL, { x: x + 0.73, y: 1.2, w: 0.65, h: 0.65, fill: { color: C.accent }, line: { color: C.accent } });
    s.addText(step.num, { x: x + 0.73, y: 1.2, w: 0.65, h: 0.65, fontSize: 14, color: C.darkBg, bold: true, align: "center", valign: "middle", margin: 0 });

    s.addText(step.title, { x, y: 2.05, w: 2.15, h: 0.4, fontSize: 13, color: C.white, bold: true, align: "center", valign: "middle", margin: 0 });
    s.addText(step.desc, { x: x + 0.15, y: 2.6, w: 1.85, h: 2.1, fontSize: 10, color: C.textMid, margin: 0 });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.325, w: 10, h: 0.3, fill: { color: C.deepBlue }, line: { color: C.deepBlue } });
  s.addText("Amazon Bedrock AgentCore", { x: 0.3, y: 5.325, w: 9.4, h: 0.3, fontSize: 9, color: C.lightGray, align: "right", valign: "middle", margin: 0 });
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 10 — Summary / Conclusion
// ═══════════════════════════════════════════════════════════════════════════════
{
  let s = pres.addSlide();
  s.background = { color: C.darkBg };

  // Decorative elements
  s.addShape(pres.shapes.OVAL, { x: -1, y: -1, w: 5, h: 5, fill: { color: C.deepBlue, transparency: 70 }, line: { color: C.deepBlue, transparency: 70 } });
  s.addShape(pres.shapes.OVAL, { x: 7, y: 3, w: 4, h: 4, fill: { color: C.teal, transparency: 75 }, line: { color: C.teal, transparency: 75 } });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.07, fill: { color: C.accent }, line: { color: C.accent } });

  s.addText("Summary", { x: 0.6, y: 0.3, w: 8.8, h: 0.5, fontSize: 14, color: C.accent, bold: true, charSpacing: 4, margin: 0 });
  s.addText("Amazon Bedrock AgentCore", { x: 0.6, y: 0.75, w: 8.8, h: 0.75, fontSize: 36, color: C.white, bold: true, margin: 0 });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 1.55, w: 4.5, h: 0.04, fill: { color: C.teal }, line: { color: C.teal } });

  const summaryPoints = [
    ["🏗️", "완전 관리형 플랫폼", "인프라 없이 AI 에이전트 구축·배포·운영"],
    ["🔓", "완전한 유연성", "어떤 프레임워크, 모델, 프로토콜도 지원"],
    ["🔒", "엔터프라이즈 보안", "microVM 격리, Identity, Policy 거버넌스"],
    ["🧠", "지능형 메모리", "단기·장기 메모리로 개인화 경험 제공"],
    ["📡", "완전한 가시성", "에이전트 추론부터 도구 호출까지 추적"],
  ];

  summaryPoints.forEach((pt, i) => {
    const y = 1.75 + i * 0.68;
    s.addText(pt[0], { x: 0.6, y, w: 0.5, h: 0.55, fontSize: 18, valign: "middle", margin: 0 });
    s.addText(pt[1], { x: 1.2, y, w: 2.5, h: 0.55, fontSize: 12, color: C.accent, bold: true, valign: "middle", margin: 0 });
    s.addText(pt[2], { x: 3.8, y, w: 5.8, h: 0.55, fontSize: 11, color: C.lightGray, valign: "middle", margin: 0 });
  });

  // CTA box
  s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 5.0, w: 8.8, h: 0.2, fill: { color: C.teal }, line: { color: C.teal } });
  s.addText("docs.aws.amazon.com/bedrock-agentcore", { x: 0.6, y: 5.0, w: 8.8, h: 0.2, fontSize: 9, color: C.darkBg, align: "center", valign: "middle", margin: 0 });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.325, w: 10, h: 0.3, fill: { color: C.midBlue }, line: { color: C.midBlue } });
  s.addText("Build · Deploy · Operate  |  Any Framework · Any Model · Any Protocol", {
    x: 0.5, y: 5.325, w: 9, h: 0.3, fontSize: 9, color: C.lightGray, align: "center", valign: "middle", margin: 0
  });
}

// ─── Save ─────────────────────────────────────────────────────────────────────
pres.writeFile({ fileName: "/Users/ksdyb/Documents/src/agent-plugins/application/artifacts/Amazon_Bedrock_AgentCore.pptx" })
  .then(() => console.log("✅ PPT saved successfully!"))
  .catch(err => console.error("❌ Error:", err));
