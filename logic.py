import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import psycopg2
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer # 1. 新增：因为要算向量

# 加载 .env
load_dotenv()

# 初始化 DeepSeek (和你原来一样)
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"), # 注意：确保 .env 里是这个名字
    base_url="https://api.deepseek.com"
)

# 2. 新增：加载那个 1.3G 的模型 (用来把问题变成数字)
# 服务启动时会加载一次，为了能去数据库里搜索
print("正在加载搜索模型...")
model = SentenceTransformer('BAAI/bge-large-zh-v1.5')

def ask_deepseek(question_text):
    print(f"收到问题: {question_text}")
    
    # --- 新增步骤 A: 去数据库找资料 ---
    # A1. 把问题变成向量
    question_vector = model.encode(question_text).tolist()
    
    # A2. 连数据库查最近的 3 条
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    # 这里的 <=> 是“距离最近”的意思
    cur.execute("SELECT content FROM knowledge_base ORDER BY embedding <=> %s::vector LIMIT 3", (question_vector,))
    results = cur.fetchall() # 拿到查询结果
    cur.close()
    conn.close()
    
    # A3. 把查到的资料拼成字符串
    db_context = ""
    if results:
        for row in results:
            db_context += row[0] + "\n---\n" # 把每一段资料拼起来
    else:
        db_context = "数据库里没查到相关内容。"
        
    # --- 原有步骤 B: 问 AI (稍微改一下 prompt) ---
    # 把查到的资料 (db_context) 塞给 AI
    prompt = f"参考资料：\n{db_context}\n\n用户问题：{question_text}\n请根据参考资料回答用户问题。"

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个考研助手。"},
                {"role": "user", "content": prompt} # 这里发给 AI 的是“资料+问题”
            ],
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"报错啦: {str(e)}"