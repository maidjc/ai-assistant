"""
小政AI助手 带使用记录完整版
✅ 侧边栏使用记录 + 一键清空
✅ 所有功能自动保存生成内容
✅ 深浅色模式自适应
✅ 对话/书摘/起名/朋友圈文案 全部正常
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

def ask_ai_stream(messages, model=MODEL_NAME, temperature=0.85):
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

# 对话人设
SYSTEM_PROMPT = """
你是「小政」，幽默风趣、接地气、会接梗的AI助手。
语气轻松自然，不呆板、不尬聊，回答实用有趣。
不知道就如实说明，不编造内容。当前日期：{date}
"""

def main():
    # 页面配置：开启侧边栏
    st.set_page_config(
        page_title="小政",
        page_icon="🤖",
        layout="centered",
        initial_sidebar_state="expanded"
    )

    # 全局样式 + 深浅色自适应
    st.markdown("""
    <style>
    * {-webkit-font-smoothing: antialiased;}
    #MainMenu, footer, header, .stDeployButton, [data-testid="stToolbar"] {
        display: none !important; height:0; visibility:hidden;
    }
    .func-card {border-radius:12px; padding:16px; margin:8px 0;}

    @media (prefers-color-scheme: light) {
        .stApp {background:#fff; color:#1a1a1a;}
        .func-card {background:#fff; border:1px solid #eee;}
        .stChatInput {background:#fff; border-top:1px solid #eee;}
        .stChatInput>div>div>div {background:#f9f9f9; border:1px solid #eee;}
        .stTextInput input, .stTextArea textarea {background:#fff; border:1px solid #eee; color:#1a1a1a;}
    }
    @media (prefers-color-scheme: dark) {
        .stApp {background:#0e1117; color:#f0f6fc;}
        .func-card {background:#161b22; border:1px solid #30363d;}
        .stChatInput {background:#161b22; border-top:1px solid #30363d;}
        .stChatInput>div>div>div {background:#21262d; border:1px solid #30363d;}
        .stTextInput input, .stTextArea textarea {background:#161b22; border:1px solid #30363d; color:#f0f6fc;}
    }

    .stButton>button {height:48px; border-radius:12px; font-size:16px;}
    .stButton>button[kind="primary"] {background:#2563eb; color:#fff; border:none;}
    .stButton>button[kind="secondary"] {background:transparent; border:1px solid #6e7681;}
    </style>
    """, unsafe_allow_html=True)

    # 初始化会话变量
    if "messages" not in st.session_state:
        today = datetime.now().strftime("%Y年%m月%d日")
        st.session_state.messages = [{"role":"system","content":SYSTEM_PROMPT.format(date=today)}]
    if "current_func" not in st.session_state:
        st.session_state.current_func = "💬 对话"
    # 初始化历史记录容器
    if "history_list" not in st.session_state:
        st.session_state.history_list = []

    # ========== 左侧侧边栏：使用记录 ==========
    with st.sidebar:
        st.header("📋 使用记录")
        st.divider()

        # 清空记录按钮
        if st.button("🗑️ 清空全部记录", use_container_width=True):
            st.session_state.history_list = []
            st.rerun()

        st.divider()
        st.subheader("历史内容")

        # 展示历史记录
        record_list = st.session_state.history_list
        if len(record_list) == 0:
            st.info("暂无任何使用记录")
        else:
            # 倒序展示，最新记录在上
            for idx, item in reversed(list(enumerate(record_list))):
                st.markdown(f"**{item['time']} | {item['module']}**")
                st.text_area("", value=item["content"], height=90, key=f"rec_{idx}", label_visibility="collapsed")
                st.divider()

    # ========== 主页面导航 ==========
    st.markdown("### 🤖 小政 AI 助手")
    nav = ["💬 对话", "📖 书摘", "🏷️ 起名", "📸 朋友圈文案"]
    cols = st.columns(4)
    for i, name in enumerate(nav):
        with cols[i]:
            btn_type = "primary" if st.session_state.current_func == name else "secondary"
            if st.button(name, use_container_width=True, type=btn_type):
                st.session_state.current_func = name
                st.rerun()

    now = datetime.now().strftime("%m-%d %H:%M")
    active_func = st.session_state.current_func

    # 1. 对话模块
    if active_func == "💬 对话":
        empty_chat = all(m["role"] == "system" for m in st.session_state.messages)
        if empty_chat:
            st.info("👋 我是小政，有问必答，还会讲段子～")

        for msg in st.session_state.messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        user_input = st.chat_input("来，随便聊～")
        if user_input:
            st.session_state.messages.append({"role":"user", "content":user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            # 流式回复
            resp_full = ""
            with st.chat_message("assistant"):
                placeholder = st.empty()
                for chunk in ask_ai_stream(st.session_state.messages):
                    resp_full += chunk
                    placeholder.markdown(resp_full + "▌")
                placeholder.markdown(resp_full)

            st.session_state.messages.append({"role":"assistant", "content":resp_full})
            # 保存记录
            save_content = f"用户：{user_input}\n助手：{resp_full}"
            st.session_state.history_list.append({
                "time": now,
                "module": "💬 对话",
                "content": save_content
            })

    # 2. 书摘模块
    elif active_func == "📖 书摘":
        st.markdown('<div class="func-card"><h3>📖 书籍介绍 & 同类推荐</h3></div>', unsafe_allow_html=True)
        mode = st.radio("模式", ["书名", "粘贴原文"], horizontal=True, label_visibility="collapsed")

        if mode == "书名":
            book = st.text_input("书名", placeholder="三体、活着、白夜行")
            author = st.text_input("作者（选填）")
            if st.button("📚 获取介绍 & 推荐", type="primary", use_container_width=True) and book.strip():
                with st.spinner("整理中..."):
                    prompt_book = """
用朋友聊天的语气介绍书籍，自然不生硬。包含基本信息、内容梗概、亮点、适合人群，再推荐几本同类书。
段落分明，不滥用格式，不编造内容。
                    """
                    res = ask_ai([
                        {"role":"system","content":prompt_book},
                        {"role":"user","content":f"介绍《{book}》，作者：{author}"}
                    ], temperature=0.6)
                    st.markdown(f'<div class="func-card">{res}</div>', unsafe_allow_html=True)
                    # 保存记录
                    st.session_state.history_list.append({
                        "time": now,
                        "module": "📖 书摘",
                        "content": f"查询：{book} {author}\n{res}"
                    })
        else:
            txt = st.text_area("原文内容", height=200)
            if st.button("✂️ 提取摘要", type="primary", use_container_width=True) and txt.strip():
                with st.spinner("提取中..."):
                    prompt_txt = "基于原文提取摘要和核心观点，语气自然，排版整洁。"
                    res = ask_ai([{"role":"system","content":prompt_txt},{"role":"user","content":txt}])
                    st.markdown(f'<div class="func-card">{res}</div>', unsafe_allow_html=True)
                    st.session_state.history_list.append({
                        "time": now,
                        "module": "📖 书摘",
                        "content": f"原文摘要\n{res}"
                    })

    # 3. 起名模块
    elif active_func == "🏷️ 起名":
        st.markdown('<div class="func-card"><h3>🏷️ AI起名</h3></div>', unsafe_allow_html=True)
        kind = st.selectbox("类型", ["品牌/店铺", "宠物", "网名", "小说角色"])
        desc = st.text_input("描述（风格、特点）")
        num = st.slider("数量", 3, 10, 5)
        if st.button("✨ 开始起名", type="primary", use_container_width=True) and desc:
            with st.spinner("构思中..."):
                prompt_name = f"生成{num}个{kind}名字，风格：{desc}。附带简短解释，语气自然，格式简洁。"
                res = ask_ai([{"role":"system","content":prompt_name},{"role":"user","content":prompt_name}], temperature=0.9)
                st.markdown(f'<div class="func-card">{res}</div>', unsafe_allow_html=True)
                # 保存记录
                st.session_state.history_list.append({
                    "time": now,
                    "module": "🏷️ 起名",
                    "content": f"类型：{kind} 需求：{desc}\n{res}"
                })

    # 4. 朋友圈文案
    elif active_func == "📸 朋友圈文案":
        st.markdown('<div class="func-card"><h3>📸 朋友圈文案生成</h3></div>', unsafe_allow_html=True)
        style = st.selectbox("文案风格", ["日常随性", "文艺走心", "幽默搞笑", "简约短句", "氛围感"])
        scene = st.text_input("场景描述", placeholder="美食、出游、自拍、风景等")
        if st.button("✨ 生成文案", type="primary", use_container_width=True) and scene:
            with st.spinner("撰写中..."):
                prompt_pyq = f"场景：{scene}，风格：{style}。生成多条自然接地气的朋友圈文案，排版整洁，无生硬AI感。"
                res = ask_ai([{"role":"system","content":prompt_pyq},{"role":"user","content":prompt_pyq}])
                st.markdown(f'<div class="func-card">{res}</div>', unsafe_allow_html=True)
                # 保存记录
                st.session_state.history_list.append({
                    "time": now,
                    "module": "📸 朋友圈文案",
                    "content": f"场景：{scene} 风格：{style}\n{res}"
                })

if __name__ == "__main__":
    main()
