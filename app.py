"""小政AI助手 - 豆包布局 + 古风竹子背景元素
保留全部原有功能、数据库、权限、双主题
新增：全屏竹子背景、竹叶纹理、竹纹装饰、古风配色
"""
import streamlit as st
from openai import OpenAI
from datetime import datetime
import sqlite3

# ========== 全局常量 & 系统提示词 ==========
SYSTEM_PROMPT = """你是「小政」，风趣随和、接地气，日常聊天自然不生硬，无AI机械话术；
硬性知识规则：
1. 通用常识正常通俗作答，细分专业领域、文史、学科、行业问题必须严谨准确，不确定的知识点主动说明无法精准作答，不编造答案；
2. 书摘内容客观贴合原著史实，起名简约有寓意、朋友圈文案贴合风格。"""
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
MODEL_NAME = "glm-4-flash"

# 单例标记：数据库只初始化1次
if "db_inited" not in st.session_state:
    st.session_state.db_inited = False

# ========== 数据库函数（无修改） ==========
def init_db():
    conn = sqlite3.connect("user_data.db", check_same_thread=False)
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
    conn = sqlite3.connect("user_data.db", check_same_thread=False)
    cur = conn.cursor()
    sql_map = {
        "book":"INSERT INTO book_record(book_name,author,content,create_time) VALUES(?,?,?,?)",
        "name":"INSERT INTO name_record(type,desc,result,create_time) VALUES(?,?,?,?)",
        "art":"INSERT INTO art_record(style,scene,content,create_time) VALUES(?,?,?,?)",
        "chat":"INSERT INTO chat_record(ask,reply,create_time) VALUES(?,?,?)"
    }
    cur.execute(sql_map[table], (*data, now))
    conn.commit()
    conn.close()

def search_sql(table, key=""):
    conn = sqlite3.connect("user_data.db", check_same_thread=False)
    cur = conn.cursor()
    sql_map = {
        "book":"select * from book_record where book_name like ?",
        "name":"select * from name_record where desc like ?",
        "art":"select * from art_record where scene like ?",
        "chat":"select * from chat_record where ask like ?"
    }
    cur.execute(sql_map[table], (f'%{key}%',))
    res = cur.fetchall()
    conn.close()
    return res

def del_sql(table, rid):
    conn = sqlite3.connect("user_data.db", check_same_thread=False)
    cur = conn.cursor()
    sql_map = {
        "book":"delete from book_record where id=?",
        "name":"delete from name_record where id=?",
        "art":"delete from art_record where id=?",
        "chat":"delete from chat_record where id=?"
    }
    cur.execute(sql_map[table], (rid,))
    conn.commit()
    conn.close()

def check_user(uname,pwd):
    conn=sqlite3.connect("user_data.db", check_same_thread=False)
    cur=conn.cursor()
    cur.execute("select role from user_info where username=? and password=?",(uname,pwd))
    res=cur.fetchone()
    conn.close()
    return res

def reset_pwd(uname,new_pwd):
    conn=sqlite3.connect("user_data.db", check_same_thread=False)
    cur=conn.cursor()
    cur.execute("update user_info set password=? where username=?",(new_pwd,uname))
    conn.commit()
    conn.close()

def add_new_user(uname,pwd,role):
    now=datetime.now().strftime("%Y-%m-%d %H:%M")
    conn=sqlite3.connect("user_data.db", check_same_thread=False)
    cur=conn.cursor()
    try:
        cur.execute("INSERT INTO user_info(username,password,role,create_time) VALUES(?,?,?,?)",(uname,pwd,role,now))
        conn.commit()
        return True
    except:
        return False
    conn.close()

def get_all_user():
    conn=sqlite3.connect("user_data.db", check_same_thread=False)
    cur=conn.cursor()
    cur.execute("select * from user_info")
    data=cur.fetchall()
    conn.close()
    return data

def delete_user_by_id(uid,uname):
    if uname == "admin":
        return False,"超级管理员admin禁止删除"
    conn=sqlite3.connect("user_data.db", check_same_thread=False)
    cur=conn.cursor()
    cur.execute("DELETE FROM user_info WHERE id=?",(uid,))
    conn.commit()
    conn.close()
    return True,"删除成功"

# 初始化数据库
if not st.session_state.db_inited:
    init_db()
    st.session_state.db_inited = True

# AI客户端初始化
if "ai_client" not in st.session_state:
    try:
        API_KEY = st.secrets["API_KEY"]
    except:
        API_KEY = "4279ab216a1e4c8282b51f541aff703e.HJdsPUVWqGbMD7t0"
    st.session_state.ai_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
client = st.session_state.ai_client

# ========== 页面全局配置 + 竹子古风CSS（核心新增部分） ==========
st.set_page_config(page_title="小政AI助手",page_icon="🎋",layout="wide",initial_sidebar_state="expanded")

