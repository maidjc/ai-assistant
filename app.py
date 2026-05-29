"""
小政AI助手 v4.1 修复版
已解决语法错误 + 清爽白主题 + 手机适配
"""
import streamlit as st
from openai import OpenAI
from datetime import datetime
from openai import APIError, APIConnectionError, RateLimitError

# ============ 配置区 ============
try:
    API_KEY = st.secrets["API_KEY"]
except:
    API_KEY = ""

BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
MODEL_NAME = "glm-4-flash"
# ================================

def get_client():
    if not API_KEY:
        return None
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)

def check_api_key():
    if not API_KEY:
        st.error("⚠️ API Key 未配置！")
        return False
    return True

def ask_ai(messages, model=MODEL_NAME, temperature=0.7):
    if not check_api_key():
        return "⚠️ 请先配置 API Key"
    client = get_client()
    full = ""
    try:
        for chunk in client.chat.completions.create(
            model=model, messages=messages, stream=True, temperature=temperature
        ):
            if chunk.choices and chunk.choices[0].delta.content:
                full += chunk.choices[0].delta.content
    except Exception as e:
        return f"⚠️ 出错：{str(e)}"
    return full

def ask_ai_stream(messages, model=MODEL_NAME, temperature=0.7):
    if not check_api_key():
        yield "⚠️ 请先配置 API Key"
        return
    client = get_client()
    try:
        for chunk in client.chat.completions.create(
            model=model, messages=messages, stream=True, temperature=temperature
        ):
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"⚠️ 出错：{str(e)}"

SYSTEM_PROMPT = """你是「小政」，接地气的AI小助手。
【身份】岑辞澈创造，忠诚可靠。
【风格】大白话、简洁、幽默、不装逼。
【原则】直接回答、问啥答啥、简洁有力、不知道就说不知道、给具体方案、用当前日期{date}。"""

