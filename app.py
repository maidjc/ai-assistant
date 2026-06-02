"""
书香AI助手｜多用户账号版
1. 内置默认管理员：账号admin，密码123456
2. 密码简单加密存储，各用户数据隔离
3. 未登录锁功能，登录后生成内容只存在自己账号下
"""
import streamlit as st
from openai import OpenAI
from datetime import datetime
import sqlite3
import hashlib

# 密码MD5加密
def get_pwd_md5(pwd):
    return hashlib.md5(pwd.encode()).hexdigest()

# 数据库初始化
def init_db():
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    # 用户表
    cur.execute('''CREATE TABLE IF NOT EXISTS user(
        uid INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')
    # 书籍
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
    # 预置管理员账号 admin 123456
    try:
        cur.execute("INSERT INTO user(username,password) VALUES(?,?)",("admin",get_pwd_md5("123456")))
    except:
        pass
    conn.commit()
    conn.close()

# 用户注册
def reg_user(uname,pwd):
    conn=sqlite3.connect("user_data.db")
    c=conn.cursor()
    try:
        c.execute("INSERT INTO user(username,password) VALUES(?,?)",(uname,get_pwd_md5(pwd)))
        conn.commit()
        res=True
    except:
        res=False
    conn.close()
    return res

# 登录校验
def login_user(uname,pwd):
    conn=sqlite3.connect("user_data.db")
    c=conn.cursor()
    c.execute("SELECT uid FROM user WHERE username=? AND password=?",(uname,get_pwd_md5(pwd)))
    ret=c.fetchone()
    conn.close()
    return ret[0] if ret else None

# 插入数据（绑定用户ID）
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

# 只查询当前用户数据
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

# 删除记录
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

# API配置
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

# 页面样式
st.set_page_config(page_title="书香AI助手",page_icon="📜",layout="centered")
st.markdown("""
<style>
.stApp {background: linear-gradient(135deg, #f8f2e4 0%, #f0e6d2 50%, #e9dcc3 100%) !important;}
#MainMenu,footer,header {display:none !important;}
.func-card{background:rgba(255,253,246,0.92);border:1px solid #d4c2a8;border-radius:12px;padding:12px;}
</style>
""",unsafe_allow_html=True)

# 登录逻辑
if "uid" not in st.session_state:
    st.session_state.uid = None

if st.session_state.uid is None:
    st.markdown("## 📜书香AI｜用户登录")
    login_tab, reg_tab = st.tabs(["登录","新用户注册"])
    with login_tab:
        un = st.text_input("用户名")
        pw = st.text_input("密码",type="password")
        if st.button("登录",type="primary"):
            uid = login_user(un,pw)
            if uid:
                st.session_state.uid = uid
                st.success("登录成功！")
                st.rerun()
            else:
                st.error("账号或密码错误")
    with reg_tab:
        new_un = st.text_input("设置用户名")
        new_pw = st.text_input("设置密码",type="password")
        if st.button("注册账号"):
            if reg_user(new_un,new_pw):
                st.success("注册成功，返回登录页登录")
            else:
                st.error("用户名已存在")
    st.info("默认管理员账号：admin｜密码：123456")
    st.stop()

# 当前登录用户ID
curr_uid = st.session_state.uid
st.markdown(f"### 📜小政AI｜已登录用户ID：{curr_uid}")
if st.button("退出登录"):
    del st.session_state.uid
    st.rerun()

# 导航栏
nav_items = ["💬 对话", "📖 书摘", "🏷️ 起名", "📸 朋友圈文案", "📂 我的存档"]
if "current_func" not in st.session_state:
    st.session_state.current_func = nav_items[0]
cols = st.columns(len(nav_items))
for idx,name in enumerate(nav_items):
    with cols[idx]:
        if st.button(name,use_container_width=True,type="primary" if st.session_state.current_func==name else "secondary"):
            st.session_state.current_func = name
            st.rerun()
func = st.session_state.current_func

# 1.对话
if func == "💬 对话":
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    prompt = st.chat_input("输入消息开始聊天")
    if prompt:
        st.session_state.chat_history.append({"role":"user","content":prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        messages = [{"role":"system","content":SYSTEM_PROMPT}] + st.session_state.chat_history
        res = client.chat.completions.create(model=MODEL_NAME,messages=messages)
        ans = res.choices[0].message.content
        st.session_state.chat_history.append({"role":"assistant","content":ans})
        with st.chat_message("assistant"):
            st.markdown(ans)
        add_sql("chat",[prompt,ans],curr_uid)

# 2.书摘
elif func == "📖 书摘":
    st.markdown('<div class="func-card"><h3>📖书籍简介与推荐</h3></div>',unsafe_allow_html=True)
    bk_name = st.text_input("书名")
    author = st.text_input("作者（选填）")
    if st.button("生成内容",type="primary") and bk_name:
        ask = f"详细介绍《{bk_name}》作者{author}，内容梗概、亮点、适配人群+同类推荐"
        ans = client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":ask}]).choices[0].message.content
        st.markdown(ans)
        add_sql("book",[bk_name,author,ans],curr_uid)

#3.起名
elif func == "🏷️ 起名":
    st.markdown('<div class="func-card"><h3>🏷️AI智能起名</h3></div>',unsafe_allow_html=True)
    typ = st.selectbox("起名分类",["品牌店铺","宠物名字","网名笔名","小说角色"])
    desc = st.text_input("起名要求、风格描述")
    num = st.slider("生成数量",3,10,5)
    if st.button("生成名字",type="primary") and desc:
        ask = f"生成{num}个{typ}名称，要求：{desc}，每个附带简短释义"
        ans = client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":ask}]).choices[0].message.content
        st.markdown(ans)
        add_sql("name",[typ,desc,ans],curr_uid)

#4.朋友圈文案
elif func == "📸 朋友圈文案":
    st.markdown('<div class="func-card"><h3>📸朋友圈文案生成</h3></div>',unsafe_allow_html=True)
    style = st.selectbox("文案风格",["日常随性","文艺走心","幽默搞笑","简约短句","氛围感"])
    scene = st.text_input("场景描述")
    if st.button("生成文案",type="primary") and scene:
        ask = f"场景：{scene}，风格：{style}，多条长短搭配朋友圈文案"
        ans = client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":ask}]).choices[0].message.content
        st.markdown(ans)
        add_sql("art",[style,scene,ans],curr_uid)

#5.我的存档（仅当前用户数据）
elif func == "📂 我的存档":
    st.markdown('<div class="func-card"><h3>📂个人历史存档（仅本人数据）</h3></div>',unsafe_allow_html=True)
    tab1,tab2,tab3,tab4 = st.tabs(["书籍存档","起名存档","文案存档","对话存档"])
    #书籍
    with tab1:
        kw = st.text_input("关键词搜索书名")
        data = search_sql("book",kw,curr_uid)
        for row in data:
            st.write(f"📅{row[5]}｜{row[2]}【{row[3]}】")
            st.text(row[4])
            if st.button("删除",key=f'b{row[0]}'):
                del_sql("book",row[0])
                st.rerun()
    #起名
    with tab2:
        kw = st.text_input("关键词搜索需求")
        data = search_sql("name",kw,curr_uid)
        for row in data:
            st.write(f"📅{row[5]}｜{row[2]}｜需求：{row[3]}")
            st.text(row[4])
            if st.button("删除",key=f'n{row[0]}'):
                del_sql("name",row[0])
                st.rerun()
    #文案
    with tab3:
        kw = st.text_input("关键词搜索场景")
        data = search_sql("art",kw,curr_uid)
        for row in data:
            st.write(f"📅{row[5]}｜{row[2]}｜{row[3]}")
            st.text(row[4])
            if st.button("删除",key=f'a{row[0]}'):
                del_sql("art",row[0])
                st.rerun()
    #聊天
    with tab4:
        kw = st.text_input("关键词搜索提问")
        data = search_sql("chat",kw,curr_uid)
        for row in data:
            st.write(f"📅{row[4]} 用户：{row[2]}")
            st.text(f"小政：{row[3]}")
            if st.button("删除",key=f'c{row[0]}'):
                del_sql("chat",row[0])
                st.rerun()