if "css_done" not in st.session_state:
    st.markdown("""
    <style>
    /* 全局基础样式 */
    *{font-family:"Microsoft Yahei", "KaiTi", sans-serif !important; margin:0; padding:0;}
    #MainMenu, footer, header, [data-testid="stToolbar"] {display:none !important; height:0;}

    /* ========== 浅色模式：竹子背景 + 书香绿调 ========== */
    .stApp {
        /* 竹子纹理背景（半透明，不遮挡文字） */
        background-image: url('https://img0.baidu.com/it/u=1976256132,2878796139&fm=253&fmt=auto&app=138&f=JPEG?w=800&h=500');
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
        background-color: #f2f8f0;
        background-blend-mode: overlay;
    }

    /* 侧边栏 - 竹纹古风样式 */
    [data-testid="stSidebar"] {
        min-width:220px !important; max-width:240px !important;
        padding:20px 15px;
        background-color: rgba(235, 245, 230, 0.92) !important;
        border-right: 2px solid #a8c9a0;
    }
    [data-testid="stSidebar"] .block-container {padding:10px 0;}
    [data-testid="stSidebar"] .stButton button {
        width:100% !important; text-align:left; padding:10px 14px;
        border-radius:8px; border:1px solid #b8d4af;
        margin:4px 0; font-size:15px; background:#ffffff80;
    }
    [data-testid="stSidebar"] .stButton button:hover {background:#d8e9d0;}
    [data-testid="stSidebar"] .stButton button[kind="primary"] {background:#8fb882; color:#ffffff; border-color:#7ca56f;}

    /* 功能卡片 - 竹色边框 */
    .func-card {
        background:rgba(255,255,255,0.85);
        border:1px solid #a8c9a0;
        border-radius:12px; padding:20px; margin:15px 0;
        box-shadow: 0 2px 8px rgba(120, 165, 110, 0.15);
    }

    /* 输入框、下拉框 竹系配色 */
    .stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
        border-radius:8px; border:1px solid #b8d4af;
        padding:8px 12px; background:#ffffff90;
    }

    /* ========== 聊天气泡（保留豆包样式 + 适配古风） ========== */
    .stChatMessage[data-testid="assistant"] {justify-content:flex-start; margin:8px 0;}
    .stChatMessage[data-testid="assistant"] .stMarkdown {
        background:rgba(247, 248, 250, 0.92); color:#1d2129;
        border-radius:16px 16px 16px 4px;
        padding:12px 16px; max-width:85%; line-height:1.6;
        border:1px solid #e0e9dc;
    }
    .stChatMessage[data-testid="user"] {justify-content:flex-end; margin:8px 0;}
    .stChatMessage[data-testid="user"] .stMarkdown {
        background:#6b9b5f; color:#ffffff;
        border-radius:16px 16px 4px 16px;
        padding:12px 16px; max-width:85%; line-height:1.6;
    }

    /* 底部聊天输入框 固定位置+竹风样式 */
    .stChatInput {position:fixed; bottom:20px; left:250px; right:30px; z-index:999;}
    .stChatInput > div > div > div {
        border-radius:24px; padding:6px 16px;
        border:1px solid #a8c9a0; background:#ffffff95;
    }

    /* ========== 深色模式：深色竹影风格 ========== */
    @media (prefers-color-scheme: dark){
        .stApp {
            background-image: url('https://img0.baidu.com/it/u=1976256132,2878796139&fm=253&fmt=auto&app=138&f=JPEG?w=800&h=500');
            background-color: #1a2019;
            background-blend-mode: multiply;
        }
        [data-testid="stSidebar"] {background-color: rgba(26, 32, 25, 0.94) !important; border-right:2px solid #4a5c46;}
        [data-testid="stSidebar"] .stButton button {background:#2c362b80; border-color:#4a5c46; color:#d0dccb;}
        [data-testid="stSidebar"] .stButton button:hover {background:#3a4738;}
        [data-testid="stSidebar"] .stButton button[kind="primary"] {background:#54704c; color:#e8f0e3;}
        .func-card {background:rgba(30, 36, 29, 0.88); border:1px solid #4a5c46;}
        .stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
            border:1px solid #4a5c46; background:#2c362b90; color:#d0dccb;
        }
        .stChatMessage[data-testid="assistant"] .stMarkdown {background:#2c362b; color:#e8f0e3; border-color:#4a5c46;}
        .stChatMessage[data-testid="user"] .stMarkdown {background:#54704c; color:#ffffff;}
        .stChatInput > div > div > div {background:#2c362b95; border:1px solid #4a5c46;}
    }
    </style>
    """,unsafe_allow_html=True)
    st.session_state.css_done = True

# ========== 初始化会话状态 ==========
init_keys = ["login","user_name","user_role","pop_login","pop_reg","pop_reset","pop_adduser","show_userlist","current_func","chat_history"]
for k in init_keys:
    if k not in st.session_state:
        if k == "login": st.session_state[k]=False
        elif k in ("user_name","user_role","current_func"): st.session_state[k]=""
        elif k=="chat_history": st.session_state[k]=[]
        else: st.session_state[k]=False

