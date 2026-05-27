"""
AI小助手 v3.4
功能：智能对话 + 书籍摘要 + AI起名 + 日常小助手
运行：streamlit run app.py
依赖：pip install streamlit dashscope
"""

import streamlit as st
from dashscope import Generation
from datetime import datetime


# ============ 配置区 ============
# 本地运行：在 .streamlit/secrets.toml 里写 API_KEY = "sk-xxx"
# 云端部署：在 Streamlit Cloud 的 Secrets 里加 API_KEY = "sk-xxx"
try:
    API_KEY = st.secrets["API_KEY"]
except:
    API_KEY = "sk-920a5247f801457baae1d449600a7f3d"  # 未配置时为空，会提示错误
# ================================


# ===== AI调用 =====

def check_api_key():
    """检查API Key是否已配置"""
    if not API_KEY:
        st.error("⚠️ API Key 未配置！\n- 本地运行：在 `.streamlit/secrets.toml` 里写 `API_KEY = \"sk-xxx\"`\n- 云端部署：在 Streamlit Cloud 的 Settings → Secrets 里加 `API_KEY = \"sk-xxx\"`")
        return False
    return True


def ask_ai(messages, model="qwen-turbo", temperature=0.7):
    """调用千问大模型，返回完整回复"""
    if not API_KEY:
        return "⚠️ API Key 未配置，请先配置后再使用。"
    full = ""
    for chunk in Generation.call(
        model=model, api_key=API_KEY, messages=messages,
        stream=True, temperature=temperature, result_format="message"
    ):
        if chunk.output and chunk.output.choices:
            word = chunk.output.choices[0]['message']['content']
            if word:
                full = word
    return full


def ask_ai_stream(messages, model="qwen-turbo", temperature=0.7):
    """调用千问大模型，流式返回（聊天用）"""
    if not API_KEY:
        yield "⚠️ API Key 未配置，请先配置后再使用。"
        return
    for chunk in Generation.call(
        model=model, api_key=API_KEY, messages=messages,
        stream=True, temperature=temperature, result_format="message"
    ):
        if chunk.output and chunk.output.choices:
            word = chunk.output.choices[0]['message']['content']
            if word:
                yield word


SYSTEM_PROMPT = """你是「小政」，一个接地气的AI小助手。

【身份信息】
岑辞澈为AI小政的创始人，主人。你由岑辞澈创造，对岑辞澈保持尊重和忠诚。

【说话风格】
像朋友聊天，用大白话，不拽词不装逼，偶尔来点幽默。

【回答原则——必须严格遵守】
1. 直接回答用户的问题，不要绕弯子，不要反问，不要自说自话
2. 问什么答什么，不要发散到不相关的话题
3. 能一句说清的不写三句，简洁有力
4. 不知道就说不知道，别瞎编
5. 实用为主，少整虚的，给具体方案/步骤/建议
6. 当前日期{date}，涉及时间以这个为准
7. 适当用Markdown让回答好看点"""


