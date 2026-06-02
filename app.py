"""
小政AI｜1.启动先登录 2.管理员用户列表 3.恢复原版书摘（自带同类推荐）
默认管理员：admin / 123456
"""
import streamlit as st
from openai import OpenAI
from datetime import datetime
import sqlite3

# ==========数据库函数==========
def init_db():
    conn = sqlite3.connect("user_data.db")
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS book_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_name TEXT,author TEXT,content TEXT,create_time TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS name_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,desc TEXT,result TEXT,create_time TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS art_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        style TEXT,scene TEXT,content TEXT,create_time TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS chat_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ask TEXT,reply TEXT,create_time TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS user_info(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,password TEXT,role TEXT,create_time TEXT)''')
    cur.execute("INSERT OR IGNORE INTO user_info(username,password,role,create_time) VALUES(?,?,?,?)",
                ("admin","123456","manager",datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

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

#账号相关
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
        return True
    except:
        return False
    conn.close()

#管理员查看全部用户
def get_all_user():
    conn=sqlite3.connect("user_data.db")
    cur=conn.cursor()
    cur.execute("select id,username,role,create_time from user_info")
    data=cur.fetchall()
    conn.close()
    return data

init_db()

#API
try:
    API_KEY = st.secrets["API_KEY"]
except:
    API_KEY = "4279ab216a1e4c8282b51f541aff703e.HJdsPUVWqGbMD7t0"
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
MODEL_NAME = "glm-4-flash"
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

SYSTEM_PROMPT = """你是「小政」，风趣随和、接地气，日常聊天自然不生硬，无AI机械话术；书摘通俗口语、起名简约有寓意、朋友圈文案贴合风格。"""

#页面配置
st.set_page_config(page_title="小政",page_icon="📜",layout="centered",initial_sidebar_state="collapsed")
st.markdown("""
<style>
*{font-family:"Microsoft Yahei","SimSun";}
#MainMenu,footer,header,[data-testid="stToolbar"]{display:none !important;height:0;visibility:hidden;}
.stApp{background:linear-gradient(135deg,#f8f2e4 0%,#f0e6d2 50%,#e9dcc3 100%) !important;background-attachment:fixed;}
.func-card{background:rgba(255,253,246,0.92);border:1px solid #d4c2a8;border-radius:12px;padding:12px;box-shadow:0 3px 12px rgba(120,95,65,0.18);margin:5px 0;}
.stButton>button{height:44px;border-radius:10px;font-size:15px;}
.stButton>button[kind="primary"]{background:#82674b;color:#fff8e8;border:none;}
.stButton>button[kind="secondary"]{border:1px solid #b8a48c;background:transparent;}
</style>
""",unsafe_allow_html=True)

#会话初始化
if "login" not in st.session_state:
    st.session_state.login=False
    st.session_state.user_name=""
    st.session_state.user_role=""
if "pop_login" not in st.session_state:st.session_state.pop_login=False
if "pop_reg" not in st.session_state:st.session_state.pop_reg=False
if "pop_reset" not in st.session_state:st.session_state.pop_reset=False
if "pop_adduser" not in st.session_state:st.session_state.pop_adduser=False
if "show_userlist" not in st.session_state:st.session_state.show_userlist=False

#====================未登录拦截：启动必须先登录====================
if not st.session_state.login:
    st.markdown("# 📜 小政AI助手")
    st.warning("⚠️ 请先登录账号后使用全部功能，暂无账号可点击注册！")
    #登录注册按钮
    c1,c2=st.columns(2)
    with c1:
        if st.button("🔐 去登录",type="primary",use_container_width=True):
            st.session_state.pop_login=True
    with c2:
        if st.button("📝 新用户注册",type="secondary",use_container_width=True):
            st.session_state.pop_reg=True

    #登录弹窗
    if st.session_state.pop_login:
        with st.expander("🔐 用户登录",expanded=True):
            u=st.text_input("账号",key="lu")
            p=st.text_input("密码",type="password",key="lp")
            cc1,cc2=st.columns(2)
            with cc1:
                if st.button("登录",type="primary",key="loginok"):
                    res=check_user(u,p)
                    if res:
                        st.session_state.login=True
                        st.session_state.user_name=u
                        st.session_state.user_role=res[0]
                        st.session_state.pop_login=False
                        st.rerun()
                    else:
                        st.error("账号或密码错误")
            with cc2:
                if st.button("关闭",key="logclose"):
                    st.session_state.pop_login=False
                    st.rerun()
    #注册弹窗
    if st.session_state.pop_reg:
        with st.expander("📝 新用户注册(默认普通用户)",expanded=True):
            ru=st.text_input("用户名",key="ru")
            rp=st.text_input("密码",type="password",key="rp")
            cc1,cc2=st.columns(2)
            with cc1:
                if st.button("完成注册",type="primary",key="regok") and ru and rp:
                    if add_new_user(ru,rp,"user"):
                        st.success("注册成功！前往登录")
                        st.session_state.pop_reg=False
                        st.rerun()
                    else:
                        st.error("用户名已被占用")
            with cc2:
                if st.button("关闭",key="regclose"):
                    st.session_state.pop_reg=False
                    st.rerun()
    st.stop()#未登录终止后续代码

#====================已登录进入系统====================
#顶部按钮栏
user_bar=st.columns([3,1,1,1,1,1,1])
user_bar[0].write(f"👤{st.session_state.user_name}【{st.session_state.user_role}】")
with user_bar[1]:
    if st.button("🔑改密",type="secondary"):st.session_state.pop_reset=True
#管理员：新建账号+查看用户
if st.session_state.user_role=="manager":
    with user_bar[2]:
        if st.button("➕新建账号",type="secondary"):st.session_state.pop_adduser=True
    with user_bar[3]:
        if st.button("👥用户列表",type="secondary"):
            st.session_state.show_userlist=True
else:
    st.session_state.show_userlist=False
with user_bar[4]:
    if st.button("🚪退出",type="secondary"):
        st.session_state.login=False
        st.session_state.user_name=""
        st.session_state.user_role=""
        st.session_state.show_userlist=False
        st.rerun()

#管理员查看用户列表弹窗
if st.session_state.show_userlist and st.session_state.user_role=="manager":
    with st.expander("👥全部用户管理列表",expanded=True):
        alluser=get_all_user()
        st.markdown("|ID|用户名|权限|注册时间|")
        st.markdown("|----|----|----|----|")
        for item in alluser:
            uid,uname,urole,utime=item
            st.markdown(f"|{uid}|{uname}|{urole}|{utime}|")
        if st.button("关闭列表"):
            st.session_state.show_userlist=False
            st.rerun()

#导航菜单
st.markdown("### 📜 小政 AI 助手")
base_menu=["💬 对话","📖 书摘","🏷️ 起名","📸 朋友圈文案"]
if st.session_state.user_role=="manager":
    nav_items=base_menu+["📂 我的存档"]
else:
    nav_items=base_menu

cols=st.columns(len(nav_items))
if "current_func" not in st.session_state:st.session_state.current_func=nav_items[0]
for idx,name in enumerate(nav_items):
    with cols[idx]:
        if st.button(name,use_container_width=True,type="primary" if st.session_state.current_func==name else "secondary"):
            st.session_state.current_func=name
            st.rerun()
func=st.session_state.current_func

# 1.对话
if func=="💬 对话":
    if "chat_history" not in st.session_state:st.session_state.chat_history=[]
    for i in st.session_state.chat_history:
        with st.chat_message(i["role"]):st.markdown(i["content"])
    msg=st.chat_input("来，随便聊～")
    if msg:
        st.session_state.chat_history.append({"role":"user","content":msg})
        with st.chat_message("user"):st.markdown(msg)
        res=client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT}]+st.session_state.chat_history)
        ans=res.choices[0].message.content
        st.session_state.chat_history.append({"role":"assistant","content":ans})
        with st.chat_message("assistant"):st.markdown(ans)
        add_sql("chat",[msg,ans])

# 2.书摘【恢复原版：介绍+同类书籍推荐】
elif func=="📖 书摘":
    st.markdown('<div class="func-card"><h3>📖 书籍介绍 & 同类推荐</h3></div>',unsafe_allow_html=True)
    book_name = st.text_input("书名")
    author = st.text_input("作者（选填）")
    if st.button("📚 获取介绍", type="primary") and book_name:
        with st.spinner("整理内容中..."):
            ask = f"详细介绍《{book_name}》作者{author}，包含基础信息、梗概、亮点、适合人群，顺带推荐同类好书，语言生活化。"
            ans = client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":ask}]).choices[0].message.content
            st.markdown(ans)
            add_sql("book", [book_name, author, ans])

# 3.起名
elif func=="🏷️ 起名":
    st.markdown('<div class="func-card"><h3>🏷️ AI起名</h3></div>',unsafe_allow_html=True)
    typ=st.selectbox("类型",["品牌店铺","宠物名字","网名笔名","小说角色"])
    desc=st.text_input("风格描述")
    num=st.slider("数量",3,10,5)
    if st.button("✨生成名字",type="primary") and desc:
        with st.spinner("生成中..."):
            rep=client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":f"{num}个{typ}名字，{desc}"}])
            txt=rep.choices[0].message.content
            st.markdown(txt)
            add_sql("name",[typ,desc,txt])

# 4.朋友圈文案
elif func=="📸 朋友圈文案":
    st.markdown('<div class="func-card"><h3>📸 朋友圈文案生成</h3></div>',unsafe_allow_html=True)
    sty=st.selectbox("风格",["日常随性","文艺走心","幽默搞笑","简约短句","氛围感"])
    scene=st.text_input("场景描述")
    if st.button("✨生成文案",type="primary") and scene:
        with st.spinner("生成中..."):
            rep=client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":f"{scene}，{sty}文案"}])
            txt=rep.choices[0].message.content
            st.markdown(txt)
            add_sql("art",[sty,scene,txt])

# 5.存档（仅管理员）
elif func=="📂 我的存档":
    if st.session_state.user_role=="manager":
        st.markdown('<div class="func-card"><h3>📂 全量内容存档</h3></div>',unsafe_allow_html=True)
        t1,t2,t3,t4=st.tabs(["书籍","起名","文案","对话"])
        with t1:
            kw=st.text_input("搜索书名")
            for r in search_sql("book",kw):
                st.write(f"📅{r[4]}｜{r[1]} {r[2]}")
                st.text(r[3])
                if st.button("删除",key=f'b{r[0]}'):del_sql("book",r[0]);st.rerun()
        with t2:
            kw=st.text_input("搜索关键词")
            for r in search_sql("name",kw):
                st.write(f"📅{r[4]}｜{r[1]}｜{r[2]}")
                st.text(r[3])
                if st.button("删除",key=f'n{r[0]}'):del_sql("name",r[0]);st.rerun()
        with t3:
            kw=st.text_input("搜索场景")
            for r in search_sql("art",kw):
                st.write(f"📅{r[4]}｜{r[1]}｜{r[2]}")
                st.text(r[3])
                if st.button("删除",key=f'a{r[0]}'):del_sql("art",r[0]);st.rerun()
        with t4:
            kw=st.text_input("搜索提问")
            for r in search_sql("chat",kw):
                st.write(f"📅{r[3]} 用户：{r[1]}")
                st.text(f"AI：{r[2]}")
                if st.button("删除",key=f'c{r[0]}'):del_sql("chat",r[0]);st.rerun()
    else:
        st.warning("仅管理员可查看存档")

# 修改密码弹窗
if st.session_state.pop_reset:
    with st.expander("🔑 修改密码",expanded=True):
        np=st.text_input("新密码",type="password",key="newp")
        cc1,cc2=st.columns(2)
        with cc1:
            if st.button("确认修改",type="primary",key="resetok") and np:
                reset_pwd(st.session_state.user_name,np)
                st.success("修改成功");st.session_state.pop_reset=False;st.rerun()
        with cc2:
            if st.button("取消",key="resetclose"):st.session_state.pop_reset=False;st.rerun()

#管理员新建账号弹窗
if st.session_state.pop_adduser and st.session_state.user_role=="manager":
    with st.expander("➕管理员创建账号",expanded=True):
        au=st.text_input("新建用户名",key="adduser")
        ap=st.text_input("新建密码",type="password",key="addpwd")
        ar=st.selectbox("账号权限",["user普通用户","manager管理员"],key="addrole")
        real_r=ar.replace("普通用户","").replace("管理员","")
        cc1,cc2=st.columns(2)
        with cc1:
            if st.button("创建",type="primary",key="addok") and au and ap:
                if add_new_user(au,ap,real_r):
                    st.success("创建成功");st.session_state.pop_adduser=False;st.rerun()
                else:st.error("用户名重复")
        with cc2:
            if st.button("关闭",key="addclose"):st.session_state.pop_adduser=False;st.rerun()