# ========== 未登录页面 ==========
if not st.session_state.login:
    st.title("🎋 小政AI助手")
    st.warning("⚠️ 请先登录账号后使用全部功能，暂无账号可点击注册！")
    c1,c2=st.columns(2)
    with c1:
        if st.button("🔐 去登录",type="primary",use_container_width=True):
            st.session_state.pop_login=True
    with c2:
        if st.button("📝 新用户注册",type="secondary",use_container_width=True):
            st.session_state.pop_reg=True

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
    st.stop()

# ========== 已登录：左侧侧边栏导航 ==========
with st.sidebar:
    st.markdown(f"### 🎋 {st.session_state.user_name}")
    st.caption(f"权限：{st.session_state.user_role}")
    st.divider()

    base_menu=["💬 对话","📖 书摘","🏷️ 起名","📸 朋友圈文案"]
    if st.session_state.user_role=="manager":
        nav_items=base_menu+["📂 我的存档"]
    else:
        nav_items=base_menu

    if st.session_state.current_func not in nav_items:
        st.session_state.current_func=nav_items[0]
    for name in nav_items:
        active = (st.session_state.current_func == name)
        if st.button(name, use_container_width=True, type="primary" if active else "secondary"):
            st.session_state.current_func=name
            st.rerun()

    st.divider()
    if st.button("🔑 修改密码",use_container_width=True):
        st.session_state.pop_reset=True
    if st.session_state.user_role=="manager":
        if st.button("➕ 新建账号",use_container_width=True):
            st.session_state.pop_adduser=True
        if st.button("👥 用户列表",use_container_width=True):
            st.session_state.show_userlist=True
    if st.button("🚪 退出登录",use_container_width=True):
        st.session_state.login=False
        st.session_state.user_name=""
        st.session_state.user_role=""
        st.session_state.show_userlist=False
        st.rerun()

# ========== 右侧主内容区 ==========
func=st.session_state.current_func

# 1. 对话模块
if func=="💬 对话":
    st.subheader("💬 智能对话")
    for i in st.session_state.chat_history:
        with st.chat_message(i["role"]):
            st.markdown(i["content"])
    msg=st.chat_input("请输入问题...")
    if msg:
        st.session_state.chat_history.append({"role":"user","content":msg})
        with st.chat_message("user"):
            st.markdown(msg)
        res=client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT}]+st.session_state.chat_history)
        ans=res.choices[0].message.content
        st.session_state.chat_history.append({"role":"assistant","content":ans})
        with st.chat_message("assistant"):
            st.markdown(ans)
        add_sql("chat",[msg,ans])

# 2. 书摘模块
elif func=="📖 书摘":
    st.markdown('<div class="func-card"><h3>📖 书籍介绍 & 同类推荐</h3></div>',unsafe_allow_html=True)
    book_name = st.text_input("书名")
    author = st.text_input("作者（选填）")
    if st.button("📚 获取介绍", type="primary") and book_name:
        with st.spinner("整理内容中..."):
            ask = f"详细介绍《{book_name}》作者{author}，包含基础信息、梗概、亮点、适合人群，顺带推荐同类好书，语言生活化，内容严谨核实。"
            ans = client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":ask}]).choices[0].message.content
            st.markdown(ans)
            add_sql("book", [book_name, author, ans])

# 3. 起名模块
elif func=="🏷️ 起名":
    st.markdown('<div class="func-card"><h3>🏷️ AI起名</h3></div>',unsafe_allow_html=True)
    typ=st.selectbox("类型",["品牌店铺","宠物名字","网名笔名","小说角色"])
    style=st.selectbox("风格",["简约清雅","古风诗意","温润治愈","清冷高级","大气稳重","可爱灵动"])
    req=st.text_input("补充要求（字数、包含字、避讳字、行业、寓意方向）")
    num=st.slider("数量",3,10,5)
    if st.button("✨生成名字",type="primary"):
        with st.spinner("生成中..."):
            prompt=f"为{typ}起{num}个名字，风格：{style}，补充要求：{req}，名字贴合品类、好听有寓意，每个附带简短释义，无多余开场白。"
            rep=client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}])
            txt=rep.choices[0].message.content
            st.markdown(txt)
            add_sql("name",[f"{typ}|{style}",req,txt])

# 4. 朋友圈文案
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

# 5. 存档（仅管理员）
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

# ========== 弹窗功能：改密、新建账号、用户列表 ==========
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

if st.session_state.show_userlist and st.session_state.user_role=="manager":
    with st.expander("👥全部用户管理列表 | 可删除非admin账号",expanded=True):
        alluser=get_all_user()
        st.markdown("|ID|用户名|权限|注册时间|操作|")
        st.markdown("|----|----|----|----|----|")
        for item in alluser:
            uid,uname,urole,utime=item
            col1,col2=st.columns([4,1])
            with col1:
                st.markdown(f"{uid}｜{uname}｜{urole}｜{utime}")
            with col2:
                if uname != "admin":
                    if st.button(f"删除{uname}",key=f"del_{uid}"):
                        flag,msg=delete_user_by_id(uid,uname)
                        if flag:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.warning(msg)
                else:
                    st.text("不可删")
        if st.button("关闭列表"):
            st.session_state.show_userlist=False
            st.rerun()
