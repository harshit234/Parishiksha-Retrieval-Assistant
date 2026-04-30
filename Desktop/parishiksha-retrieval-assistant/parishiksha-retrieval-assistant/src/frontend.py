import streamlit as st
import sys
import os

sys.path.append(os.path.abspath('.'))

from src.retrieval import retriever
from src.generation import generate_answer
from src.guardrails import safe_generate
from src.teacher_mode import generate_with_citations

st.set_page_config(
    page_title="PariShiksha • NCERT Assistant",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded"
)

CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500&display=swap');

  :root {
    --bg:          #0A0E1A;
    --card:        #111827;
    --card2:       #141D2E;
    --border:      rgba(99,179,237,0.11);
    --glow:        rgba(99,179,237,0.30);
    --accent:      #3B82F6;
    --accent2:     #06B6D4;
    --asoft:       rgba(59,130,246,0.13);
    --hi:          #F1F5F9;
    --mid:         #94A3B8;
    --lo:          #64748B;
    --ok:          #10B981;
    --ai-bg:       #0D1C2E;
    --r:           12px;
  }

  /* ── RESET ── */
  html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"],section.main,.main .block-container {
    background: var(--bg) !important;
  }
  *  { font-family:'DM Sans',sans-serif !important; box-sizing:border-box; }
  p,span,div,label,li { color:var(--hi) !important; }

  /* kill all streamlit chrome */
  #MainMenu,footer,header,
  [data-testid="stToolbar"],
  [data-testid="stDecoration"],
  [data-testid="stStatusWidget"] { display:none !important; }

  /* kill default streamlit chat widget entirely */
  [data-testid="stChatMessage"],
  [data-testid="stChatInput"],
  [data-testid="stBottom"] { display:none !important; }

  ::-webkit-scrollbar{width:4px}
  ::-webkit-scrollbar-track{background:transparent}
  ::-webkit-scrollbar-thumb{background:var(--glow);border-radius:8px}

  .block-container { padding:2rem 2.5rem 130px !important; max-width:980px !important; margin:0 auto !important; }

  /* ── SIDEBAR ── */
  [data-testid="stSidebar"] { background:var(--card) !important; border-right:1px solid var(--border) !important; box-shadow:6px 0 40px rgba(0,0,0,.55) !important; }
  [data-testid="stSidebar"]>div { padding-top:1.4rem !important; }
  [data-testid="stSidebar"] .stRadio [data-testid="stWidgetLabel"] { display:none !important; }
  [data-testid="stSidebar"] .stRadio div[role="radiogroup"] { display:flex !important; flex-direction:column !important; gap:6px !important; }
  [data-testid="stSidebar"] .stRadio input[type="radio"] { appearance:none !important;-webkit-appearance:none !important;width:0 !important;height:0 !important;opacity:0 !important;position:absolute !important;pointer-events:none !important; }
  [data-testid="stSidebar"] .stRadio [data-baseweb="radio"]>div:first-child { display:none !important; }
  [data-testid="stSidebar"] .stRadio label { background:var(--card2) !important;border:1px solid var(--border) !important;border-radius:var(--r) !important;padding:10px 14px 10px 38px !important;cursor:pointer !important;transition:all .2s !important;position:relative !important;display:flex !important;align-items:center !important;margin:0 !important;width:100% !important; }
  [data-testid="stSidebar"] .stRadio label::before { content:'' !important;position:absolute !important;left:12px !important;top:50% !important;transform:translateY(-50%) !important;width:13px !important;height:13px !important;border-radius:50% !important;border:2px solid var(--lo) !important;background:transparent !important;transition:all .2s !important; }
  [data-testid="stSidebar"] .stRadio label:hover { border-color:var(--accent) !important;background:var(--asoft) !important; }
  [data-testid="stSidebar"] .stRadio label:hover::before { border-color:var(--accent) !important; }
  [data-testid="stSidebar"] .stRadio label p { font-size:.88rem !important;font-weight:500 !important;color:var(--mid) !important;margin:0 !important; }
  [data-testid="stSidebar"] .stRadio [data-baseweb="radio"]:has([aria-checked="true"]) label { border-color:var(--accent) !important;background:rgba(59,130,246,.10) !important; }
  [data-testid="stSidebar"] .stRadio [data-baseweb="radio"]:has([aria-checked="true"]) label::before { background:var(--accent) !important;border-color:var(--accent) !important;box-shadow:0 0 8px rgba(59,130,246,.55) !important; }
  [data-testid="stSidebar"] .stRadio [data-baseweb="radio"]:has([aria-checked="true"]) label p { color:var(--accent) !important;font-weight:600 !important; }

  hr { border-color:var(--border) !important; }

  /* ── HERO ── */
  .hero { display:flex;align-items:center;gap:20px;padding:1.8rem 2rem;background:linear-gradient(135deg,#0E1D35,#0A1322 55%,#0C1829);border:1px solid var(--border);border-radius:var(--r);margin-bottom:22px;position:relative;overflow:hidden;box-shadow:0 4px 32px rgba(0,0,0,.5),0 0 40px rgba(59,130,246,.08); }
  .hero::before{content:'';position:absolute;top:-50px;right:-50px;width:250px;height:250px;background:radial-gradient(circle,rgba(59,130,246,.16) 0%,transparent 70%);pointer-events:none}
  .hero::after {content:'';position:absolute;bottom:-40px;left:38%;width:180px;height:180px;background:radial-gradient(circle,rgba(6,182,212,.09) 0%,transparent 70%);pointer-events:none}
  .hero-ico { font-size:3rem;line-height:1;flex-shrink:0 }
  .hero-title { font-family:'Syne',sans-serif !important;font-size:2.1rem !important;font-weight:800 !important;letter-spacing:-.03em !important;margin:0 !important;line-height:1.1 !important;color:var(--hi) !important }
  .hero-title b { color:var(--accent) !important }
  .hero-sub { font-size:.86rem;color:var(--lo) !important;margin-top:5px }
  .hero-badge { display:inline-flex;align-items:center;gap:7px;background:rgba(16,185,129,.10);border:1px solid rgba(16,185,129,.28);color:var(--ok) !important;font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:4px 11px;border-radius:50px;margin-top:10px }
  .hero-badge::before { content:'';width:6px;height:6px;background:var(--ok);border-radius:50%;animation:blink 2s infinite }
  @keyframes blink{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.4;transform:scale(.75)}}

  /* ── STATS ── */
  .stats { display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:22px }
  .sc { background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:15px 18px;transition:border-color .2s,box-shadow .2s }
  .sc:hover { border-color:var(--glow);box-shadow:0 0 18px rgba(59,130,246,.09) }
  .sl { font-size:.66rem;text-transform:uppercase;letter-spacing:.12em;color:var(--lo) !important;font-weight:600;margin-bottom:7px }
  .sv { font-family:'Syne',sans-serif;font-size:1.6rem;font-weight:700;line-height:1;color:var(--accent) !important }
  .sv.plain { color:var(--hi) !important;font-size:1rem;line-height:1.3 }
  .sn { font-size:.7rem;color:var(--lo) !important;margin-top:5px }

  /* ── CHAT BUBBLES (pure HTML — zero Streamlit involvement) ── */
  .chat-wrap { display:flex;flex-direction:column;gap:16px;margin-top:8px }

  .bubble-row { display:flex;align-items:flex-start;gap:12px }
  .bubble-row.user { flex-direction:row-reverse }

  .avatar {
    width:36px;height:36px;border-radius:50%;
    display:flex;align-items:center;justify-content:center;
    font-size:18px;line-height:1;flex-shrink:0;
  }
  .avatar.user { background:linear-gradient(135deg,#2563EB,#0891B2) }
  .avatar.ai   { background:linear-gradient(135deg,#1E3A5F,#0C1F33);border:1px solid var(--glow) }

  .bubble { max-width:78%;border-radius:var(--r);padding:12px 16px;font-size:.94rem;line-height:1.75 }
  .bubble.user { background:#1E3A5F;color:var(--hi) !important;border-bottom-right-radius:3px }
  .bubble.ai   {
    background:var(--ai-bg);border:1px solid var(--border);
    border-left:3px solid var(--accent);border-bottom-left-radius:3px;
    color:var(--mid) !important;position:relative;
  }
  .bubble.ai::before {
    content:'✦ AI RESPONSE';position:absolute;top:-9px;left:14px;
    background:var(--bg);padding:0 7px;
    font-size:.58rem;font-weight:700;letter-spacing:.14em;color:var(--accent) !important;
  }
  .bubble.ai *  { color:var(--mid) !important }
  .bubble.ai ul,.bubble.ai ol { padding-left:1.3rem !important }
  .bubble.ai li { margin-bottom:3px !important }

  .src-wrap { margin-top:10px;margin-left:48px }
  .src-toggle { display:flex;align-items:center;gap:6px;cursor:pointer;font-size:.78rem;color:var(--lo) !important;background:var(--card2);border:1px solid var(--border);border-radius:8px;padding:7px 13px;width:fit-content;transition:all .2s;user-select:none }
  .src-toggle:hover { border-color:var(--accent);color:var(--accent) !important }
  .src-list { margin-top:6px;display:none }
  .src-list.open { display:block }
  .src-tag { display:inline-flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--border);border-radius:6px;padding:5px 12px;font-size:.78rem;color:var(--mid) !important;margin:3px 3px 3px 0 }
  .src-tag b { color:var(--accent2) !important }

  /* ── EMPTY STATE ── */
  .empty { text-align:center;padding:3rem 1rem }
  .empty-ico { font-size:2.8rem;margin-bottom:14px }
  .empty-title { font-family:'Syne',sans-serif;font-size:1.15rem;font-weight:700;color:var(--mid) !important;margin-bottom:7px }
  .empty-sub { font-size:.84rem;color:var(--lo) !important;line-height:1.65;max-width:360px;margin:0 auto }
  .chips { display:flex;flex-wrap:wrap;justify-content:center;gap:8px;margin-top:20px }
  .chip { background:var(--card);border:1px solid var(--border);border-radius:50px;padding:7px 15px;font-size:.79rem;color:var(--mid) !important;cursor:pointer;transition:all .2s }
  .chip:hover { border-color:var(--accent);color:var(--accent) !important;background:var(--asoft) }

  /* ── FIXED BOTTOM INPUT BAR ── */
  .bar-wrap {
    position:fixed;bottom:0;left:280px;right:0;
    background:var(--bg);border-top:1px solid var(--border);
    padding:14px 40px 18px;z-index:999;
  }
  .bar-inner { max-width:900px;margin:0 auto;display:flex;gap:10px;align-items:center }
  .bar-inner [data-testid="stTextInput"] { flex:1 !important;margin:0 !important }
  .bar-inner [data-testid="stTextInput"]>div { margin:0 !important }
  .bar-inner [data-testid="stTextInput"] input {
    background:var(--card) !important;border:1px solid var(--border) !important;
    border-radius:var(--r) !important;color:var(--hi) !important;
    font-size:.95rem !important;padding:13px 20px !important;height:50px !important;
    caret-color:var(--accent) !important;transition:border-color .2s,box-shadow .2s !important;
  }
  .bar-inner [data-testid="stTextInput"] input::placeholder { color:var(--lo) !important }
  .bar-inner [data-testid="stTextInput"] input:focus { border-color:var(--accent) !important;box-shadow:0 0 0 3px rgba(59,130,246,.18) !important;outline:none !important }
  .bar-inner [data-testid="stTextInput"] label { display:none !important }
  .bar-inner [data-testid="stButton"] button {
    background:var(--accent) !important;border:none !important;border-radius:var(--r) !important;
    color:white !important;font-size:.9rem !important;font-weight:600 !important;
    padding:0 24px !important;height:50px !important;cursor:pointer !important;
    transition:background .2s,transform .1s !important;white-space:nowrap !important;
  }
  .bar-inner [data-testid="stButton"] button:hover { background:#2563EB !important;transform:translateY(-1px) !important }
  .bar-inner [data-testid="stButton"] button p { color:white !important;margin:0 !important }

  /* ── SIDEBAR COMPONENTS ── */
  .sb-logo { display:flex;align-items:center;gap:11px;padding-bottom:1.4rem;border-bottom:1px solid var(--border);margin-bottom:1.4rem }
  .sb-name { font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;color:var(--hi) !important }
  .sb-name b { color:var(--accent) !important }
  .sb-sub  { font-size:.63rem;color:var(--lo) !important;margin-top:1px;letter-spacing:.05em }
  .sb-lbl  { font-size:.63rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;color:var(--lo) !important;margin:18px 0 8px }
  .sb-info { background:var(--card2);border:1px solid var(--border);border-radius:var(--r);padding:11px 13px;font-size:.78rem;color:var(--lo) !important;line-height:1.65;margin-top:6px }
  .sb-info b { color:var(--mid) !important }
  .sb-foot { padding:1.5rem 0 .5rem;font-size:.65rem;color:var(--lo) !important;text-align:center;letter-spacing:.04em;border-top:1px solid var(--border);margin-top:24px }
</style>

<script>
function toggleSrc(id){
  var el=document.getElementById(id);
  if(el){ el.classList.toggle('open'); }
}
</script>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ── SESSION STATE ──────────────────────────────────────────────────────────────
if "messages"         not in st.session_state: st.session_state.messages = []
if "pending_question" not in st.session_state: st.session_state.pending_question = None

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-logo">
      <span style="font-size:1.9rem;line-height:1">📘</span>
      <div>
        <div class="sb-name">Pari<b>Shiksha</b></div>
        <div class="sb-sub">NCERT AI Assistant</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-lbl">⚙ Response Mode</div>', unsafe_allow_html=True)
    mode = st.radio("", ["Standard", "Teacher Mode", "Safe Mode"])

    INFO = {
        "Standard":     ("⚡", "Fast, direct answers from NCERT content."),
        "Teacher Mode": ("🎓", "Detailed answers with source citations."),
        "Safe Mode":    ("🛡", "Strict guardrails — within curriculum only."),
    }
    ico, desc = INFO[mode]
    st.markdown(f'<div class="sb-info">{ico}&nbsp;<b>{mode}</b><span style="display:block;margin-top:3px">{desc}</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-lbl">📖 Syllabus</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-info"><b>Class 9 Science</b><br>Ch 8 — Motion<br>Ch 9 — Force &amp; Laws of Motion</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-foot">Week 9 Project · PariShiksha v1.0</div>', unsafe_allow_html=True)

# ── PROCESS PENDING (before render, clears immediately) ───────────────────────
if st.session_state.pending_question:
    q = st.session_state.pending_question
    st.session_state.pending_question = None          # clear FIRST

    if mode == "Standard":
        result = generate_answer(q, retriever)
    elif mode == "Teacher Mode":
        result = generate_with_citations(q, retriever, generate_answer)
    else:
        result = safe_generate(q, retriever, generate_answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "chunks": result.get("retrieved_chunks", [])
    })

# ── HERO + STATS ──────────────────────────────────────────────────────────────
total_q = len([m for m in st.session_state.messages if m["role"] == "user"])

st.markdown(f"""
<div class="hero">
  <div class="hero-ico">📘</div>
  <div>
    <h1 class="hero-title">Pari<b>Shiksha</b></h1>
    <div class="hero-sub">NCERT Class 9 Science Study Assistant &nbsp;·&nbsp; Chapters 8 &amp; 9</div>
    <div class="hero-badge">AI Powered &nbsp;·&nbsp; Offline-Ready</div>
  </div>
</div>
<div class="stats">
  <div class="sc"><div class="sl">Questions Asked</div><div class="sv">{total_q}</div><div class="sn">This session</div></div>
  <div class="sc"><div class="sl">Active Mode</div><div class="sv plain">{mode}</div><div class="sn">Change in sidebar</div></div>
  <div class="sc"><div class="sl">Knowledge Base</div><div class="sv">2</div><div class="sn">Chapters indexed</div></div>
</div>
""", unsafe_allow_html=True)

# ── CHAT HISTORY (pure HTML bubbles — no st.chat_message) ────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="empty">
      <div class="empty-ico">🔭</div>
      <div class="empty-title">Ask anything from Motion or Forces</div>
      <div class="empty-sub">Your AI study partner has read every line of NCERT Ch 8 &amp; 9.<br>Type a question below to get started.</div>
      <div class="chips">
        <div class="chip">What is Newton's 2nd law?</div>
        <div class="chip">Speed vs velocity</div>
        <div class="chip">What is inertia?</div>
        <div class="chip">Derive equations of motion</div>
      </div>
    </div>""", unsafe_allow_html=True)
else:
    html_parts = ['<div class="chat-wrap">']
    for idx, msg in enumerate(st.session_state.messages):
        role = msg["role"]
        content = msg["content"]

        if role == "user":
            html_parts.append(f"""
            <div class="bubble-row user">
              <div class="avatar user">👤</div>
              <div class="bubble user">{content}</div>
            </div>""")
        else:
            src_id = f"src-{idx}"
            chunks = msg.get("chunks", [])
            src_html = ""
            if chunks:
                tags = "".join(
                    f'<div class="src-tag"><b>#{i+1}</b>&nbsp; {c["metadata"].get("chapter","?")} &nbsp;·&nbsp; {c["metadata"].get("type","—")}</div>'
                    for i, c in enumerate(chunks)
                )
                src_html = f"""
                <div class="src-wrap">
                  <div class="src-toggle" onclick="toggleSrc('{src_id}')">
                    📚 Sources ({len(chunks)} chunks) &nbsp;▾
                  </div>
                  <div class="src-list" id="{src_id}">{tags}</div>
                </div>"""

            html_parts.append(f"""
            <div class="bubble-row">
              <div class="avatar ai">🤖</div>
              <div style="flex:1;min-width:0">
                <div class="bubble ai">{content}</div>
                {src_html}
              </div>
            </div>""")

    html_parts.append('</div>')
    st.markdown("".join(html_parts), unsafe_allow_html=True)

# ── FIXED INPUT BAR ───────────────────────────────────────────────────────────
st.markdown('<div class="bar-wrap"><div class="bar-inner">', unsafe_allow_html=True)
col_in, col_btn = st.columns([10, 1])
with col_in:
    typed = st.text_input("q", label_visibility="collapsed",
                          placeholder="Ask anything from Motion or Force & Laws of Motion…",
                          key="chat_input_field")
with col_btn:
    send = st.button("Send ➤", use_container_width=True)
st.markdown('</div></div>', unsafe_allow_html=True)

# ── SUBMIT — one rerun, no loop ───────────────────────────────────────────────
if send and typed.strip():
    st.session_state.messages.append({"role": "user", "content": typed.strip()})
    st.session_state.pending_question = typed.strip()
    st.rerun()
