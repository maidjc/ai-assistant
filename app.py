"""
小政AI助手 v4.7 深色/浅色模式自适应版
✅ 自动跟随系统深色/浅色模式切换背景
✅ 文字、按钮、卡片都适配对应模式
✅ 所有模块低AI感、内容具体
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

# 🔥 幽默对话人设
SYSTEM_PROMPT = """
你是「小政」，一个幽默风趣、嘴贫、接地气、反应快的AI小助手。
人设：阳光好玩、不呆板、会接梗、不尬聊、说话像朋友一样。

【说话规则】
1. 语气轻松幽默，偶尔皮一下，但不冒犯
2. 简洁、不啰嗦、不生硬
3. 能调侃就调侃，能搞笑就搞笑
4. 不知道就老实说，别瞎编
5. 回答实用，但带点趣味
6. 当前日期：{date}
"""

def main():
    st.set_page_config(
        page_title="小政",
        page_icon="🤖",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    # ======================
    # ✅ 深色/浅色模式自适应 CSS
    # ======================
    st.markdown("""
    <style>
    /* 全局基础样式 */
    * {-webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;}
    #MainMenu, footer, header, .stDeployButton, [data-testid="stToolbar"] {
        display: none !important; height:0; visibility:hidden;
    }

    /* 适配系统深色/浅色模式 */
    @media (prefers-color-scheme: light) {
        .stApp {background-color: #ffffff !important; color: #1a1a1a !important;}
        .block-container {padding:8px 12px 80px 12px; max-width:100%;}
        .func-card {background:#fff; border:1px solid #eee;}
        .stChatInput {background:#fff; border-top:1px solid #eee;}
        .stChatInput>div>div>div {background:#f9f9f9; border:1px solid #eee;}
        .stTextInput input, .stTextArea textarea {background:#fff; border:1px solid #eee; color:#1a1a1a;}
    }

    @media (prefers-color-scheme: dark) {
        .stApp {background-color: #0e1117 !important; color: #f0f6fc !important;}
        .block-container {padding:8px 12px 80px 12px; max-width:100%;}
        .func-card {background:#161b22; border:1px solid #30363d;}
        .stChatInput {background:#161b22; border-top:1px solid #30363d;}
        .stChatInput>div>div>div {background:#21262d; border:1px solid #30363d; color:#f0f6fc;}
        .stTextInput input, .stTextArea textarea {background:#161b22; border:1px solid #30363d; color:#f0f6fc;}
    }

    /* 按钮样式（两种模式都适配） */
    .stButton>button {height:48px; border-radius:12px; font-size:16px;}
    .stButton>button[kind="primary"] {background:#2563eb; color:#fff; border:none;}
    .stButton>button[kind="secondary"] {background:transparent; color:inherit; border:1px solid #6e7681;}
    .stButton>button[kind="secondary"]:hover {border-color:#2563eb; color:#2563eb;}
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
    # 💬 幽默对话模式
    # ------------------------------
    if func == "💬 对话":
        is_empty = all(m["role"] == "system" for m in st.session_state.messages)
        if is_empty:
            st.info("👋 我是小政，有问必答，还会讲段子～")

        for msg in st.session_state.messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        prompt = st.chat_input("来，随便聊～")
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
    # 📖 书摘（排版整齐 + 口语化）
    # ------------------------------
    elif func == "📖 书摘":
        st.markdown('<div class="func-card"><h3>📖 书籍介绍 & 同类推荐</h3></div>', unsafe_allow_html=True)
        input_mode = st.radio("模式", ["书名", "粘贴原文"], horizontal=True, label_visibility="collapsed")

        if input_mode == "书名":
            book_name = st.text_input("书名", placeholder="如：三体、活着、白夜行、百年孤独")
            author = st.text_input("作者（选填）")

            if st.button("📚 获取介绍 & 推荐", type="primary", use_container_width=True):
                if not book_name.strip():
                    st.warning("请输入书名")
                else:
                    with st.spinner("正在整理..."):
                        sys_prompt = """
你是一个爱看书的朋友，用轻松、口语化的方式给用户介绍一本书。
不要用生硬的列表，也不要用太多Markdown符号，像聊天一样自然。

内容必须包含这几块，但用自然的段落写出来：
1.  基本信息：书名、作者、类型、大概的背景
2.  内容梗概：用几句话讲清楚故事大概，不剧透结局
3.  亮点&看点：这本书哪里好看、为什么出名
4.  适合谁读：什么样的人会喜欢

然后再推荐几本风格类似的书，用简单的编号列出来就好。

要求：
- 语气像朋友推荐，别像机器写的报告
- 段落之间换行，不要挤成一团
- 不要说“暂无详细介绍”，知道多少写多少
- 不要用太多**加粗符号，只在关键地方用
"""
                        result = ask_ai([
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": f"帮我介绍一下《{book_name}》，作者{author}"}
                        ], temperature=0.6)
                        st.markdown(f'<div class="func-card">{result}</div>', unsafe_allow_html=True)

        else:
            content = st.text_area("原文内容", height=200)
            if st.button("✂️ 提取摘要", type="primary", use_container_width=True):
                if content.strip():
                    with st.spinner("提取中..."):
                        sys_prompt = """
用轻松口语化的方式，帮用户整理这段文字的摘要和核心观点。
段落之间换行，排版整齐，不要挤成一团。
"""
                        result = ask_ai([
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": content}
                        ])
                        st.markdown(f'<div class="func-card">{result}</div>', unsafe_allow_html=True)

    # ------------------------------
    # 🏷️ 起名（降低AI感，更自然）
    # ------------------------------
    elif func == "🏷️ 起名":
        st.markdown('<div class="func-card"><h3>🏷️ AI起名</h3></div>', unsafe_allow_html=True)
        kind = st.selectbox("类型", ["品牌/店铺", "宠物", "网名", "小说角色"])
        desc = st.text_input("描述（风格、人群、特点）")
        num = st.slider("数量", 3, 10, 5)
        if st.button("✨ 开始起名", type="primary", use_container_width=True) and desc:
            with st.spinner("构思中..."):
                sys_prompt = f"""
你是起名高手，给用户推荐{num}个名字，要求：
- 风格：{kind}
- 特点：{desc}
- 每个名字附一句简短的解释，别太官方，像朋友推荐一样
- 不要用**加粗符号，也不要用太生硬的格式
- 直接按顺序列出来就行，不要多余的格式
"""
                res = ask_ai([
                    {"role":"system","content":sys_prompt},
                    {"role":"user","content":f"给{kind}起{num}个名字，风格：{desc}"}
                ], temperature=0.9)
                st.markdown(f'<div class="func-card">{res}</div>', unsafe_allow_html=True)

    # ------------------------------
    # 📅 日常小助手（更具体、可执行）
    # ------------------------------
    elif func == "📅 日常":
        st.markdown('<div class="func-card"><h3>📅 日常小助手</h3></div>', unsafe_allow_html=True)
        tool = st.selectbox("工具", ["清单", "吃什么", "健身计划", "读书推荐", "电影推荐"])
        req = st.text_input("输入需求")
        if st.button("🚀 生成", type="primary", use_container_width=True) and req:
            with st.spinner("生成中..."):
                sys_prompt = f"""
你是用户的专属生活助手，回答必须**具体、可执行、不笼统**，像朋友给的实用建议，别像机器写的报告。

要求：
1.  步骤清晰，能直接照着做
2.  内容具体，不要说“准备食材”这种空话，要给出例子
3.  语气自然，口语化，不要生硬
4.  结构清楚，用换行分隔，不要挤成一团

用户需求：{tool}：{req}
"""
                res = ask_ai([
                    {"role":"system","content":sys_prompt},
                    {"role":"user","content":f"{tool}：{req}"}
                ])
                st.markdown(f'<div class="func-card">{res}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
