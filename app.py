"""
小政AI助手｜修复数据表空格+SQL字段错位报错，登录才可使用，数据绑定用户名，管理员查看全量记录
默认管理员账号：admin / 123456
"""
import streamlit as st
from openai import OpenAI
from datetime import datetime
import sqlite3

# ========== 数据库初始化 ==========
def init_db():
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    # 用户信息表
    cur.execute('''CREATE TABLE IF NOT EXISTS user_info(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        create_time TEXT
    )''')
    # 书籍记录表（首字段username绑定用户）
    cur.execute('''CREATE TABLE IF NOT EXISTS book_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        book_name TEXT,
        author TEXT,
        content TEXT,
        create_time TEXT
    )''')
    # 起名记录表
    cur.execute('''CREATE TABLE IF NOT EXISTS name_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        type TEXT,
        desc TEXT,
        result TEXT,
        create_time TEXT
    )''')
    # 朋友圈文案表
    cur.execute('''CREATE TABLE IF NOT EXISTS art_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        style TEXT,
        scene TEXT,
        content TEXT,
        create_time TEXT
    )''')
    # 【重点修复：表名chat_record无空格，之前空格chat record导致SQL报错】
    cur.execute('''CREATE TABLE IF NOT EXISTS chat_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        ask TEXT,
        reply TEXT,
        create_time TEXT
    )''')
    # 默认管理员账号
    cur.execute("INSERT OR IGNORE INTO user_info(username,password,role,create_time) VALUES(?,?,?,?)",
                ("admin","123456","manager",datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

# 插入数据：带入登录用户名
def add_sql(table, uname, data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    if table == "book":
        cur.execute("INSERT INTO book_record(username,book_name,author,content,create_time) VALUES(?,?,?,?,?)", (uname,*data, now))
    elif table == "name":
        cur.execute("INSERT INTO name_record(username,type,desc,result,create_time) VALUES(?,?,?,?,?)", (uname,*data, now))
    elif table == "art":
        cur.execute("INSERT INTO art_record(username,style,scene,content,create_time) VALUES(?,?,?,?,?)", (uname,*data, now))
    elif table == "chat":
        # 修复：表名chat_record，字段无空格
        cur.execute("INSERT INTO chat_record(username,ask,reply,create_time) VALUES(?,?,?,?)", (uname,*data, now))
    conn.commit()
    conn.close()

# 查询：普通用户查自己，管理员全量查询
def search_sql(table, key="", uname="", is_admin=False):
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    sql_base = ""
    params = []
    if is_admin:
        where_sql = " WHERE 1=1 "
    else:
        where_sql = " WHERE username=? "
        params.append(uname)

    if key.strip()!="":
        if table=="book":
            where_sql += " AND book_name LIKE ? "
        elif table=="name":
            where_sql += " AND desc LIKE ? "
        elif table=="art":
            where_sql += " AND scene LIKE ? "
        elif table=="chat":
            where_sql += " AND ask LIKE ? "
        params.append(f'%{key}%')

    if table == "book":
        sql_base = f"select * from book_record {where_sql}"
    elif table == "name":
        sql_base = f"select * from name_record {where_sql}"
    elif table == "art":
        sql_base = f"select * from art_record {where_sql}"
    elif table == "chat":
        sql_base = f"select * from chat_record {where_sql}"
    cur.execute(sql_base, params)
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

# 账号工具函数
def check_user(uname,pwd):
    conn=sqlite3.connect("user_data.db")
    cur=conn.cursor()
    cur.execute("select role from user_info where username=? and password=?",(uname,pwd))
    res=cur.fetchone()
    conn.close()
    return res

def reset_pwd(uname,new_pwd):
    conn=sqlite3.connect("user_data.db")
    cur=conn.cursor()
    cur.execute("update user_info set password=? where username=?",(new_pwd,uname))
    conn.commit()
    conn.close()

def add_new_user(uname,pwd,role):
    now=datetime.now().strftime("%Y-%m-%d %H:%M")
    conn=sqlite3.connect("user_data.db")
    cur=conn.cursor()
    try:
        cur.execute("INSERT INTO user_info(username,password,role,create_time) VALUES(?,?,?,?)",(uname,pwd,role,now))
        conn.commit()
        flag=True
    except:
        flag=False
    conn.close()
    return flag

# 初始化数据库
init_db()

# ========== API配置 ==========
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

# ==========页面样式CSS==========
st.set_page_config(page_title="小政",page_icon="📜",layout="centered",initial_sidebar_state="collapsed")
st.markdown("""
<style>
* {font-family:"Microsoft Yahei","SimSun",serif;}
#MainMenu,footer,header,.stDeployButton,[data-testid="stToolbar"]{display:none !important;visibility:hidden;}
.stApp{background:linear-gradient(135deg,#f8f2e4 0%,#f0e6d2 50%,#e9dcc3 100%) !important;background-attachment:fixed;}
.func-card{background:rgba(255,253,246,0.92) !important;border:1px solid #d4c2a8;border-radius:12px;box-shadow:0 3px 12px rgba(120,95,65,0.18);padding:10px;}
div[data-testid="stChatMessage"]{background:rgba(255,253,246,0.9) !important;border:1px solid #d4c2a8;border-radius:10px;}
.stButton>button{height:44px;border-radius:10px;font-size:15px;letter-spacing:1px;}
.stButton>button[kind="primary"]{background:#82674b !important;color:#fff8e8;border:none;}
.stButton>button[kind="secondary"]{background:transparent;border:1px solid #b8a48c;color:inherit;}
</style>
""",unsafe_allow_html=True)

# ==========会话状态初始化==========
if "login" not in st.session_state:
    st.session_state.login=False
    st.session_state.user_name=""
    st.session_state.user_role=""
if "pop_login" not in st.session_state:st.session_state.pop_login=False
if "pop_reg" not in st.session_state:st.session_state.pop_reg=False
if "pop_reset" not in st.session_state:st.session_state.pop_reset=False
if "pop_adduser" not in st.session_state:st.session_state.pop_adduser=False

# 顶部功能按钮
user_bar=st.columns([3,1,1,1,1,1])
if not st.session_state.login:
    with user_bar[1]:
        if st.button("🔐登录",type="secondary"):st.session_state.pop_login=True
    with user_bar[2]:
        if st.button("📝注册",type="secondary"):st.session_state.pop_reg=True
else:
    user_bar[0].write(f"👤{st.session_state.user_name}【{st.session_state.user_role}】")
    with user_bar[1]:
        if st.button("🔑改密",type="secondary"):st.session_state.pop_reset=True
    with user_bar[2]:
        if st.session_state.user_role=="manager":
            if st.button("➕开账号",type="secondary"):st.session_state.pop_adduser=True
    with user_bar[3]:
        if st.button("🚪退出",type="secondary"):
            st.session_state.login=False
            st.session_state.user_name=""
            st.session_state.user_role=""
            st.rerun()

st.markdown("### 📜 小政 AI 助手")

# ==========未登录拦截：必须登录注册才能使用功能==========
if not st.session_state.login:
    st.info("⚠️ 请先登录或注册账号后，方可使用对话、书摘、起名、文案、存档全部功能！")
else:
    nav_items = ["💬 对话", "📖 书摘", "🏷️ 起名", "📸 朋友圈文案", "📂 我的存档"]
    cols = st.columns(len(nav_items))
    if "current_func" not in st.session_state:st.session_state.current_func=nav_items[0]
    for idx,name in enumerate(nav_items):
        with cols[idx]:
            if st.button(name,use_container_width=True,type="primary" if st.session_state.current_func==name else "secondary"):
                st.session_state.current_func=name;st.rerun()
    func=st.session_state.current_func
    uname=st.session_state.user_name
    is_admin=True if st.session_state.user_role=="manager" else False

    #1对话模块
    if func=="💬 对话":
        if "chat_history" not in st.session_state:st.session_state.chat_history=[]
        for i in st.session_state.chat_history:
            with st.chat_message(i["role"]):st.markdown(i["content"])
        prompt=st.chat_input("来，随便聊～")
        if prompt:
            st.session_state.chat_history.append({"role":"user","content":prompt})
            with st.chat_message("user"):st.markdown(prompt)
            msg=[{"role":"system","content":SYSTEM_PROMPT}]+st.session_state.chat_history
            ans=client.chat.completions.create(model=MODEL_NAME,messages=msg).choices[0].message.content
            st.session_state.chat_history.append({"role":"assistant","content":ans})
            with st.chat_message("assistant"):st.markdown(ans)
            add_sql("chat",uname,[prompt,ans])

    #2书摘模块
    elif func=="📖 书摘":
        st.markdown('<div class="func-card"><h3>📖 书籍介绍 & 同类推荐</h3></div>',unsafe_allow_html=True)
        bk=st.text_input("书名")
        aut=st.text_input("作者（选填）")
        if st.button("📚 获取介绍",type="primary") and bk:
            with st.spinner("整理中..."):
                ask=f"详细介绍《{bk}》{aut}，梗概亮点+同类推荐，口语化。"
                ans=client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":ask}]).choices[0].message.content
                st.markdown(ans)
                add_sql("book",uname,[bk,aut,ans])

    #3起名模块
    elif func=="🏷️ 起名":
        st.markdown('<div class="func-card"><h3>🏷️ AI起名</h3></div>',unsafe_allow_html=True)
        typ=st.selectbox("类型",["品牌店铺","宠物名字","网名笔名","小说角色"])
        desc=st.text_input("风格/要求描述")
        num=st.slider("数量",3,10,5)
        if st.button("✨生成名字",type="primary") and desc:
            with st.spinner("构思中..."):
                ask=f"生成{num}个{typ}名字：{desc}，附带释义。"
                ans=client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":ask}]).choices[0].message.content
                st.markdown(ans)
                add_sql("name",uname,[typ,desc,ans])

    #4朋友圈文案模块
    elif func=="📸 朋友圈文案":
        st.markdown('<div class="func-card"><h3>📸 朋友圈文案生成</h3></div>',unsafe_allow_html=True)
        sty=st.selectbox("风格",["日常随性","文艺走心","幽默搞笑","简约短句","氛围感"])
        scene=st.text_input("场景描述")
        if st.button("✨生成文案",type="primary") and scene:
            with st.spinner("撰写..."):
                ask=f"场景{scene}，{sty}多条朋友圈文案。"
                ans=client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":ask}]).choices[0].message.content
                st.markdown(ans)
                add_sql("art",uname,[sty,scene,ans])

    #5存档：管理员查看全用户，普通用户仅自己
    elif func=="📂 我的存档":
        st.markdown('<div class="func-card"><h3>📂 存档记录【{}】</h3></div>'.format("管理员全量查看" if is_admin else "仅本人记录"),unsafe_allow_html=True)
        tab1,tab2,tab3,tab4=st.tabs(["书籍","起名","文案","对话"])
        with tab1:
            kw=st.text_input("书名检索")
            data=search_sql("book",kw,uname,is_admin)
            for row in data:
                uid,usr,bk,aut,cont,dt=row
                st.write(f"📅{dt}｜用户:{usr}｜{bk}【{aut}】")
                st.text(cont)
                if st.button("删除",key=f'b{uid}'):del_sql("book",uid);st.rerun()
        with tab2:
            kw=st.text_input("需求检索")
            data=search_sql("name",kw,uname,is_admin)
            for row in data:
                uid,usr,typ,desc,res,dt=row
                st.write(f"📅{dt}｜用户:{usr}｜{typ}｜{desc}")
                st.text(res)
                if st.button("删除",key=f'n{uid}'):del_sql("name",uid);st.rerun()
        with tab3:
            kw=st.text_input("场景检索")
            data=search_sql("art",kw,uname,is_admin)
            for row in data:
                uid,usr,sty,sc,cont,dt=row
                st.write(f"📅{dt}｜用户:{usr}｜{sty}｜{sc}")
                st.text(cont)
                if st.button("删除",key=f'a{uid}'):del_sql("art",uid);st.rerun()
        with tab4:
            kw=st.text_input("提问检索")
            data=search_sql("chat",kw,uname,is_admin)
            for row in data:
                uid,usr,ask,rep,dt=row
                st.write(f"📅{dt}｜用户:{usr}｜提问：{ask}")
                st.text(f"回复：{rep}")
                if st.button("删除",key=f'c{uid}'):del_sql("chat",uid);st.rerun()

# ==========弹窗登录/注册/改密/管理员开户==========
#登录弹窗
if st.session_state.pop_login:
    with st.expander("🔐 用户登录",expanded=True):
        u=st.text_input("账号",key="lu")
        p=st.text_input("密码",type="password",key="lp")
        c1,c2=st.columns(2)
        with c1:
            if st.button("登录",type="primary",key="loginok"):
                ret=check_user(u,p)
                if ret:
                    st.session_state.login=True
                    st.session_state.user_name=u
                    st.session_state.user_role=ret[0]
                    st.session_state.pop_login=False;st.rerun()
                else:st.error("账号密码错误")
        with c2:
            if st.button("关闭",key="lgclose"):st.session_state.pop_login=False;st.rerun()

#注册弹窗
if st.session_state.pop_reg:
    with st.expander("📝 新用户注册(普通user)",expanded=True):
        ru=st.text_input("注册用户名",key="ru")
        rp=st.text_input("注册密码",type="password",key="rp")
        c1,c2=st.columns(2)
        with c1:
            if st.button("注册",type="primary",key="regok") and ru and rp:
                if add_new_user(ru,rp,"user"):
                    st.success("注册成功，请登录");st.session_state.pop_reg=False;st.rerun()
                else:st.error("用户名已存在")
        with c2:
            if st.button("关闭",key="rgclose"):st.session_state.pop_reg=False;st.rerun()

#改密弹窗
if st.session_state.pop_reset:
    with st.expander("🔑 修改个人密码",expanded=True):
        np=st.text_input("新密码",type="password",key="newp")
        c1,c2=st.columns(2)
        with c1:
            if st.button("确认修改",type="primary",key="resok") and np:
                reset_pwd(st.session_state.user_name,np)
                st.success("修改成功");st.session_state.pop_reset=False;st.rerun()
        with c2:
            if st.button("取消",key="rescancel"):st.session_state.pop_reset=False;st.rerun()

#管理员新建账号弹窗
if st.session_state.pop_adduser and st.session_state.user_role=="manager":
    with st.expander("➕管理员创建账号",expanded=True):
        au=st.text_input("新建账号",key="auser")
        ap=st.text_input("新建密码",type="password",key="apwd")
        role_sel=st.selectbox("权限",["user普通用户","manager管理员"])
        r=role_sel.replace("普通用户","").replace("管理员","")
        c1,c2=st.columns(2)
        with c1:
            if st.button("创建",type="primary",key="addok") and au and ap:
                if add_new_user(au,ap,r):st.success("创建成功")
                else:st.error("账号已占用")
        with c2:
            if st.button("关闭",key="addclose"):st.session_state.pop_adduser=False;st.rerun()