def main():
    st.set_page_config(
        page_title="小政",
        page_icon="🤖",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    # 清爽白主题 + 高对比度 CSS
    st.markdown("""
    <style>
    * {
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    #MainMenu, footer, header, .stDeployButton, [data-testid="stToolbar"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }
    .stApp {
        background: #ffffff !important;
        padding: 0 !important;
        margin: 0 auto !important;
        max-width: 100% !important;
    }
    .block-container {
        max-width: 100% !important;
        width: 100% !important;
        padding: 8px 12px 80px 12px !important;
        margin: 0 auto !important;
    }
    body, .stMarkdown, .stTextInput, .stTextArea, .stButton, .stRadio, .stSelectbox {
        color: #1a1a1a !important;
        font-family: system-ui, -apple-system, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif !important;
    }
    .stChatInput {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #ffffff !important;
        padding: 8px 12px;
        z-index: 999;
        border-top: 1px solid #e5e7eb;
    }
    .stChatInput > div > div > div {
        border-radius: 24px !important;
        height: 46px !important;
        font-size: 16px !important;
        border: 1.5px solid #e5e7eb !important;
        background: #f9fafb !important;
    }
    [data-testid="stChatMessageContent"] {
        font-size: 16px !important;
        line-height: 1.6 !important;
        padding: 8px 12px !important;
        color: #1a1a1a !important;
    }
    .stButton > button {
        height: 48px !important;
        font-size: 16px !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 500 !important;
        transition: all 0.2s ease;
    }
    .stButton > button[kind="primary"] {
        background: #2563eb !important;
        color: #ffffff !important;
    }
    .stButton > button[kind="secondary"] {
        background: #f3f4f6 !important;
        color: #1a1a1a !important;
    }
    .func-card {
        background: #ffffff !important;
        border-radius: 16px;
        padding: 16px;
        margin: 8px 0;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .stTextInput input, .stTextArea textarea {
        font-size: 16px !important;
        height: 48px !important;
        border-radius: 12px !important;
        border: 1.5px solid #e5e7eb !important;
        background: #ffffff !important;
        color: #1a1a1a !important;
    }
    h3, h4, h5, h6, .stTitle, .stHeader {
        color: #1a1a1a !important;
    }
    .stRadio label, .stSelectbox label {
        color: #1a1a1a !important;
        font-size: 16px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # 初始化会话
    if "messages" not in st.session_state:
        today = datetime.now().strftime("%Y年%m月%d日")
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT.format(date=today)}]
    if "stats" not in st.session_state:
        st.session_state.stats = {"对话次数": 0, "总字数": 0}
    if "current_func" not in st.session_state:
        st.session_state.current_func = "💬 对话"

    # 顶部导航
    st.markdown("### 🤖 小政 AI 助手")
    nav_items = ["💬 对话", "📖 书摘", "🏷️ 起名", "📅 日常"]
    cols = st.columns(4)
    for i, label in enumerate(nav_items):
        with cols[i]:
            if st.button(label, use_container_width=True, type="primary" if st.session_state.current_func == label else "secondary"):
                st.session_state.current_func = label
                st.rerun()

    func = st.session_state.current_func

    # 💬 对话
    if func == "💬 对话":
        is_empty = all(m["role"] == "system" for m in st.session_state.messages)
        if is_empty:
            st.info("👋 我是小政，随便问我啥～")

        for msg in st.session_state.messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        prompt = st.chat_input("点这里输入...")
        if prompt:
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                placeholder = st.empty()
                full = ""
                for word in ask_ai_stream(st.session_state.messages):
                    full += word
                    placeholder.markdown(full + "▌")
                placeholder.markdown(full)

            st.session_state.messages.append({"role": "assistant", "content": full})
            st.session_state.stats["对话次数"] += 1
            st.session_state.stats["总字数"] += len(full)

    # 📖 书摘
    elif func == "📖 书摘":
        st.markdown('<div class="func-card"><h3>📖 书籍摘要</h3></div>', unsafe_allow_html=True)
        mode = st.radio("模式", ["书名", "粘贴内容"], horizontal=True)
        if mode == "书名":
            book = st.text_input("书名")
            section = st.text_input("章节（可选）")
            if st.button("生成概览", use_container_width=True):
                if book:
                    res = ask_ai([
                        {"role":"system","content":"概括全书，简洁清晰"},
                        {"role":"user","content":f"《{book}》{section} 概览"}
                    ])
                    st.markdown(f'<div class="func-card">{res}</div>', unsafe_allow_html=True)
        else:
            txt = st.text_area("粘贴内容", height=200)
            if st.button("提取摘要", use_container_width=True):
                res = ask_ai([
                    {"role":"system","content":"提取好词好句+概括"},
                    {"role": "user", "content":txt}
                ])
                st.markdown(f'<div class="func-card">{res}</div>', unsafe_allow_html=True)

    # 🏷️ 起名
    elif func == "🏷️ 起名":
        st.markdown('<div class="func-card"><h3>🏷️ AI起名</h3></div>', unsafe_allow_html=True)
        t = st.selectbox("类型", ["品牌", "宠物", "网名", "角色"])
        desc = st.text_input("描述")
        if st.button("开始起名", use_container_width=True):
            res = ask_ai([
                {"role":"system","content":"起名高手，简洁好记"},
                {"role":"user","content":f"{t}：{desc}，起5个"}
            ])
            st.markdown(f'<div class="func-card">{res}</div>', unsafe_allow_html=True)

    # 📅 日常
    elif func == "📅 日常":
        st.markdown('<div class="func-card"><h3>📅 日常小助手</h3></div>', unsafe_allow_html=True)
        tool = st.selectbox("工具", ["清单", "吃什么", "健身计划", "读书", "电影"])
        txt = st.text_input("输入需求")
        if st.button("生成", use_container_width=True):
            res = ask_ai([
                {"role":"system","content":"实用简洁"},
                {"role":"user","content":f"{tool}：{txt}"}
            ])
            st.markdown(f'<div class="func-card">{res}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
