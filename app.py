"""小政AI｜GLM-4.6V｜深浅主题(浅绿/书香深色)｜管理员删用户｜起名智能｜文案违禁过滤｜普通用户隐藏GitHub相关、隐藏存档"""
import streamlit as st
from openai import OpenAI
from datetime import datetime
import sqlite3

# ==========全局常量只初始化一次==========
SYSTEM_PROMPT = """你是「小政」，风趣随和、接地气，日常聊天自然不生硬。
⚠️【必须严格遵守】所有输出**严禁出现任何违法/违规/敏感词汇**：
1. 绝对禁止：最、第一、唯一、顶级、国家级、世界级、极致、完美、100%、纯天然、永久、万能、特效、秒杀、万人疯抢、国家专供、免检、防癌、抗癌等广告法违禁词；
2. 不得使用虚假夸大、诱导欺诈、权威背书、医疗保证、色情迷信暴力内容；
3. 遇到极限词需求，自动替换为安全表达：如“最好”→“优选”、“第一”→“领先”、“顶级”→“高端”；
4. 文案需合规、真实、得体，规避所有平台敏感词，不谐音、不变体、不绕弯。
书摘通俗口语、起名简约有寓意、朋友圈文案贴合风格，全程合规。"""
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
MODEL_NAME = "glm-4.6v"

# 违禁词过滤配置
BANNED_WORDS = {
    "最", "第一", "唯一", "顶级", "国家级", "世界级", "极致", "极佳", "完美",
    "NO.1", "TOP1", "全网第一", "销量第一", "独一无二", "仅此一次", "最后一波",
    "100%", "纯天然", "永久", "万能", "特效", "史无前例", "前无古人", "祖传",
    "秒杀", "万人疯抢", "全民免单", "再不抢就没", "点击领奖", "恭喜获奖",
    "国家专供", "免检", "防癌", "抗癌", "根治", "无副作用"
}
REPLACE_MAP = {
    "最好": "优选",
    "第一": "领先",
    "唯一": "专属",
    "顶级": "高端",
    "国家级": "高品质",
    "100%": "高纯度",
    "纯天然": "天然成分",
    "秒杀": "限时优惠",
    "万人疯抢": "人气热销"
}

def filter_banned_words(text: str) -> str:
    for bad, good in REPLACE_MAP.items():
        text = text.replace(bad, good)
    for word in BANNED_WORDS:
        if word in text:
            text = text.replace(word, "***")
    return text

# 单例标记：数据库只初始化1次
if "db_inited" not in st.session_state:
    st.session_state.db_inited = False

# ==========数据库函数==========
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
    cur.execute("select id,username,role,create_time from user_info")
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

# 仅首次启动初始化数据库
if not st.session_state.db_inited:
    init_db()
    st.session_state.db_inited = True

# AI客户端只实例化一次
if "ai_client" not in st.session_state:
    try:
        API_KEY = st.secrets["API_KEY"]
    except:
        API_KEY = "4279ab216a1e4c8282b51f541aff703e.HJdsPUVWqGbMD7t0"
    st.session_state.ai_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
client = st.session_state.ai_client

#页面配置
st.set_page_config(page_title="小政",page_icon="📜",layout="centered",initial_sidebar_state="collapsed")

#CSS只渲染一次
if "css_done" not in st.session_state:
    st.markdown("""
    <style>
    *{font-family:"Microsoft Yahei","SimSun";}
    #MainMenu,footer,header,[data-testid="stToolbar"]{display:none !important;height:0;visibility:hidden;}
    /*浅色清新绿色 */
    @media (prefers-color-scheme: light){
    .stApp{background:linear-gradient(135deg,#F1F8E9 0%,#E8F5E9 50%,#DCEDC8 100%) !important;background-attachment:fixed;color:#263238;}
    .func-card{background:rgba(255,255,255,0.92);border:1px solid #C8E6C9;border-radius:12px;padding:12px;box-shadow:0 3px 12px rgba(80,160,80,0.15);margin:5px 0;}
    div[data-testid="stChatMessage"]{background:rgba(255,255,255,0.9);border:1px solid #C8E6C9;border-radius:10px;}
    .stChatInput{background:rgba(255,255,255,0.95) !important;border-top:1px solid #C8E6C9;}
    .stChatInput>div>div>div{background:#F1F8E9 !important;border:1px solid #C8E6C9;border-radius:20px;color:#263238;}
    .stTextInput input,.stTextArea textarea,.stSelectbox>div>div{background:rgba(255,255,255,0.9);border:1px solid #C8E6C9;border-radius:8px;color:#263238;}
    }
    /*深色书香棕 */
    @media (prefers-color-scheme: dark){
    .stApp{background:linear-gradient(135deg,#2c261e 0%,#252018 50%,#1e1a14 100%) !important;background-attachment:fixed;color:#e8dfcc;}
    .func-card{background:rgba(45,39,30,0.92);border:1px solid #6b5c4b;border-radius:12px;padding:12px;box-shadow:0 3px 12px rgba(0,0,0,0.35);margin:5px 0;}
    div[data-testid="stChatMessage"]{background:rgba(45,39,30,0.9);border:1px solid #6b5c4b;border-radius:10px;}
    .stChatInput{background:rgba(45,39,30,0.95) !important;border-top:1px solid #6b5c4b;}
    .stChatInput>div>div>div{background:#332c22 !important;border:1px solid #6b5c4b;border-radius:20px;color:#e8dfcc;}
    .stTextInput input,.stTextArea textarea,.stSelectbox>div>div{background:rgba(45,39,30,0.9);border:1px solid #6b5c4b;border-radius:8px;color:#e8dfcc;}
    }
    .stButton>button{height:44px;border-radius:10px;font-size:15px;}
    .stButton>button[kind="primary"]{background:#2E7D32;color:#fff;border:none;}
    .stButton>button[kind="primary"]:hover{background:#27672b;transform:translateY(-2px);}
    .stButton>button[kind="secondary"]{border:1px solid #b8a48c;background:transparent;}
    .stButton>button[kind="secondary"]:hover{border-color:#82674b;color:#82674b;}
    </style>
    """,unsafe_allow_html=True)
    st.session_state.css_done = True