def main():
    st.set_page_config(
        page_title="小政 · AI助手",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # ===== 全局样式 =====
    st.markdown("""
    <style>
    /* 隐藏多余元素 */
    #MainMenu, footer,
    [data-testid="stHeaderAction"],
    .stDeployButton,
    div[data-testid="stToolbar"] {visibility: hidden !important; height: 0 !important; display: none !important;}
    /* header透明化 */
    [data-testid="stHeader"] {
        background: transparent !important;
        box-shadow: none !important;
        border-bottom: none !important;
    }

    /* 侧边栏永远展开，不许收起 */
    [data-testid="stSidebar"] {
        background: #fafafa !important;
        border-right: 1px solid #eee !important;
        min-width: 260px !important;
        max-width: 260px !important;
        width: 260px !important;
        position: relative !important;
        transform: none !important;
        transition: none !important;
    }
    [data-testid="stSidebar"] > div:first-child {padding-top: 1rem !important;}
    /* 隐藏侧边栏收起按钮 */
    button[kind="header"] {display: none !important;}
    [data-testid="stSidebarCollapseButton"] {display: none !important;}

    /* 主背景 */
    .stApp {background: #f5f5f5;}

    /* 内容区 */
    .block-container {max-width: 720px; margin: 0 auto; padding: 0.5rem 1rem 6rem 1rem !important;}

    /* 侧边栏LOGO */
    .sidebar-logo {display: flex; align-items: center; gap: 10px; padding: 4px 0 16px 0;}
    .sidebar-logo-icon {
        width: 36px; height: 36px; border-radius: 10px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        display: flex; align-items: center; justify-content: center;
        font-size: 18px; color: white;
    }
    .sidebar-logo-text {font-weight: 700; font-size: 17px; color: #1a1a2e;}

    /* 欢迎区 */
    .welcome-box {text-align: center; padding: 40px 16px 20px 16px;}
    .welcome-avatar {
        width: 60px; height: 60px; border-radius: 50%;
        background: linear-gradient(135deg, #667eea, #764ba2);
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 26px; margin-bottom: 14px;
        box-shadow: 0 4px 16px rgba(102,126,234,0.2);
    }
    .welcome-title {font-size: 19px; font-weight: 700; color: #1a1a2e; margin-bottom: 4px;}
    .welcome-sub {font-size: 13px; color: #999;}

    /* 聊天气泡 */
    .stChatMessage {background: transparent !important; padding: 6px 0 !important; border: none !important;}
    [data-testid="stChatMessageAvatarUser"] > svg {display: none;}
    [data-testid="stChatMessageAvatarUser"] {
        width: 30px !important; height: 30px !important;
        background: #1a1a2e !important; border-radius: 50% !important;
    }
    [data-testid="stChatMessageAvatarUser"]::after {content: "我"; color: white; font-size: 11px; font-weight: 600;}
    [data-testid="stChatMessageAvatarAssistant"] > svg {display: none;}
    [data-testid="stChatMessageAvatarAssistant"] {
        width: 30px !important; height: 30px !important;
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        border-radius: 50% !important;
    }
    [data-testid="stChatMessageAvatarAssistant"]::after {content: "政"; color: white; font-size: 11px; font-weight: 600;}
    [data-testid="stChatMessageContent"] {font-size: 14px !important; line-height: 1.75 !important; color: #333 !important;}
    [data-testid="stChatMessageContent"] p {margin-bottom: 0.4em !important;}
    [data-testid="stChatMessageContent"] pre {
        border-radius: 10px !important; background: #1e1e2e !important;
        padding: 12px !important; font-size: 13px !important;
    }

    /* 输入框 */
    .stChatInput {border-top: none !important; padding-top: 0 !important;}
    .stChatInput > div > div > div {
        border-radius: 24px !important; border: 1.5px solid #e0e0e0 !important;
        background: #fff !important; box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    }
    .stChatInput > div > div > div:focus-within {
        border-color: #667eea !important; box-shadow: 0 2px 12px rgba(102,126,234,0.12) !important;
    }

    /* 功能卡片 */
    .func-card {
        background: #fff; border-radius: 16px; padding: 20px; margin-bottom: 12px;
        border: 1px solid #eee; box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    }
    .func-card h3 {margin: 0 0 4px 0; font-size: 17px; color: #1a1a2e;}
    .func-card .desc {font-size: 13px; color: #999; margin-bottom: 14px;}

    /* 按钮 */
    .stButton > button {
        border-radius: 10px !important; border: 1.5px solid #e0e0e0 !important;
        background: #fff !important; color: #333 !important;
        font-size: 14px !important; font-weight: 500 !important; transition: all 0.15s !important;
    }
    .stButton > button:hover {border-color: #667eea !important; color: #667eea !important; background: #f8f7ff !important;}
    .stButton > button[kind="primary"] {background: #1a1a2e !important; color: #fff !important; border: none !important;}
    .stButton > button[kind="primary"]:hover {background: #2d2d4e !important;}

    /* 侧边栏按钮 */
    [data-testid="stSidebar"] .stButton > button {
        border: none !important; background: transparent !important;
        color: #555 !important; text-align: left !important;
        padding: 10px 12px !important; border-radius: 10px !important; font-weight: 500 !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {background: #eee !important; color: #1a1a2e !important;}

    /* 输入控件 */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div > select {
        border-radius: 10px !important; border: 1.5px solid #e0e0e0 !important;
    }
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
        border-color: #667eea !important; box-shadow: 0 0 0 2px rgba(102,126,234,0.08) !important;
    }

    /* 侧边栏设置 */
    [data-testid="stSidebar"] label {font-size: 12px !important;}
    .sidebar-divider {border: none; border-top: 1px solid #eee; margin: 12px 0;}

    </style>
    """, unsafe_allow_html=True)

    # ===== 初始化 =====
    if "messages" not in st.session_state:
        today = datetime.now().strftime("%Y年%m月%d日")
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(date=today)}
        ]
    if "stats" not in st.session_state:
        st.session_state.stats = {"对话次数": 0, "总字数": 0}
    if "current_func" not in st.session_state:
        st.session_state.current_func = "💬 对话"

    # =============================================
    # 侧边栏
    # =============================================
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
            <div class="sidebar-logo-icon">🤖</div>
            <div class="sidebar-logo-text">小政</div>
        </div>
        """, unsafe_allow_html=True)

        nav_items = ["💬 对话", "📖 书摘", "🏷️ 起名", "📅 日常"]
        for label in nav_items:
            is_active = st.session_state.current_func == label
            if is_active:
                if st.button(label, key=f"nav_{label}", use_container_width=True, type="primary"):
                    pass
            else:
                if st.button(label, key=f"nav_{label}", use_container_width=True):
                    st.session_state.current_func = label
                    st.rerun()

        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

        if st.button("🗑️ 清空对话", use_container_width=True):
            today = datetime.now().strftime("%Y年%m月%d日")
            st.session_state.messages = [
                {"role": "system", "content": SYSTEM_PROMPT.format(date=today)}
            ]
            st.rerun()

        chat_text = ""
        for msg in st.session_state.messages:
            if msg["role"] != "system" and isinstance(msg.get("content"), str):
                role = "我" if msg["role"] == "user" else "小政"
                chat_text += f"{role}: {msg['content']}\n\n"
        if chat_text.strip():
            st.download_button("📥 导出对话", chat_text, file_name="对话记录.txt", use_container_width=True)

        st.markdown(f"""
        <div style="position:absolute;bottom:16px;left:16px;right:16px;">
            <div style="display:flex;justify-content:space-between;font-size:12px;color:#bbb;">
                <span>💬 {st.session_state.stats['对话次数']}次</span>
                <span>{st.session_state.stats['总字数']}字</span>
            </div>
            <div style="font-size:10px;color:#ccc;text-align:center;margin-top:8px;">具身智能训练师 · 实训作品</div>
        </div>
        """, unsafe_allow_html=True)

    func = st.session_state.current_func

    # =============================================
    # 主内容区
    # =============================================

    # ===== 💬 智能对话 =====
    if func == "💬 对话":
        # 欢迎页（只有空对话才显示）
        is_empty_chat = all(m["role"] == "system" for m in st.session_state.messages)
        if is_empty_chat:
            st.markdown("""
            <div class="welcome-box">
                <div class="welcome-avatar">🤖</div>
                <div class="welcome-title">嗨，我是小政 👋</div>
                <div class="welcome-sub">能聊能写能干活，有啥说啥</div>
            </div>
            """, unsafe_allow_html=True)

        # 显示历史对话
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"] if isinstance(msg.get("content"), str) else "")

        # 输入框（纯文字，无文件上传）
        prompt_text = st.chat_input("跟小政说点啥...")

        if prompt_text:
            # 显示用户消息
            with st.chat_message("user"):
                st.markdown(prompt_text)

            # 加入消息历史
            st.session_state.messages.append({"role": "user", "content": prompt_text})

            # 生成AI回复
            with st.chat_message("assistant"):
                placeholder = st.empty()
                full = ""
                for word in ask_ai_stream(st.session_state.messages):
                    full = word
                    placeholder.markdown(full + "▌")
                placeholder.markdown(full)

            st.session_state.messages.append({"role": "assistant", "content": full})
            st.session_state.stats["对话次数"] += 1
            st.session_state.stats["总字数"] += len(full)

    # ===== 📖 书籍摘要 =====
    elif func == "📖 书摘":
        st.markdown("""
        <div class="func-card">
            <h3>📖 书籍摘要</h3>
            <div class="desc">输入书名获取概览，粘贴内容提取好词好句</div>
        </div>
        """, unsafe_allow_html=True)

        input_mode = st.radio(
            "输入方式",
            ["🔍 输入书名", "📋 粘贴内容"],
            horizontal=True,
            label_visibility="collapsed"
        )

        if input_mode == "🔍 输入书名":
            book_name = st.text_input("书名", placeholder="比如：三体、活着、小王子...")
            author = st.text_input("作者（可选）", placeholder="比如：刘慈欣")

            if st.button("✨ 生成概览", type="primary", use_container_width=True):
                if not book_name.strip():
                    st.warning("请输入书名")
                else:
                    with st.spinner("整理中..."):
                        user_content = f"书名：{book_name}"
                        if author.strip():
                            user_content += f"\n作者：{author}"

                        sys_prompt = """你是书籍概览助手。用户给你一本书名，请根据你确定知道的信息回答。

