"""
小政AI助手 —— 侧边栏可展开+记录不丢 最终版
✅ 侧边栏展开按钮可见
✅ 隐藏后再展开，记录不丢
✅ 刷新页面记录不丢（本地JSON）
✅ 可一键强制展开侧边栏
"""
import streamlit as st
from openai import OpenAI
from datetime import datetime
import json
import os

# ---------------- 配置 ----------------
try:
    API_KEY = st.secrets["API_KEY"]
except:
    API_KEY = "4279ab216a1e4c8282b51f541aff703e.HJdsPUVWqGbMD7t0"

BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
MODEL_NAME = "glm-4-flash"
HISTORY_FILE = "history.json"

# ---------------- AI 客户端 ----------------
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

# ---------------- 历史记录持久化 ----------------
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history_list):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history_list, f, ensure_ascii=False, indent=2)

# ---------------- 页面配置：必须最前面，且只调用一次 ----------------
st.set_page_config(
    page_title="小政",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"  # 强制默认展开
)

# ---------------- 极简 CSS：不隐藏侧边栏按钮 ----------------
st.markdown("""
<style>
#MainMenu, footer, header, .stDeployButton, [data-testid="stToolbar"] {
    display: none !important;
}
.func-card {
    border-radius:12px; padding:16px; margin:8px 0;
    background:#fff; border:1px solid #eee;
}
@media (prefers-color-scheme: dark) {
    .func-card {background:#161b22; border:1px solid #30363d;}
    .stApp {background:#0e1117; color:#f0f6fc;}
}
.stButton>button {border-radius:12px; font-size:16px;}
</style>
""", unsafe_allow_html=True)

# ---------------- 初始化会话 ----------------
if "messages" not in st.session_state:
    today = datetime.now().strftime("%Y年%m月%d日")
    st.session_state.messages = [{
        "role": "system",
        "content": f"你是「小政」，幽默风趣、接地气、会接梗的AI助手。当前日期：{today}"
    }]

if "current_func" not in st.session_state:
    st.session_state.current_func = "💬 对话"

if "history_list" not in st.session_state:
    st.session_state.history_list = load_history()

# ---------------- 侧边栏：使用记录 + 一键展开提示 ----------------
with st.sidebar:
    st.header("📋 使用记录")
    st.info("如果看不到内容，点右上角「<」展开侧边栏")
    st.divider()

    if st.button("🗑️ 清空全部记录", use_container_width=True):
        st.session_state.history_list = []
        save_history([])
        st.rerun()

    st.divider()
    st.subheader("历史内容")

    history = st.session_state.history_list
    if not history:
        st.info("暂无任何使用记录")
    else:
        for idx, item in reversed(list(enumerate(history))):
            st.markdown(f"**{item['time']} | {item['module']}**")
            st.text_area("", value=item["content"], height=90, label_visibility="collapsed")
            st.divider()

# ---------------- 主页面导航 ----------------
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

# ---------------- 1. 对话 ----------------
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

        resp_full = ask_ai(st.session_state.messages)
        with st.chat_message("assistant"):
            st.markdown(resp_full)

        st.session_state.messages.append({"role":"assistant", "content":resp_full})

        new_entry = {
            "time": now,
            "module": "💬 对话",
            "content": f"用户：{user_input}\n助手：{resp_full}"
        }
        st.session_state.history_list.append(new_entry)
        save_history(st.session_state.history_list)

# ---------------- 2. 书摘 ----------------
elif active_func == "📖 书摘":
    st.markdown('<div class="func-card"><h3>📖 书籍介绍 & 同类推荐</h3></div>', unsafe_allow_html=True)
    mode = st.radio("模式", ["书名", "粘贴原文"], horizontal=True, label_visibility="collapsed")

    if mode == "书名":
        book = st.text_input("书名", placeholder="三体、活着、白夜行")
        author = st.text_input("作者（选填）")
        if st.button("📚 获取介绍 & 推荐", type="primary", use_container_width=True) and book.strip():
            with st.spinner("整理中..."):
                res = ask_ai([
                    {"role":"system","content":"用朋友聊天的语气介绍书籍，自然不生硬。包含基本信息、梗概、亮点、适合人群，再推荐几本同类书。"},
                    {"role":"user","content":f"介绍《{book}》，作者：{author}"}
                ], temperature=0.6)
                st.markdown(f'<div class="func-card">{res}</div>', unsafe_allow_html=True)

                new_entry = {"time": now, "module": "📖 书摘", "content": f"查询：{book} {author}\n{res}"}
                st.session_state.history_list.append(new_entry)
                save_history(st.session_state.history_list)
    else:
        txt = st.text_area("原文内容", height=200)
        if st.button("✂️ 提取摘要", type="primary", use_container_width=True) and txt.strip():
            with st.spinner("提取中..."):
                res = ask_ai([
                    {"role":"system","content":"基于原文提取摘要和核心观点，语气自然，排版整洁。"},
                    {"role":"user","content":txt}
                ])
                st.markdown(f'<div class="func-card">{res}</div>', unsafe_allow_html=True)

                new_entry = {"time": now, "module": "📖 书摘", "content": f"原文摘要\n{res}"}
                st.session_state.history_list.append(new_entry)
                save_history(st.session_state.history_list)

# ---------------- 3. 起名 ----------------
elif active_func == "🏷️ 起名":
    st.markdown('<div class="func-card"><h3>🏷️ AI起名</h3></div>', unsafe_allow_html=True)
    kind = st.selectbox("类型", ["品牌/店铺", "宠物", "网名", "小说角色"])
    desc = st.text_input("描述（风格、特点）")
    num = st.slider("数量", 3, 10, 5)
    if st.button("✨ 开始起名", type="primary", use_container_width=True) and desc:
        with st.spinner("构思中..."):
            res = ask_ai([
                {"role":"system","content":f"生成{num}个{kind}名字，风格：{desc}。附带简短解释，语气自然，格式简洁。"},
                {"role":"user","content":f"给{kind}起{num}个名字，风格：{desc}"}
            ], temperature=0.9)
            st.markdown(f'<div class="func-card">{res}</div>', unsafe_allow_html=True)

            new_entry = {"time": now, "module": "🏷️ 起名", "content": f"类型：{kind} 需求：{desc}\n{res}"}
            st.session_state.history_list.append(new_entry)
            save_history(st.session_state.history_list)

# ---------------- 4. 朋友圈文案 ----------------
elif active_func == "📸 朋友圈文案":
    st.markdown('<div class="func-card"><h3>📸 朋友圈文案生成</h3></div>', unsafe_allow_html=True)
    style = st.selectbox("文案风格", ["日常随性", "文艺走心", "幽默搞笑", "简约短句", "氛围感"])
    scene = st.text_input("场景描述", placeholder="美食、出游、自拍、风景等")
    if st.button("✨ 生成文案", type="primary", use_container_width=True) and scene:
        with st.spinner("撰写中..."):
            res = ask_ai([
                {"role":"system","content":f"场景：{scene}，风格：{style}。生成多条自然接地气的朋友圈文案，排版整洁，无生硬AI感。"},
                {"role":"user","content":f"场景：{scene}，风格：{style}，生成朋友圈文案"}
            ])
            st.markdown(f'<div class="func-card">{res}</div>', unsafe_allow_html=True)

            new_entry = {"time": now, "module": "📸 朋友圈文案", "content": f"场景：{scene} 风格：{style}\n{res}"}
            st.session_state.history_list.append(new_entry)
            save_history(st.session_state.history_list)

if __name__ == "__main__":
    pass