#统一初始化会话
init_keys = ["login","user_name","user_role","pop_login","pop_reg","pop_reset","pop_adduser","show_userlist","current_func","chat_history"]
for k in init_keys:
    if k not in st.session_state:
        if k == "login": st.session_state[k]=False
        elif k in ("user_name","user_role","current_func"): st.session_state[k]=""
        elif k=="chat_history": st.session_state[k]=[]
        else: st.session_state[k]=False

#====================未登录拦截：启动必须先登录====================
if not st.session_state.login:
    st.markdown("# 📜 小政AI助手")
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

#====================已登录进入系统====================
user_bar=st.columns([3,1,1,1,1,1,1])
user_bar[0].write(f"👤{st.session_state.user_name}【{st.session_state.user_role}】")
with user_bar[1]:
    if st.button("🔑改密",type="secondary"):st.session_state.pop_reset=True
if st.session_state.user_role=="manager":
    with user_bar[2]:
        if st.button("➕新建账号",type="secondary"):st.session_state.pop_adduser=True
    with user_bar[3]:
        if st.button("👥用户列表",type="secondary"):
            st.session_state.show_userlist=True
    # 仅管理员展示Github相关入口
    with user_bar[5]:
        st.link_button("Github项目","https://github.com/")
with user_bar[4]:
    if st.button("🚪退出",type="secondary"):
        st.session_state.login=False
        st.session_state.user_name=""
        st.session_state.user_role=""
        st.session_state.show_userlist=False
        st.rerun()

# ==========管理员用户列表（删除用户）==========
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

#导航菜单
st.markdown("### 📜 小政 AI 助手")
base_menu=["💬 对话","📖 书摘","🏷️ 起名","📸 朋友圈文案"]
# 管理员多出存档菜单，普通用户隐藏存档
if st.session_state.user_role=="manager":
    nav_items=base_menu+["📂 我的存档"]
else:
    nav_items=base_menu

cols=st.columns(len(nav_items))
if st.session_state.current_func not in nav_items:
    st.session_state.current_func=nav_items[0]
for idx,name in enumerate(nav_items):
    with cols[idx]:
        if st.button(name,use_container_width=True,type="primary" if st.session_state.current_func==name else "secondary"):
            st.session_state.current_func=name
            st.rerun()
func=st.session_state.current_func

#对话
if func=="💬 对话":
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

#书摘
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

#智能起名
elif func=="🏷️ 起名":
    st.markdown('<div class="func-card"><h3>🏷️ AI起名</h3></div>',unsafe_allow_html=True)
    typ=st.selectbox("类型",["品牌店铺","宠物名字","网名笔名","小说角色"])
    desc=st.text_input("风格描述（如：古风雅致、简约大气、可爱日系、国风书香）")
    num=st.slider("数量",3,10,5)
    if st.button("✨生成名字",type="primary") and desc:
        with st.spinner("生成中..."):
            ask_name = f"""根据需求智能起名：类型：{typ}，风格要求：{desc}。
1、每个名字附带详细释义、寓意、出处；
2、避开贬义谐音、生僻冷门字；
3、排版工整，分点罗列；
4、一共{num}个。"""
            rep=client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":ask_name}])
            txt=rep.choices[0].message.content
            st.markdown(txt)
            add_sql("name",[typ,desc,txt])

#朋友圈文案+违禁过滤
elif func=="📸 朋友圈文案":
    st.markdown('<div class="func-card"><h3>📸 朋友圈文案生成</h3></div>',unsafe_allow_html=True)
    sty=st.selectbox("风格",["日常随性","文艺走心","幽默搞笑","简约短句","氛围感"])
    scene=st.text_input("场景描述")
    if st.button("✨生成文案",type="primary") and scene:
        with st.spinner("生成中..."):
            ask_copy = f"{scene}，写{sty}朋友圈文案，文案遵守广告法规，禁用极限夸大违规词汇"
            rep=client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":ask_copy}])
            txt=rep.choices[0].message.content
            txt = filter_banned_words(txt)
            st.markdown(txt)
            add_sql("art",[sty,scene,txt])

#存档仅管理员可见
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