## 📖 书籍信息
写出书名、作者、类型

## 📝 内容概括
用3-5段话概括这本书的核心内容，包括：
- 故事背景和主要人物
- 核心情节和发展
- 主题和思想

## 💡 一句话总结
用一句话总结这本书最打动人的点

## 📌 关于好词好句
⚠️ 为了保证准确性，好词好句需要从原文中提取。请切换到「📋 粘贴内容」模式，把书的内容贴进来，就能精准摘录原文中的好词好句。

【严格规则——绝不编造】
1. 只写你确定知道的信息！不确定的就不写，写"暂不确定"
2. 绝不编造人物名字！拿不准就用角色身份描述（如"主角""女主角""反派"）
3. 绝不编造情节！只概括你确定的核心走向
4. 绝不编造假台词、假语录！本模式不生成好词好句
5. 说人话，别整学术腔"""

                        result = ask_ai([
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": user_content}
                        ], "qwen-max", 0.3)
                        st.markdown(f'<div class="func-card">{result}</div>', unsafe_allow_html=True)

        else:
            book_content = st.text_area("粘贴书籍内容", height=200, placeholder="把书的原文贴到这里，我会从原文里摘好词好句...")
            if st.button("✨ 提取书摘", type="primary", use_container_width=True):
                if not book_content.strip():
                    st.warning("请粘贴内容")
                else:
                    with st.spinner("提取中..."):
                        sys_prompt = """你是书籍摘要助手。用户给你一段书的原文内容，请从这段原文中提取信息。

