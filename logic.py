import os
import psycopg2
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

# 1. 基础配置
load_dotenv()
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
DB_URL = os.getenv("DATABASE_URL")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")

# 2. 模型懒加载 (这是给 upload_handler 借用的核心)
model = None 

def get_model():
    """懒加载：保证全局只加载一次模型"""
    global model
    if model is None:
        print("🚀 [系统] 正在加载 embedding 模型 (BGE)...")
        model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
    return model

# --- 功能 A: 获取文件列表 ---
def get_file_list():
    print("📂 [逻辑层] 正在查询文件列表...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT source FROM knowledge_base;")
        files = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return files
    except Exception as e:
        print(f"❌ 获取文件列表失败: {e}")
        return []

# --- 功能 B: 流式问答 (Generator) ---
def ask_deepseek(question_text, file_filter=None):
    range_info = f"《{file_filter}》" if file_filter else "【全库】"
    print(f"\n📢 [逻辑层] 用户提问: {question_text} (范围: {range_info})")
    
    # 1. 搜索数据库
    query_instruction = "为这个句子生成表示以用于检索相关文章："
    try:
        # 调用自己的 get_model()
        question_vector = get_model().encode(query_instruction + question_text).tolist()
        
        conn = psycopg2.connect(DB_URL)
        register_vector(conn)
        cur = conn.cursor()
        
        if file_filter:
            sql = "SELECT content, source FROM knowledge_base WHERE source = %s ORDER BY embedding <=> %s::vector LIMIT 3"
            cur.execute(sql, (file_filter, question_vector))
        else:
            sql = "SELECT content, source FROM knowledge_base ORDER BY embedding <=> %s::vector LIMIT 3"
            cur.execute(sql, (question_vector,))
            
        results = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        yield f"❌ 数据库报错: {e}"
        return

    # 2. 组装 Prompt
    db_context = ""
    if results:
        for row in results:
            db_context += f"--- 来源: {row[1]} ---\n{row[0]}\n\n"
    else:
        db_context = "（数据库里未找到相关资料）"

    prompt = f"请根据下面的【参考资料】回答用户问题。\n【参考资料】\n{db_context}\n【用户问题】\n{question_text}"

    # 3. 流式请求 DeepSeek
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个乐于助人的考研助手。"},
                {"role": "user", "content": prompt}
            ],
            stream=True 
        )
        
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content 
    except Exception as e:
        yield f"DeepSeek API 报错: {e}"

# 4. (如果你写了这行) 顶格写的函数调用：立刻执行！
# get_model() 