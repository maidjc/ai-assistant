"""
小政AI助手 v4.2 最终稳定版
✅ 书摘不再胡编乱造
✅ 改为：书籍介绍 + 同类小说推荐
✅ 手机适配 + 清爽配色 + 无报错
"""
import streamlit as st
from openai import OpenAI
from datetime import datetime

# ============ 配置区 ============
try:
    API_KEY = st.secrets["API_KEY"]
except:
    API_KEY = "4279ab216a1e4c8282b51f541aff703e.HJdsPUVWqGbMD7t0"

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

    # 清爽白主题 CSS
    st.markdown("""
    <style>
    * {-webkit-font-smoothing: antialiased;}
    #MainMenu, footer, header, .stDeployButton, [data-testid="stToolbar"] {
        display: none !important; height:0; visibility:hidden;
    }
    .stApp {background:#fff;}
    .block-container {padding:8px 12px 80px 12px; max-width:100%;}
    .stChatInput {
        position:fixed; bottom:0; left:0; right:0;
        background:#fff; padding:8px 12px; z-index:999;
        border-top:1px solid #eee;
    }
    .stChatInput>div>div>div {border-radius:24px; height:46px; background:#f9f9f9;}
    .stButton>button {height:48px; border-radius:12px; font-size:16px;}
    .stButton>button[kind="primary"] {background:#2563eb; color:#fff;}
    .func-card {
        background:#fff; border-radius:16px; padding:16px;
        margin:8px 0; border:1px solid #eee;
    }
    </style>
    """, unsafe_allow_html=True)

    # 初始化
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
            if st.button(label, use_container_width=True,
                type="primary" if st.session_state.current_func == label else "secondary"):
                st.session_state.current_func = label
                st.rerun()

    func = st.session_state.current_func

    # ------------------------------
    # 💬 对话
    # ------------------------------
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

    # ------------------------------
    # 📖 书摘（核心修复：绝不胡编）
    # ------------------------------
    elif func == "📖 书摘":
        st.markdown('<div class="func-card"><h3>📖 书籍介绍 & 同类推荐</h3></div>', unsafe_allow_html=True)
        input_mode = st.radio("模式", ["书名", "粘贴原文"], horizontal=True, label_visibility="collapsed")

        if input_mode == "书名":
            book_name = st.text_input("书名", placeholder="如：三体、活着、白夜行")
            author = st.text_input("作者（选填）")

            if st.button("📚 获取介绍 & 推荐", type="primary", use_container_width=True):
                if not book_name.strip():
                    st.warning("请输入书名")
                else:
                    with st.spinner("正在整理..."):
                        # 🔴 关键：强制禁止编造，只做介绍+推荐
                        sys_prompt = """
你是专业书籍推荐官，**绝对禁止编造任何章节、剧情、细节**。
用户输入书名，你只输出两项内容：
1. 本书真实、简洁、客观的介绍（主题、类型、核心亮点）
2. 推荐5本**同类型、同风格**的高质量小说，每本一句话理由

输出格式严格如下：
### 📖 书籍介绍
（这里写介绍）

### 🔍 同类小说推荐
1. 《书名》：一句话推荐理由
2. 《书名》：一句话推荐理由
3. 《书名》：一句话推荐理由
4. 《书名》：一句话推荐理由
5. 《书名》：一句话推荐理由

规则：
- 不知道就说“暂无详细介绍”，不许编
- 不写具体章节、不编剧情
- 语言简洁、真实、可靠
"""
                        result = ask_ai([
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": f"书名：{book_name} 作者：{author}"}
                        ], temperature=0.2)
                        st.markdown(f'<div class="func-card">{result}</div>', unsafe_allow_html=True)

        else:
            st.markdown('<div style="color:#666; margin-bottom:8px;">粘贴原文，提取真实摘要（不编造）</div>', unsafe_allow_html=True)
            content = st.text_area("原文内容", height=200)
            if st.button("✂️ 提取真实摘要", type="primary", use_container_width=True):
                if content.strip():
                    with st.spinner("提取中..."):
                        sys_prompt = """
从用户提供的原文中**只提取真实存在的信息**，不扩展、不编造、不脑补。
输出：
### ✂️ 内容摘要
### 💡 核心观点
"""
                        result = ask_ai([
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": content}
                        ])
                        st.markdown(f'<div class="func-card">{result}</div>', unsafe_allow_html=True)

    # ------------------------------
    # 🏷️ 起名
    # ------------------------------
    elif func == "🏷️ 起名":
        st.markdown('<div class="func-card"><h3>🏷️ AI起名</h3></div>', unsafe_allow_html=True)
        kind = st.selectbox("类型", ["品牌/店铺", "宠物", "网名", "小说角色"])
        desc = st.text_input("描述（风格、人群、特点）")
        num = st.slider("数量", 3, 10, 5)
        if st.button("✨ 开始起名", type="primary", use_container_width=True) and desc:
            with st.spinner("构思中..."):
                res = ask_ai([
                    {"role":"system","content":"起名简洁、好记、有寓意，附一句话解释"},
                    {"role":"user","content":f"给{kind}起{num}个名字，要求：{desc}"}
                ], temperature=0.9)
                st.markdown(f'<div class="func-card">{res}</div>', unsafe_allow_html=True)

    # ------------------------------
    # 📅 日常
    # ------------------------------
    elif func == "📅 日常":
        st.markdown('<div class="func-card"><h3>📅 日常小助手</h3></div>', unsafe_allow_html=True)
        tool = st.selectbox("工具", ["清单", "吃什么", "健身计划", "读书推荐", "电影推荐"])
        req = st.text_input("输入需求")
        if st.button("🚀 生成", type="primary", use_container_width=True) and req:
            with st.spinner("生成中..."):
                res = ask_ai([
                    {"role":"system","content":"简洁实用、步骤清晰、不啰嗦"},
                    {"role":"user","content":f"{tool}：{req}"}
                ])
                st.markdown(f'<div class="func-card">{res}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
