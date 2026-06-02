"""
小政AI助手｜优化版：弹窗登录+密码重置+管理员后台+多用户隔离
自动升级旧数据表，保留原有历史数据
"""
import streamlit as st
from openai import OpenAI
from datetime import datetime
import sqlite3
import hashlib

# ====================== 全局配置 ======================
ADMIN_NAME = "admin"
ADMIN_PWD = "admin123"  #管理员初始密码，可自行修改

#密码哈希工具
def make_hash(pwd):
    return hashlib.sha256(str(pwd).encode()).hexdigest()
def check_hash(pwd, hashed):
    return make_hash(pwd) == hashed

# ====================== 数据库初始化&升级（兼容旧库） ======================
def init_db():
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    #用户表（新增密保字段用于找回密码）
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        question TEXT,
        answer_hash TEXT,
        create_time TEXT
    )''')
    #四张业务表
    cur.execute('''CREATE TABLE IF NOT EXISTS book_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        book_name TEXT,
        author TEXT,
        content TEXT,
        create_time TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS name_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        desc TEXT,
        result TEXT,
        create_time TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS art_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        style TEXT,
        scene TEXT,
        content TEXT,
        create_time TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS chat_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        ask TEXT,
        reply TEXT,
        create_time TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    conn.commit()
    conn.close()

#旧数据库自动升级补全user_id字段，保留历史数据
def upgrade_old_db():
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE book_record ADD COLUMN user_id INTEGER DEFAULT 1")
        cur.execute("ALTER TABLE name_record ADD COLUMN user_id INTEGER DEFAULT 1")
        cur.execute("ALTER TABLE art_record ADD COLUMN user_id INTEGER DEFAULT 1")
        cur.execute("ALTER TABLE chat_record ADD COLUMN user_id INTEGER DEFAULT 1")
    except Exception:
        pass
    #自动创建管理员账号
    user = get_user_by_username(ADMIN_NAME)
    if not user:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        cur.execute("INSERT INTO users(username,password_hash,question,answer_hash,create_time) VALUES(?,?,?,?,?)",
                    (ADMIN_NAME,make_hash(ADMIN_PWD),"管理员密保","",now))
    conn.commit()
    conn.close()

# ====================== 用户操作函数 ======================
def get_user_by_username(username):
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    cur.execute("SELECT id,username,password_hash,question,answer_hash FROM users WHERE username=?",(username,))
    res = cur.fetchone()
    conn.close()
    return res

#注册（带密保）
def create_user(username,pwd,ques,ans):
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cur.execute("INSERT INTO users(username,password_hash,question,answer_hash,create_time) VALUES(?,?,?,?,?)",
                (username,make_hash(pwd),ques,make_hash(ans),now))
    conn.commit()
    conn.close()

#密码重置
def reset_user_pwd(username,new_pwd):
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    cur.execute("UPDATE users SET password_hash=? WHERE username=?",(make_hash(new_pwd),username))
    conn.commit()
    conn.close()

#管理员：查询全部用户
def admin_get_all_user():
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    cur.execute("SELECT id,username,create_time FROM users")
    res = cur.fetchall()
    conn.close()
    return res

#管理员：根据用户id查全量数据
def admin_get_user_all_data(uid):
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    book = cur.execute("select * from book_record where user_id=?",(uid,)).fetchall()
    name = cur.execute("select * from name_record where user_id=?",(uid,)).fetchall()
    art = cur.execute("select * from art_record where user_id=?",(uid,)).fetchall()
    chat = cur.execute("select * from chat_record where user_id=?",(uid,)).fetchall()
    conn.close()
    return book,name,art,chat

