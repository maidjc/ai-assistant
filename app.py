"""
小政AI助手 书香完整版｜附带本地数据存储
功能：对话、书摘、起名、朋友圈文案、我的存档(历史数据保存)
存储：SQLite本地文件数据库 user_data.db
"""
import streamlit as st
from openai import OpenAI
from datetime import datetime
import sqlite3

# ========== 数据库初始化与增删改查函数 ==========
def init_db():
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    # 书籍记录表
    cur.execute('''CREATE TABLE IF NOT EXISTS book_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_name TEXT,
        author TEXT,
        content TEXT,
        create_time TEXT
    )''')
    # 起名记录表
    cur.execute('''CREATE TABLE IF NOT EXISTS name_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        desc TEXT,
        result TEXT,
        create_time TEXT
    )''')
    # 朋友圈文案
    cur.execute('''CREATE TABLE IF NOT EXISTS art_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        style TEXT,
        scene TEXT,
        content TEXT,
        create_time TEXT
    )''')
    # 聊天记录
    cur.execute('''CREATE TABLE IF NOT EXISTS chat_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ask TEXT,
        reply TEXT,
        create_time TEXT
    )''')
    conn.commit()
    conn.close()

# 新增数据
def add_sql(table, data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    if table == "book":
        cur.execute("INSERT INTO book_record(book_name,author,content,create_time) VALUES(?,?,?,?)", (*data, now))
    elif table == "name":
        cur.execute("INSERT INTO name_record(type,desc,result,create_time) VALUES(?,?,?,?)", (*data, now))
    elif table == "art":
        cur.execute("INSERT INTO art_record(style,scene,content,create_time) VALUES(?,?,?,?)", (*data, now))
    elif table == "chat":
        cur.execute("INSERT INTO chat_record(ask,reply,create_time) VALUES(?,?,?)", (*data, now))
    conn.commit()
    conn.close()

# 模糊查询
def search_sql(table, key=""):
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    if table == "book":
        cur.execute("select * from book_record where book_name like ?", (f'%{key}%',))
    elif table == "name":
        cur.execute("select * from name_record where desc like ?", (f'%{key}%',))
    elif table == "art":
        cur.execute("select * from art_record where scene like ?", (f'%{key}%',))
    elif table == "chat":
        cur.execute("select * from chat_record where ask like ?", (f'%{key}%',))
    res = cur.fetchall()
    conn.close()
    return res

# 删除单条
def del_sql(table, rid):
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    if table == "book":
        cur.execute("delete from book_record where id=?", (rid,))
    elif table == "name":
        cur.execute("delete from name_record where id=?", (rid,))
    elif table == "art":
        cur.execute("delete from art_record where id=?", (rid,))
    elif table == "chat":
        cur.execute("delete from chat_record where id=?", (rid,))
    conn.commit()
    conn.close()

# 初始化数据库
init_db()

# ========== API配置 ==========
try:
    API_KEY = st.secrets["API_KEY"]
except:
    API_KEY = ""
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
MODEL_NAME = "glm-4-flash"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# 角色提示词
SYSTEM_PROMPT = """
你是「小政」，风趣随和、接地气，日常聊天自然不生硬，无AI机械话术；
书摘通俗口语、起名简约有寓意、朋友圈文案贴合风格。
"""

# ========== 页面配置+书香CSS ==========
st.set_page_config(
    page_title="小政",
    page_icon="📜",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
* {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    font-family: "Microsoft Yahei", "SimSun", serif;
}
#MainMenu, footer, header, .stDeployButton, [data-testid="stToolbar"] {
    display: none !important;
    height: 0;
    visibility: hidden;
}
.stApp {
    background: linear-gradient(135deg, #f8f2e4 0%, #f0e6d2 50%, #e9dcc3 100%) !important;
    background-attachment: fixed;
}
@media (prefers-color-scheme: light) {
    .stApp { color: #4a3f30 !important; }
    .block-container {padding:12px 15px 80px 15px;max-width:100%;}
    .func-card {
        background: rgba(255,253,246,0.92) !important;
        border:1px solid #d4c2a8 !important;
        border-radius:12px !important;
        box-shadow:0 3px 12px rgba(120,95,65,0.18) !important;
    }
    div[data-testid="stChatMessage"] {
        background:rgba(255,253,246,0.9) !important;
        border:1px solid #d4c2a8 !important;
        border-radius:10px !important;
    }
    .stChatInput {background:rgba(255,253,246,0.95) !important;border-top:1px solid #d4c2a8;}
    .stChatInput>div>div>div {background:#faf4e6 !important;border:1px solid #d4c2a8;border-radius:20px;color:#4a3f30;}
    .stTextInput input,.stTextArea textarea,.stSelectbox>div>div {
        background:rgba(255,253,246,0.9) !important;border:1px solid #d4c2a8;border-radius:8px;color:#4a3f30 !important;
    }
}
@media (prefers-color-scheme: dark) {
    .stApp {background:linear-gradient(135deg,#2c261e 0%,#252018 50%,#1e1a14 100%) !important;color:#e8dfcc !important;}
    .block-container {padding:12px 15px 80px 15px;max-width:100%;}
    .func-card {background:rgba(45,39,30,0.92) !important;border:1px solid #6b5c4b !important;border-radius:12px;box-shadow:0 3px 12px rgba(0,0,0,0.35);}
    div[data-testid="stChatMessage"] {background:rgba(45,39,30,0.9) !important;border:1px solid #6b5c4b;border-radius:10px;}
    .stChatInput {background:rgba(45,39,30,0.95) !important;border-top:1px solid #6b5c4b;}
    .stChatInput>div>div>div {background:#332c22 !important;border:1px solid #6b5c4b;border-radius:20px;color:#e8dfcc;}
    .stTextInput input,.stTextArea textarea,.stSelectbox>div>div {
        background:rgba(45,39,30,0.9) !important;border:1px solid #6b5c4b;border-radius:8px;color:#e8dfcc !important;
    }
}
.stButton>button {height:44px !important;border-radius:10px !important;font-size:15px !important;font-weight:500;letter-spacing:1px;transition:all 0.25s ease;}
.stButton>button[kind="primary"] {background:#82674b !important;color:#fff8e8 !important;border:none;box-shadow:0 2px 6px rgba(110,80,50,0.25);}
.stButton>button[kind="primary"]:hover {background:#6d543c !important;transform:translateY(-2px);box-shadow:0 4px 10px rgba(110,80,50,0.35);}
.stButton>button[kind="secondary"] {background:transparent !important;color:inherit;border:1px solid #b8a48c;}
.stButton>button[kind="secondary"]:hover {border-color:#82674b;color:#82674b;transform:translateY(-1px);}
</style>
""", unsafe_allow_html=True)

# ========== 导航栏 ==========
st.markdown("### 📜 小政 AI 助手")
nav_items = ["💬 对话", "📖 书摘", "🏷️ 起名", "📸 朋友圈文案", "📂 我的存档"]
cols = st.columns(len(nav_items))
if "current_func" not in st.session_state:
    st.session_state.current_func = nav_items[0]

for idx, name in enumerate(nav_items):
    with cols[idx]:
        if st.button(name, use_container_width=True, type="primary" if st.session_state.current_func==name else "secondary"):
            st.session_state.current_func = name
            st.rerun()

func = st.session_state.current_func

# ========== 1.对话模块 ==========
if func == "💬 对话":
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    for item in st.session_state.chat_history:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
    prompt = st.chat_input("来，随便聊～")
    if prompt:
        st.session_state.chat_history.append({"role":"user","content":prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        msg = [{"role":"system","content":SYSTEM_PROMPT}] + st.session_state.chat_history
        res = client.chat.completions.create(model=MODEL_NAME,messages=msg)
        ans = res.choices[0].message.content
        st.session_state.chat_history.append({"role":"assistant","content":ans})
        with st.chat_message("assistant"):
            st.markdown(ans)
        # 保存对话入库
        add_sql("chat", [prompt, ans])

# ========== 2.书摘模块 ==========
elif func == "📖 书摘":
    st.markdown('<div class="func-card"><h3>📖 书籍介绍 & 同类推荐</h3></div>', unsafe_allow_html=True)
    book_name = st.text_input("书名")
    author = st.text_input("作者（选填）")
    if st.button("📚 获取介绍", type="primary") and book_name:
        with st.spinner("整理内容中..."):
            ask = f"详细介绍《{book_name}》作者{author}，包含基础信息、梗概、亮点、适合人群，顺带推荐同类好书，语言生活化。"
            ans = client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":ask}]).choices[0].message.content
            st.markdown(ans)
            # 存入数据库
            add_sql("book", [book_name, author, ans])

# ==========3.起名模块 ==========
elif func == "🏷️ 起名":
    st.markdown('<div class="func-card"><h3>🏷️ AI起名</h3></div>', unsafe_allow_html=True)
    typ = st.selectbox("类型",["品牌店铺","宠物名字","网名笔名","小说角色"])
    desc = st.text_input("风格/要求描述")
    num = st.slider("数量",3,10,5)
    if st.button("✨生成名字",type="primary") and desc:
        with st.spinner("构思中..."):
            ask = f"生成{num}个{typ}名字，要求：{desc}，每个附带简短释义，自然无AI感。"
            ans = client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":ask}]).choices[0].message.content
            st.markdown(ans)
            add_sql("name",[typ,desc,ans])

# ==========4.朋友圈文案 ==========
elif func == "📸 朋友圈文案":
    st.markdown('<div class="func-card"><h3>📸 朋友圈文案生成</h3></div>', unsafe_allow_html=True)
    style = st.selectbox("风格",["日常随性","文艺走心","幽默搞笑","简约短句","氛围感"])
    scene = st.text_input("场景描述（美食/出游/看书等）")
    if st.button("✨生成文案",type="primary") and scene:
        with st.spinner("撰写文案..."):
            ask = f"场景：{scene}，风格：{style}，多条长短搭配朋友圈文案，简洁自然。"
            ans = client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":ask}]).choices[0].message.content
            st.markdown(ans)
            add_sql("art",[style,scene,ans])

# ==========5.我的存档｜历史记录查询+删除 ==========
elif func == "📂 我的存档":
    st.markdown('<div class="func-card"><h3>📂 个人内容存档</h3></div>', unsafe_allow_html=True)
    tab1,tab2,tab3,tab4 = st.tabs(["书籍存档","起名存档","文案存档","对话存档"])
    # 书籍
    with tab1:
        kw = st.text_input("书名搜索")
        data = search_sql("book",kw)
        for row in data:
            st.write(f"📅{row[4]}｜{row[1]}【{row[2]}】")
            st.text(row[3])
            if st.button("删除",key=f'b{row[0]}'):
                del_sql("book",row[0])
                st.rerun()
    #起名
    with tab2:
        kw = st.text_input("需求关键词")
        data = search_sql("name",kw)
        for row in data:
            st.write(f"📅{row[4]}｜分类：{row[1]}｜需求：{row[2]}")
            st.text(row[3])
            if st.button("删除",key=f'n{row[0]}'):
                del_sql("name",row[0])
                st.rerun()
    #文案
    with tab3:
        kw = st.text_input("场景搜索")
        data = search_sql("art",kw)
        for row in data:
            st.write(f"📅{row[4]}｜风格：{row[1]}｜场景：{row[2]}")
            st.text(row[3])
            if st.button("删除",key=f'a{row[0]}'):
                del_sql("art",row[0])
                st.rerun()
    #聊天
    with tab4:
        kw = st.text_input("提问检索")
        data = search_sql("chat",kw)
        for row in data:
            st.write(f"📅{row[3]} 用户：{row[1]}")
            st.text(f"小政：{row[2]}")
            if st.button("删除",key=f'c{row[0]}'):
                del_sql("chat",row[0])
                st.rerun()