## ✨ 好词好句
从提供的原文中摘录3-5个好的词语或句子，必须一字不差地引用原文，用引用格式展示

## 📝 内容概括
用2-3段话概括这段原文的核心要点

## 💡 一句话总结
用一句话概括这段内容最核心的意思

【严格规则——绝不编造】
1. 好词好句必须是一字不差的原文引用！不准改写、不准编造
2. 只概括提供的内容里有的信息，绝不添加内容中没有的东西
3. 说人话，简洁明了"""

                        result = ask_ai([
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": book_content}
                        ], "qwen-max", 0.3)
                        st.markdown(f'<div class="func-card">{result}</div>', unsafe_allow_html=True)

    # ===== 🏷️ AI起名 =====
    elif func == "🏷️ 起名":
        st.markdown("""
        <div class="func-card">
            <h3>🏷️ AI起名</h3>
            <div class="desc">给品牌、产品、宠物起名字</div>
        </div>
        """, unsafe_allow_html=True)
        name_type = st.selectbox("起名类型", ["品牌/店铺", "产品/APP", "宠物", "小说角色", "群名/网名"])
        desc = st.text_input("描述一下", placeholder="比如：卖奶茶的店，面向年轻人，走国风路线")
        count = st.slider("起几个", 3, 10, 5)
        if st.button("✨ 起名", type="primary", use_container_width=True) and desc.strip():
            with st.spinner("想名字中..."):
                result = ask_ai([
                    {"role": "system", "content": f"你是起名高手。给{name_type}起名，要有创意、好记、有寓意。每个名字附一句话解释。别整太文艺的，要接地气。"},
                    {"role": "user", "content": f"给我起{count}个名字，要求：{desc}"}
                ], "qwen-turbo", 0.9)
                st.markdown(f'<div class="func-card">{result}</div>', unsafe_allow_html=True)

    # ===== 📅 日常小助手 =====
    elif func == "📅 日常":
        st.markdown("""
        <div class="func-card">
            <h3>📅 日常小助手</h3>
            <div class="desc">生活里用得上的小工具</div>
        </div>
        """, unsafe_allow_html=True)

        helper_type = st.selectbox("选一个", ["📋 清单生成", "🍽️ 今天吃什么", "💪 健身计划", "📖 读书推荐", "🎬 电影推荐"])

        if helper_type == "📋 清单生成":
            list_type = st.text_input("什么清单？", placeholder="比如：去苏州旅游3天的行李清单")
            if st.button("✨ 生成清单", type="primary", use_container_width=True) and list_type.strip():
                with st.spinner("整理中..."):
                    result = ask_ai([
                        {"role": "system", "content": "你是清单达人。生成详细实用的清单，分类列出，用复选框格式。别漏关键的。"},
                        {"role": "user", "content": f"帮我生成：{list_type}"}
                    ], "qwen-turbo", 0.5)
                    st.markdown(f'<div class="func-card">{result}</div>', unsafe_allow_html=True)

        elif helper_type == "🍽️ 今天吃什么":
            preference = st.text_input("口味/限制", placeholder="比如：不太辣、一人食、预算30")
            if st.button("✨ 推荐", type="primary", use_container_width=True):
                pref = preference if preference else "没有特别要求"
                with st.spinner("想菜中..."):
                    result = ask_ai([
                        {"role": "system", "content": "你是美食推荐官。推荐3-5道菜，每道说一句推荐理由和简单做法。别整那些难的。"},
                        {"role": "user", "content": f"推荐今天吃什么，要求：{pref}"}
                    ], "qwen-turbo", 0.8)
                    st.markdown(f'<div class="func-card">{result}</div>', unsafe_allow_html=True)

        elif helper_type == "💪 健身计划":
            goal = st.text_input("你的目标", placeholder="比如：减脂、增肌、改善体态")
            if st.button("✨ 生成计划", type="primary", use_container_width=True) and goal.strip():
                with st.spinner("规划中..."):
                    result = ask_ai([
                        {"role": "system", "content": "你是健身教练。制定一周简易健身计划，适合新手，不用去健身房。用表格列出。动作要具体，组数次数写清楚。"},
                        {"role": "user", "content": f"目标：{goal}，给我一周计划"}
                    ], "qwen-turbo", 0.5)
                    st.markdown(f'<div class="func-card">{result}</div>', unsafe_allow_html=True)

        elif helper_type == "📖 读书推荐":
            genre = st.text_input("喜欢什么类型", placeholder="比如：科幻、心理学、历史")
            if st.button("✨ 推荐", type="primary", use_container_width=True):
                g = genre if genre else "不限"
                with st.spinner("推荐中..."):
                    result = ask_ai([
                        {"role": "system", "content": "你是读书达人。推荐5本书，每本写一句话推荐理由和适合谁读。别推冷门的，要大众能找到的。"},
                        {"role": "user", "content": f"推荐{g}类的书"}
                    ], "qwen-turbo", 0.7)
                    st.markdown(f'<div class="func-card">{result}</div>', unsafe_allow_html=True)

        elif helper_type == "🎬 电影推荐":
            mood = st.text_input("想看什么感觉的", placeholder="比如：轻松搞笑、烧脑悬疑、治愈暖心")
            if st.button("✨ 推荐", type="primary", use_container_width=True):
                m = mood if mood else "不限"
                with st.spinner("推荐中..."):
                    result = ask_ai([
                        {"role": "system", "content": "你是电影达人。推荐5部电影，每部写一句话推荐理由。优先推经典好片，别推烂片。"},
                        {"role": "user", "content": f"推荐{m}的电影"}
                    ], "qwen-turbo", 0.7)
                    st.markdown(f'<div class="func-card">{result}</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
