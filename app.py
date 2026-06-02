"""
书香AI助手｜带用户名分用户存储版
多用户隔离：每个账号独立存档，互不干扰
"""
import streamlit as st
from openai import OpenAI
from datetime import datetime
import sqlite3

# ==================== 数据库升级：新增用户表、全部表加user_id ====================
def init_db():
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    # 用户表
    cur.execute('''CREATE TABLE IF NOT EXISTS user(
        uid INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')
    # 书籍表增加user_id
    cur.execute('''CREATE TABLE IF NOT EXISTS book_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        book_name TEXT,
        author TEXT,
        content TEXT,
        create_time TEXT
    )''')
    # 起名
    cur.execute('''CREATE TABLE IF NOT EXISTS name_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        desc TEXT,
        result TEXT,
        create_time TEXT
    )''')
    # 文案
    cur.execute('''CREATE TABLE IF NOT EXISTS art_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        style TEXT,
        scene TEXT,
        content TEXT,
        create_time TEXT
    )''')
    # 聊天
    cur.execute('''CREATE TABLE IF NOT EXISTS chat_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        ask TEXT,
        reply TEXT,
        create_time TEXT
    )''')
    conn.commit()
    conn.close()

# 新增用户
def reg_user(uname,pwd):
    conn=sqlite3.connect("user_data.db")
    c=conn.cursor()
    try:
        c.execute("INSERT INTO user(username,password) VALUES(?,?)",(uname,pwd))
        conn.commit()
        flag=True
    except:
        flag=False
    conn.close()
    return flag

# 登录校验，返回用户uid
def login_user(uname,pwd):
    conn=sqlite3.connect("user_data.db")
    c=conn.cursor()
    c.execute("SELECT uid FROM user WHERE username=? AND password=?",(uname,pwd))
    res=c.fetchone()
    conn.close()
    return res[0] if res else None

# 新增数据（携带当前登录user_id）
def add_sql(table, data, user_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    if table == "book":
        cur.execute("INSERT INTO book_record(user_id,book_name,author,content,create_time) VALUES(?,?,?,?,?)", (user_id,*data, now))
    elif table == "name":
        cur.execute("INSERT INTO name_record(user_id,type,desc,result,create_time) VALUES(?,?,?,?,?)", (user_id,*data, now))
    elif table == "art":
        cur.execute("INSERT INTO art_record(user_id,style,scene,content,create_time) VALUES(?,?,?,?,?)", (user_id,*data, now))
    elif table == "chat":
        cur.execute("INSERT INTO chat_record(user_id,ask,reply,create_time) VALUES(?,?,?,?)", (user_id,*data, now))
    conn.commit()
    conn.close()

# 查询只查当前登录用户的数据
def search_sql(table, key="", user_id=0):
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    if table == "book":
        cur.execute("select * from book_record where user_id=? and book_name like ?", (user_id,f'%{key}%'))
    elif table == "name":
        cur.execute("select * from name_record where user_id=? and desc like ?", (user_id,f'%{key}%'))
    elif table == "art":
        cur.execute("select * from art_record where user_id=? and scene like ?", (user_id,f'%{key}%'))
    elif table == "chat":
        cur.execute("select * from chat_record where user_id=? and ask like ?", (user_id,f'%{key}%'))
    res = cur.fetchall()
    conn.close()
    return res

# 删除
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

init_db()

# ==================== API配置 ====================
try:
    API_KEY = st.secrets["API_KEY"]
except:
    API_KEY = "4279ab216a1e4c8282b51f541aff703e.HJdsPUVWqGbMD7t0"
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
MODEL_NAME = "glm-4-flash"
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
SYSTEM_PROMPT = """
你是「小政」，风趣随和、接地气，日常聊天自然不生硬，无AI机械话术；
书摘通俗口语、起名简约有寓意、朋友圈文案贴合风格。
"""

# ==================== 页面样式 ====================
st.set_page_config(page_title="小政AI",page_icon="📜",layout="centered")
st.markdown("""
<style>
.stApp {background: linear-gradient(135deg, #f8f2e4 0%, #f0e6d2 50%, #e9dcc3 100%) !important;}
#MainMenu,footer,header{display:none !important;}
.func-card{background:rgba(255,253,246,0.92);border:1px solid #d4c2a8;border-radius:12px;padding:10px;}
</style>
""",unsafe_allow_html=True)

# ==================== 登录注册模块 ====================
if "uid" not in st.session_state:
    st.session_state.uid = None
if st.session_state.uid is None:
    st.markdown("## 📜书香AI助手 · 用户登录")
    tab1,tab2 = st.tabs(["登录","注册"])
    with tab1:
        un = st.text_input("用户名")
        pw = st.text_input("密码",type="password")
        if st.button("登录"):
            uid = login_user(un,pw)
            if uid:
                st.session_state.uid=uid
                st.success("登录成功！")
                st.rerun()
            else:
                st.error("账号或密码错误")
    with tab2:
        unr = st.text_input("新建用户名")
        pwr = st.text_input("设置密码",type="password")
        if st.button("注册"):
            if reg_user(unr,pwr):
                st.success("注册完成，请去登录")
            else:
                st.error("用户名已被占用")
    st.stop() #未登录停止往下运行

# 已登录获取当前用户ID
curr_uid = st.session_state.uid
st.markdown(f"### 📜 小政 AI 助手｜当前用户：{curr_uid}")
if st.button("退出登录"):
    del st.session_state.uid
    st.rerun()

# 导航
nav_items = ["💬 对话", "📖 书摘", "🏷️ 起名", "📸 朋友圈文案", "📂 我的存档"]
if "current_func" not in st.session_state:
    st.session_state.current_func=nav_items[0]
cols=st.columns(len(nav_items))
for i,name in enumerate(nav_items):
    with cols[i]:
        if st.button(name,use_container_width=True,type="primary" if st.session_state.current_func==name else "secondary"):
            st.session_state.current_func=name
            st.rerun()
func=st.session_state.current_func

# ==================== 1对话 ====================
if func == "💬 对话":
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    for i in st.session_state.chat_history:
        with st.chat_message(i["role"]):st.markdown(i["content"])
    p=st.chat_input("聊天")
    if p:
        st.session_state.chat_history.append({"role":"user","content":p})
        with st.chat_message("user"):st.markdown(p)
        msg=[{"role":"system","content":SYSTEM_PROMPT}]+st.session_state.chat_history
        ans=client.chat.completions.create(model=MODEL_NAME,messages=msg).choices[0].message.content
        st.session_state.chat_history.append({"role":"assistant","content":ans})
        with st.chat_message("assistant"):st.markdown(ans)
        add_sql("chat",[p,ans],curr_uid)

# ====================2书摘====================
elif func == "📖 书摘":
    st.markdown('<div class="func-card"><h3>📖书籍介绍</h3></div>',unsafe_allow_html=True)
    bk=st.text_input("书名")
    aut=st.text_input("作者")
    if st.button("生成",type="primary") and bk:
        ask=f"介绍《{bk}》{aut}，梗概亮点+同类推荐"
        res=client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":ask}]).choices[0].message.content
        st.markdown(res)
        add_sql("book",[bk,aut,res],curr_uid)

# ====================3起名====================
elif func == "🏷️ 起名":
    st.markdown('<div class="func-card"><h3>🏷️AI起名</h3></div>',unsafe_allow_html=True)
    tp=st.selectbox("类型",["品牌","宠物","网名","角色"])
    desc=st.text_input("要求描述")
    num=st.slider("数量",3,10,5)
    if st.button("生成",type="primary") and desc:
        ask=f"{num}个{tp}名字，{desc}，附带释义"
        res=client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":ask}]).choices[0].message.content
        st.markdown(res)
        add_sql("name",[tp,desc,res],curr_uid)

# ====================4文案====================
elif func == "📸 朋友圈文案":
    st.markdown('<div class="func-card"><h3>📸朋友圈文案</h3></div>',unsafe_allow_html=True)
    sty=st.selectbox("风格",["随性","文艺","搞笑","短句","氛围感"])
    sce=st.text_input("场景")
    if st.button("生成",type="primary") and sce:
        ask=f"场景{sce}，风格{sty}多条朋友圈文案"
        res=client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":ask}]).choices[0].message.content
        st.markdown(res)
        add_sql("art",[sty,sce,res],curr_uid)

# ====================5我的存档（只显示当前用户）====================
elif func == "📂 我的存档":
    st.markdown('<div class="func-card"><h3>📂个人存档（仅自己数据）</h3></div>',unsafe_allow_html=True)
    t1,t2,t3,t4=st.tabs(["书籍","起名","文案","对话"])
    with t1:
        k=st.text_input("搜书名")
        d=search_sql("book",k,curr_uid)
        for r in d:
            st.write(f"{r[5]}｜{r[2]} {r[3]}")
            st.text(r[4])
            if st.button("删",key=f'b{r[0]}'):del_sql("book",r[0]);st.rerun()
    with t2:
        k=st.text_input("搜需求")
        d=search_sql("name",k,curr_uid)
        for r in d:
            st.write(f"{r[5]}｜{r[2]}：{r[3]}")
            st.text(r[4])
            if st.button("删",key=f'n{r[0]}'):del_sql("name",r[0]);st.rerun()
    with t3:
        k=st.text_input("搜场景")
        d=search_sql("art",k,curr_uid)
        for r in d:
            st.write(f"{r[5]}｜{r[2]} {r[3]}")
            st.text(r[4])
            if st.button("删",key=f'a{r[0]}'):del_sql("art",r[0]);st.rerun()
    with t4:
        k=st.text_input("搜提问")
        d=search_sql("chat",k,curr_uid)
        for r in d:
            st.write(f"{r[4]} 用户：{r[2]}")
            st.text(f"回复：{r[3]}")
            if st.button("删",key=f'c{r[0]}'):del_sql("chat",r[0]);st.rerun()
