"""
小政AI书香助手｜网页卡顿优化完整版
优化点：DB连接缓存｜查询缓存｜form防实时刷新｜存档分页｜聊天只渲染20条
管理员账号：admin  密码：123456
PyCharm/网页部署通用
"""
import streamlit as st
from openai import OpenAI
from datetime import datetime
import sqlite3
import hashlib

#====================优化1：全局数据库连接缓存【头部固定位置】====================
@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect("user_data.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

#====================密码加密====================
def make_hash(pwd):
    return hashlib.sha256(str(pwd).encode()).hexdigest()

def check_hash(pwd, hashed_str):
    return make_hash(pwd) == hashed_str

#====================初始化数据库表====================
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    #用户表
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        create_time TEXT
    )''')
    #书籍记录
    cur.execute('''CREATE TABLE IF NOT EXISTS book_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,book_name TEXT,author TEXT,content TEXT,create_time TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    #起名记录
    cur.execute('''CREATE TABLE IF NOT EXISTS name_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,type TEXT,desc TEXT,result TEXT,create_time TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    #文案记录
    cur.execute('''CREATE TABLE IF NOT EXISTS art_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,style TEXT,scene TEXT,content TEXT,create_time TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    #对话记录
    cur.execute('''CREATE TABLE IF NOT EXISTS chat_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,ask TEXT,reply TEXT,create_time TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    #初始化管理员
    if not cur.execute("SELECT id FROM users WHERE username='admin'").fetchone():
        cur.execute("INSERT INTO users(username,password_hash,role,create_time) VALUES(?,?,?,?)",
                    ("admin", make_hash("123456"), "admin", datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()

#====================优化2：查询缓存@st.cache_data====================
@st.cache_data(ttl=300)
def get_user_info(username):
    conn = get_db_connection()
    return conn.cursor().execute("SELECT id,username,password_hash,role FROM users WHERE username=?", (username,)).fetchone()

def user_register(uname, pwd):
    conn = get_db_connection()
    conn.cursor().execute("INSERT INTO users(username,password_hash,role,create_time) VALUES(?,?,?,?)",
                           (uname, make_hash(pwd), "user", datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    get_user_info.clear()

def reset_password(uname, new_pwd):
    conn = get_db_connection()
    conn.cursor().execute("UPDATE users SET password_hash=? WHERE username=?", (make_hash(new_pwd), uname))
    conn.commit()
    get_user_info.clear()

@st.cache_data(ttl=60)
def get_all_users():
    conn = get_db_connection()
    return conn.cursor().execute("SELECT id,username,role,create_time FROM users").fetchall()

def insert_data(table, data_list, uid):
    conn = get_db_connection()
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    if table == "book":
        cur.execute("INSERT INTO book_record(user_id,book_name,author,content,create_time) VALUES(?,?,?,?,?)", (uid, *data_list, now))
    elif table == "name":
        cur.execute("INSERT INTO name_record(user_id,type,desc,result,create_time) VALUES(?,?,?,?,?)", (uid, *data_list, now))
    elif table == "art":
        cur.execute("INSERT INTO art_record(user_id,style,scene,content,create_time) VALUES(?,?,?,?,?)", (uid, *data_list, now))
    elif table == "chat":
        cur.execute("INSERT INTO chat_record(user_id,ask,reply,create_time) VALUES(?,?,?,?)", (uid, *data_list, now))
    conn.commit()
    search_data.clear()

@st.cache_data(ttl=60)
def search_data(table, key_word, uid):
    conn = get_db_connection()
    cur = conn.cursor()
    if table == "book":
        res = cur.execute("SELECT * FROM book_record WHERE user_id=? AND book_name LIKE ?", (uid, f'%{key_word}%')).fetchall()
    elif table == "name":
        res = cur.execute("SELECT * FROM name_record WHERE user_id=? AND desc LIKE ?", (uid, f'%{key_word}%')).fetchall()
    elif table == "art":
        res = cur.execute("SELECT * FROM art_record WHERE user_id=? AND scene LIKE ?", (uid, f'%{key_word}%')).fetchall()
    else:
        res = cur.execute("SELECT * FROM chat_record WHERE user_id=? AND ask LIKE ?", (uid, f'%{key_word}%')).fetchall()
    return res

def delete_data(table, row_id, uid):
    conn = get_db_connection()
    cur = conn.cursor()
    if table == "book":
        cur.execute("DELETE FROM book_record WHERE id=? AND user_id=?", (row_id, uid))
    elif table == "name":
        cur.execute("DELETE FROM name_record WHERE id=? AND user_id=?", (row_id, uid))
    elif table == "art":
        cur.execute("DELETE FROM art_record WHERE id=? AND user_id=?", (row_id, uid))
    else:
        cur.execute("DELETE FROM chat_record WHERE id=? AND user_id=?", (row_id, uid))
    conn.commit()
    search_data.clear()

#初始化数据库
init_db()

#AI配置 填入自己智谱key
API_KEY = "4279ab216a1e4c8282b51f541aff703e.HJdsPUVWqGbMD7t0"
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
MODEL_NAME = "glm-4-flash"
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
SYSTEM_MSG = "你是小政，语言生活化自然，书评通俗详实，起名文雅有寓意，朋友圈文案贴合场景，无生硬AI话术。"

#页面CSS精简
st.set_page_config(page_title="小政书香AI助手", page_icon="📜", layout="centered", initial_sidebar_state="collapsed")
st.markdown("""
<style>
*{font-family:"SimSun","Microsoft YaHei",serif;}
#MainMenu,footer,header,.stDeployButton,[data-testid="stToolbar"]{display:none !important;}
.stApp{background:linear-gradient(135deg,#f8f2e4,#f0e6d2,#e9dcc3);background-attachment:fixed;}
.func-card{background:rgba(255,253,246,0.92);border:1px solid #d4c2a8;border-radius:12px;box-shadow:0 3px 12px rgba(120,95,65,0.18);}
div[data-testid="stChatMessage"]{background:rgba(255,253,246,0.9);border:1px solid #d4c2a8;border-radius:10px;}
input,textarea,.stSelectbox>div>div{background:rgba(255,253,246,0.9);border:1px solid #d4c2a8;border-radius:8px;color:#4a3f30;}
.stButton>button{height:44px;border-radius:10px;font-size:15px;letter-spacing:1px;}
.stButton>button[kind="primary"]{background:#82674b;color:#fff8e8;border:none;}
.stButton>button[kind="secondary"]{background:transparent;border:1px solid #b8a48c;}
</style>
""", unsafe_allow_html=True)

#会话缓存初始化
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "now_page" not in st.session_state:
    st.session_state.now_page = "💬 对话"
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []

#====================优化3：登录页全部套Form，打字不刷新====================
if st.session_state.user_id is None:
    st.markdown("## 📜 书香AI助手 用户中心")
    tab_login, tab_reg, tab_reset = st.tabs(["登录", "注册", "密码重置"])
    #登录表单
    with tab_login:
        with st.form("login_form"):
            un = st.text_input("账号")
            pw = st.text_input("密码", type="password")
            sub = st.form_submit_button("登录", type="primary")
            if sub:
                user = get_user_info(un)
                if user and check_hash(pw, user[2]):
                    st.session_state.user_id = user[0]
                    st.session_state.username = user[1]
                    st.session_state.user_role = user[3]
                    st.rerun()
                else:
                    st.error("账号或密码错误")
    #注册表单
    with tab_reg:
        with st.form("reg_form"):
            new_u = st.text_input("新建用户名")
            new_p = st.text_input("设置密码", type="password")
            sub = st.form_submit_button("注册", type="primary")
            if sub:
                if get_user_info(new_u):
                    st.warning("用户名已存在")
                else:
                    user_register(new_u, new_p)
                    st.success("注册成功，请前往登录")
    #重置密码表单
    with tab_reset:
        with st.form("reset_form"):
            reset_u = st.text_input("待重置账号")
            reset_p = st.text_input("新设密码", type="password")
            sub = st.form_submit_button("确认重置", type="primary")
            if sub:
                if get_user_info(reset_u):
                    reset_password(reset_u, reset_p)
                    st.success("密码重置成功")
                else:
                    st.warning("账号不存在")
    st.stop()

#顶部栏
col_top1, col_top2, col_top3 = st.columns([3, 1, 1])
with col_top1:
    st.markdown(f"### 📜 小政AI助手｜欢迎 {st.session_state.username}")
with col_top2:
    if st.button("退出登录", type="secondary"):
        st.session_state.clear()
        st.rerun()
admin_open = False
if st.session_state.user_role == "admin":
    with col_top3:
        admin_open = st.button("管理员后台", type="secondary")

#导航栏
page_list = ["💬 对话", "📖 书摘", "🏷️ 起名", "📸 朋友圈文案", "📂 我的存档"]
col_nav = st.columns(len(page_list))
for idx, name in enumerate(page_list):
    with col_nav[idx]:
        if st.button(name, use_container_width=True, type="primary" if st.session_state.now_page == name else "secondary"):
            st.session_state.now_page = name
            st.rerun()
current_page = st.session_state.now_page
uid = st.session_state.user_id

#====================优化5：对话只渲染最新20条聊天记录====================
if current_page == "💬 对话":
    for item in st.session_state.chat_log[-20:]:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
    ask_txt = st.chat_input("输入问题开始聊天")
    if ask_txt and API_KEY:
        st.session_state.chat_log.append({"role": "user", "content": ask_txt})
        with st.chat_message("user"):
            st.markdown(ask_txt)
        msg_all = [{"role": "system", "content": SYSTEM_MSG}] + st.session_state.chat_log[-20:]
        res = client.chat.completions.create(model=MODEL_NAME, messages=msg_all)
        ans_txt = res.choices[0].message.content
        st.session_state.chat_log.append({"role": "assistant", "content": ans_txt})
        with st.chat_message("assistant"):
            st.markdown(ans_txt)
        insert_data("chat", [ask_txt, ans_txt], uid)
    elif not API_KEY:
        st.warning("请在代码内填入API_KEY才可调用AI")

#====================优化3：书摘页面Form包裹====================
elif current_page == "📖 书摘":
    st.markdown('<div class="func-card"><h3>📖 书籍解读与同类推荐</h3></div>', unsafe_allow_html=True)
    with st.form("book_form"):
        book_name = st.text_input("书籍名称")
        book_author = st.text_input("作者（选填）")
        sub = st.form_submit_button("生成书评", type="primary")
    if sub and book_name and API_KEY:
        with st.spinner("正在解析书籍..."):
            req = f"详细介绍《{book_name}》，作者{book_author}，简介、梗概、亮点、适配人群+同类书单"
            ans = client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_MSG},{"role":"user","content":req}]).choices[0].message.content
            st.markdown(ans)
            insert_data("book", [book_name, book_author, ans], uid)

#====================优化3：起名页面Form====================
elif current_page == "🏷️ 起名":
    st.markdown('<div class="func-card"><h3>🏷️ 文艺智能起名</h3></div>', unsafe_allow_html=True)
    with st.form("name_form"):
        name_type = st.selectbox("起名分类", ["品牌店铺", "宠物名字", "网名笔名", "小说角色"])
        name_desc = st.text_input("风格与需求描述")
        num = st.slider("生成数量", 3, 10, 5)
        sub = st.form_submit_button("一键生成", type="primary")
    if sub and name_desc and API_KEY:
        with st.spinner("构思名称..."):
            req = f"生成{num}个{name_type}名字，{name_desc}，附带简短释义"
            ans = client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_MSG},{"role":"user","content":req}]).choices[0].message.content
            st.markdown(ans)
            insert_data("name", [name_type, name_desc, ans], uid)

#====================优化3：文案页面Form====================
elif current_page == "📸 朋友圈文案":
    st.markdown('<div class="func-card"><h3>📸 朋友圈文案生成</h3></div>', unsafe_allow_html=True)
    with st.form("art_form"):
        art_style = st.selectbox("文案风格", ["日常随性", "文艺走心", "幽默搞笑", "简约短句", "氛围感"])
        art_scene = st.text_input("场景描述（读书、美食、出游等）")
        sub = st.form_submit_button("生成文案", type="primary")
    if sub and art_scene and API_KEY:
        with st.spinner("撰写文案..."):
            req = f"场景：{art_scene}，风格：{art_style}，多条长短文案"
            ans = client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_MSG},{"role":"user","content":req}]).choices[0].message.content
            st.markdown(ans)
            insert_data("art", [art_style, art_scene, ans], uid)

#====================优化4：存档分页（每页5条）====================
elif current_page == "📂 我的存档":
    st.markdown('<div class="func-card"><h3>📂 个人历史存档</h3></div>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["书籍存档", "起名存档", "文案存档", "对话存档"])
    page_size = 5

    def page_render(table, tab):
        with tab:
            with st.form(f"search_{table}"):
                key = st.text_input("检索关键词")
                st.form_submit_button("搜索")
            data = search_data(table, key, uid)
            total = len(data)
            max_page = total // page_size + 1 if total else 1
            page = st.number_input("页码", min_value=1, max_value=max_page, value=1)
            start = (page - 1) * page_size
            end = start + page_size
            for row in data[start:end]:
                st.write(f"📅{row[-1]}｜{row[2]} {row[3]}")
                st.text(row[4])
                if st.button("删除", key=f"{table}{row[0]}"):
                    delete_data(table, row[0], uid)
                    st.rerun()

    page_render("book", tab1)
    page_render("name", tab2)
    page_render("art", tab3)
    page_render("chat", tab4)

#管理员后台
if admin_open:
    st.markdown("## ⚙管理员后台｜用户管理")
    all_user = get_all_users()
    st.table(all_user)
    st.info("admin超级管理员，可查看全部注册用户；普通用户仅查看自身数据")