# ====================== 数据存取CRUD ======================
def add_sql(table, data, user_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    if table == "book":
        cur.execute("INSERT INTO book_record(user_id,book_name,author,content,create_time) VALUES(?,?,?,?,?)",(user_id,*data,now))
    elif table == "name":
        cur.execute("INSERT INTO name_record(user_id,type,desc,result,create_time) VALUES(?,?,?,?,?)",(user_id,*data,now))
    elif table == "art":
        cur.execute("INSERT INTO art_record(user_id,style,scene,content,create_time) VALUES(?,?,?,?,?)",(user_id,*data,now))
    elif table == "chat":
        cur.execute("INSERT INTO chat_record(user_id,ask,reply,create_time) VALUES(?,?,?,?)",(user_id,*data,now))
    conn.commit()
    conn.close()

def search_sql(table, key="", user_id=None):
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    if table == "book":
        cur.execute("select * from book_record where user_id=? and book_name like ?",(user_id,f'%{key}%'))
    elif table == "name":
        cur.execute("select * from name_record where user_id=? and desc like ?",(user_id,f'%{key}%'))
    elif table == "art":
        cur.execute("select * from art_record where user_id=? and scene like ?",(user_id,f'%{key}%'))
    elif table == "chat":
        cur.execute("select * from chat_record where user_id=? and ask like ?",(user_id,f'%{key}%'))
    res = cur.fetchall()
    conn.close()
    return res

def del_sql(table, rid, user_id):
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    if table == "book":cur.execute("delete from book_record where id=? and user_id=?",(rid,user_id))
    elif table == "name":cur.execute("delete from name_record where id=? and user_id=?",(rid,user_id))
    elif table == "art":cur.execute("delete from art_record where id=? and user_id=?",(rid,user_id))
    elif table == "chat":cur.execute("delete from chat_record where id=? and user_id=?",(rid,user_id))
    conn.commit()
    conn.close()

# ====================== 初始化数据库 ======================
init_db()
upgrade_old_db()

# ====================== AI配置 ======================
try:
    API_KEY = st.secrets["API_KEY"]
except:
    API_KEY = "4279ab216a1e4c8282b51f541aff703e.HJdsPUVWqGbMD7t0"
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
MODEL_NAME = "glm-4-flash"
from openai import OpenAI
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
SYSTEM_PROMPT = """你是「小政」，风趣随和、接地气，日常聊天自然不生硬，无AI机械话术；书摘通俗口语、起名简约有寓意、朋友圈文案贴合风格。"""

# ====================== 页面CSS（书香风格） ======================
st.set_page_config(page_title="小政AI助手",page_icon="📜",layout="centered",initial_sidebar_state="collapsed")
st.markdown("""
<style>
*{font-family:"Microsoft Yahei",SimSun,serif;}
#MainMenu,footer,header,.stDeployButton,[data-testid="stToolbar"]{display:none !important;visibility:hidden;height:0;}
.stApp{background:linear-gradient(135deg,#f8f2e4 0%,#f0e6d2 50%,#e9dcc3 100%);background-attachment:fixed;}
.func-card{background:rgba(255,253,246,0.92);border:1px solid #d4c2a8;border-radius:12px;padding:10px;box-shadow:0 3px 12px rgba(120,95,65,0.18);}
.stButton>button{border-radius:10px;height:42px;}
</style>
""",unsafe_allow_html=True)

# ====================== Session初始化 ======================
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
#弹窗开关
if "open_login_modal" not in st.session_state:
    st.session_state.open_login_modal = True

# ====================== 弹窗登录组件 ======================
if st.session_state.open_login_modal and st.session_state.user_id is None:
    with st.modal("📜 用户登录", is_open=True):
        tab1,tab2,tab3 = st.tabs(["登录","注册","忘记密码"])
        #登录
        with tab1:
            un = st.text_input("用户名")
            pw = st.text_input("密码",type="password")
            if st.button("登录",type="primary"):
                uinfo = get_user_by_username(un)
                if uinfo and check_hash(pw,uinfo[2]):
                    st.session_state.user_id = uinfo[0]
                    st.session_state.username = uinfo[1]
                    st.session_state.is_admin = True if un == ADMIN_NAME else False
                    st.session_state.open_login_modal = False
                    st.rerun()
                else:
                    st.error("账号或密码错误")
        #注册（密保用于找回密码）
        with tab2:
            reg_name = st.text_input("设置用户名")
            reg_pwd = st.text_input("设置密码",type="password")
            q = st.text_input("密保问题（例如：我的母校？）")
            a = st.text_input("密保答案")
            if st.button("完成注册",type="primary"):
                if get_user_by_username(reg_name):
                    st.warning("用户名已存在")
                else:
                    create_user(reg_name,reg_pwd,q,a)
                    st.success("注册成功！前往登录")
        #忘记密码：密保重置
        with tab3:
            find_name = st.text_input("需要找回的用户名")
            if find_name:
                u = get_user_by_username(find_name)
                if u is None:
                    st.warning("用户不存在")
                else:
                    st.info(f"密保问题：{u[3]}")
                    ans_input = st.text_input("输入密保答案")
                    new_p = st.text_input("输入新密码",type="password")
                    if st.button("确认重置密码",type="primary"):
                        if check_hash(ans_input,u[4]):
                            reset_user_pwd(find_name,new_p)
                            st.success("密码重置成功！")
                        else:
                            st.error("密保答案错误")

# ====================== 顶部导航栏（用户名+登出+管理员入口） ======================
col_top1,col_top2,col_top3 = st.columns([3,1,1])
with col_top1:
    st.markdown(f"### 📜 小政 AI 助手｜欢迎：{st.session_state.username}")
with col_top2:
    if st.session_state.is_admin:
        if st.button("🔧管理员后台"):
            st.session_state.page = "admin"
with col_top3:
    if st.button("🚪登出"):
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.is_admin = False
        st.session_state.open_login_modal = True
        if "page" in st.session_state:
            del st.session_state.page
        st.rerun()

# ====================== 管理员后台页面 ======================
if "page" in st.session_state and st.session_state.page == "admin" and st.session_state.is_admin:
    st.markdown('<div class="func-card"><h3>🔧管理员后台｜全用户数据管理</h3></div>',unsafe_allow_html=True)
    all_user = admin_get_all_user()
    uid_sel = st.selectbox("选择用户查看数据",options=[f"{u[0]}｜{u[1]}｜注册时间{u[2]}" for u in all_user])
    sel_uid = int(uid_sel.split("｜")[0])
    bk,nm,art,chat = admin_get_user_all_data(sel_uid)
    t1,t2,t3,t4 = st.tabs(["书籍存档","起名存档","文案存档","聊天记录"])
    with t1:
        for i in bk:st.write(f"{i[5]}｜{i[2]}《{i[3]}》\n{i[4]}")
    with t2:
        for i in nm:st.write(f"{i[5]}｜{i[2]}｜需求{i[3]}\n{i[4]}")
    with t3:
        for i in art:st.write(f"{i[5]}｜{i[2]}｜{i[3]}\n{i[4]}")
    with t4:
        for i in chat:st.write(f"{i[4]}\n用户:{i[2]}\n助手:{i[3]}")
    if st.button("返回首页"):
        del st.session_state.page
        st.rerun()
else:
    #功能导航
    nav = ["💬对话","📖书摘","🏷️起名","📸朋友圈文案","📂我的存档"]
    nav_col = st.columns(len(nav))
    if "current_func" not in st.session_state:
        st.session_state.current_func = nav[0]
    for idx,n in enumerate(nav):
        with nav_col[idx]:
            if st.button(n,use_container_width=True,type="primary" if st.session_state.current_func==n else "secondary"):
                st.session_state.current_func = n
                st.rerun()
    func = st.session_state.current_func
    uid = st.session_state.user_id

    #1对话
    if func == "💬对话":
        if "chat_history" not in st.session_state:st.session_state.chat_history=[]
        for item in st.session_state.chat_history:
            with st.chat_message(item["role"]):st.markdown(item["content"])
            prompt = st.chat_input("来，随便聊～")
            if prompt:
                st.session_state.chat_history.append({"role":"user","content":prompt})
                with st.chat_message("user"):st.markdown(prompt)
                msg = [{"role":"system","content":SYSTEM_PROMPT}] + st.session_state.chat_history
                res = client.chat.completions.create(model=MODEL_NAME,messages=msg)
                ans = res.choices[0].message.content
                st.session_state.chat_history.append({"role":"assistant","content":ans})
                with st.chat_message("assistant"):st.markdown(ans)
                add_sql("chat",[prompt,ans],uid)
    #2书摘
    elif func == "📖书摘":
        st.markdown('<div class="func-card"><h3>📖书籍介绍&同类推荐</h3></div>',unsafe_allow_html=True)
        bname = st.text_input("书名")
        bauthor = st.text_input("作者(选填)")
        if st.button("生成书摘",type="primary") and bname:
            ask = f"详细介绍《{bname}》{bauthor}，梗概、亮点、适配人群+同类推荐，语言通俗生活化"
            res = client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":ask}])
            ans = res.choices[0].message.content
            st.markdown(ans)
            add_sql("book",[bname,bauthor,ans],uid)
    #3起名
    elif func == "🏷️起名":
        st.markdown('<div class="func-card"><h3>🏷️文艺起名</h3></div>',unsafe_allow_html=True)
        tp = st.selectbox("起名类型",["品牌店铺","宠物名字","网名笔名","小说角色"])
        desc = st.text_input("起名要求/风格")
        num = st.slider("生成数量",3,10,5)
        if st.button("生成名字",type="primary") and desc:
            ask = f"生成{num}个{tp}名称，需求：{desc}，附带释义，文风书香自然"
            ans = client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":ask}]).choices[0].message.content
            st.markdown(ans)
            add_sql("name",[tp,desc,ans],uid)
    #4朋友圈文案
    elif func == "📸朋友圈文案":
        st.markdown('<div class="func-card"><h3>📸朋友圈文案生成</h3></div>',unsafe_allow_html=True)
        sty = st.selectbox("文案风格",["日常随性","文艺走心","幽默搞笑","简约短句","氛围感"])
        scene = st.text_input("场景描述")
        if st.button("生成文案",type="primary") and scene:
            ask = f"场景{scene}，风格{sty}，多条长短搭配朋友圈文案"
            ans = client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":ask}]).choices[0].message.content
            st.markdown(ans)
            add_sql("art",[sty,scene,ans],uid)
    #5我的存档
    elif func == "📂我的存档":
        st.markdown('<div class="func-card"><h3>📂个人内容存档</h3></div>',unsafe_allow_html=True)
        t1,t2,t3,t4 = st.tabs(["书籍存档","起名存档","文案存档","对话存档"])
        with t1:
            kw = st.text_input("书名检索")
            data = search_sql("book",kw,uid)
            for row in data:
                st.write(f"📅{row[5]}｜{row[2]}【{row[3]}】")
                st.text(row[4])
                if st.button("删除",key=f'b{row[0]}'):del_sql("book",row[0],uid);st.rerun()
        with t2:
            kw = st.text_input("需求检索")
            data = search_sql("name",kw,uid)
            for row in data:
                st.write(f"📅{row[5]}｜{row[2]}｜{row[3]}")
                st.text(row[4])
                if st.button("删除",key=f'n{row[0]}'):del_sql("name",row[0],uid);st.rerun()
        with t3:
            kw = st.text_input("场景检索")
            data = search_sql("art",kw,uid)
            for row in data:
                st.write(f"📅{row[5]}｜{row[2]}｜{row[3]}")
                st.text(row[4])
                if st.button("删除",key=f'a{row[0]}'):del_sql("art",row[0],uid);st.rerun()
        with t4:
            kw = st.text_input("提问检索")
            data = search_sql("chat",kw,uid)
            for row in data:
                st.write(f"📅{row[4]} 用户：{row[2]}")
                st.text(f"助手：{row[3]}")
                if st.button("删除",key=f'c{row[0]}'):del_sql("chat",row[0],uid);st.rerun()
