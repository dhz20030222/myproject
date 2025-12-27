import os
# 1. 魔法代码：强制使用国内镜像 (防断网)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import psycopg2
from pgvector.psycopg2 import register_vector  # 👈 关键修正1：引入向量工具
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

load_dotenv()


DB_URL = os.getenv("DATABASE_URL")
# 初始化 DeepSeek
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"), 
    base_url="https://api.deepseek.com"
)

print("正在加载搜索模型 (BGE)...")
model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
def ask_deepseek(question_text, file_filter=None):
    """
    question_text: 用户的问题
    file_filter: (可选) 用户指定的文件名。如果不传，则搜索整个知识库。
    """
    # 打印日志看看搜的是全库还是单文件
    range_info = f"《{file_filter}》" if file_filter else "【全库】"
    print(f"\n📢 [逻辑层] 用户提问: {question_text} (范围: {range_info})")
    
    # --- 步骤 A: 搜索数据库 ---
    
    # 1. 向量化 (⚠️ 注意：这里用 get_model() 配合懒加载)
    query_instruction = "为这个句子生成表示以用于检索相关文章："
    question_vector = get_model().encode(query_instruction + question_text).tolist()
    
    try:
        conn = psycopg2.connect(DB_URL)
        register_vector(conn)
        cur = conn.cursor()
        
        # 2. 动态构建 SQL (关键升级！支持按文件名过滤)
        if file_filter:
            # ✅ 情况1: 用户指定了文件，只在这个文件里搜
            sql = """
                SELECT content, source, page_number
                FROM knowledge_base 
                WHERE source = %s 
                ORDER BY embedding <=> %s::vector 
                LIMIT 3
            """
            cur.execute(sql, (file_filter, question_vector))
        else:
            # 🌐 情况2: 没选文件，全库搜索
            sql = """
                SELECT content, source, page_number
                FROM knowledge_base 
                ORDER BY embedding <=> %s::vector 
                LIMIT 3
            """
            cur.execute(sql, (question_vector,))
            
        results = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ 数据库查询出错: {e}")
        return "抱歉，数据库连接出了点问题，请检查后台日志。"
    
    # --- 步骤 B: 组装资料 ---
    db_context = ""
    print(f"👀 数据库检索结果: 找到了 {len(results)} 条资料")
    
    if results:
        for i, row in enumerate(results):
            content = row[0]
            source = row[1]
            page_num = row[2] # 多取一个页码，回答更专业
            
            # 打印摘要方便调试
            print(f"   📄 [资料{i+1}] 来自《{source}》第{page_num}页") 
            db_context += f"--- 资料 {i+1} (来源: {source} 第{page_num}页) ---\n{content}\n\n"
    else:
        db_context = "数据库里未找到相关信息。"

    # --- 步骤 C: 问 DeepSeek ---
    prompt = f"""
    你是一个严谨的考研复试助手。
    请根据下面的【参考资料】回答【用户问题】。
    
    ⚠️ 规则：
    1. 答案必须基于参考资料。
    2. 如果资料里明确提到了（比如“允许使用STL”），请直接告诉用户“允许”。
    3. 如果资料里真没有，就说不知道，不要瞎编。

    【参考资料】：
    {db_context}

    【用户问题】：
    {question_text}
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个乐于助人的助手。"},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"DeepSeek 报错啦: {str(e)}"

# --- 新增功能: 获取文件列表 (给前端下拉框用) ---
def get_file_list():
    print("📂 [逻辑层] 正在查询文件列表...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # SQL 意思是：只选出不重复(DISTINCT)的 source 字段
        cur.execute("SELECT DISTINCT source FROM knowledge_base;")
        
        # 把查询结果变成一个干净的列表，比如 ['math.pdf', 'rule.pdf']
        files = [row[0] for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        print(f"   ✅ 查到了 {len(files)} 个文件")
        return files
    except Exception as e:
        print(f"❌ 获取文件列表失败: {e}")
        return []
