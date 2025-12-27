import os
# 1. 魔法代码：强制使用国内镜像 (防断网)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import psycopg2
from pgvector.psycopg2 import register_vector  # 👈 关键修正1：引入向量工具
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

load_dotenv()

# 初始化 DeepSeek
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"), 
    base_url="https://api.deepseek.com"
)

print("正在加载搜索模型 (BGE)...")
model = SentenceTransformer('BAAI/bge-large-zh-v1.5')

def ask_deepseek(question_text):
    print(f"\n📢 用户提问: {question_text}")
    
    # --- 步骤 A: 搜索数据库 ---
    
    # 关键修正2：加上搜索前缀，让匹配更准
    query_instruction = "为这个句子生成表示以用于检索相关文章："
    question_vector = model.encode(query_instruction + question_text).tolist()
    
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        
        # 关键修正3：告诉连接器怎么处理向量
        register_vector(conn)
        
        cur = conn.cursor()
        
        # 关键修正4：SQL语句加上 ::vector 强制转换
        # 意思是：把传进来的数组(%s)当成向量(vector)去和数据库里的比较
        sql = """
            SELECT content, source 
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
            # 打印出来给你看，确认有没有拿到“STL”那段
            print(f"   📄 [资料{i+1}] {content[:20]}...") 
            db_context += f"--- 资料 {i+1} ---\n{content}\n\n"
    else:
        db_context = "数据库里未找到相关信息。"

    # --- 步骤 C: 问 DeepSeek ---
    prompt = f"""
    你是一个严谨的考研复试助手。
    请根据下面的【参考资料】回答【用户问题】。
    
    ⚠️ 规则：
    1. 答案必须基于参考资料。
    2. 如果资料里明确提到了（比如“允许使用STL”），请直接告诉用户“允许”。
    3. 如果资料里真没有，就说不知道。

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

def process_uploaded_file(temp_file_path, filename):
    """
    处理上传文件的空函数（占位符）
    下一步我们再来实现具体的 PDF 读取和入库逻辑
    """
    print(f"👉 [逻辑层] 收到文件: {filename}, 临时路径: {temp_file_path}")
    
    # 暂时先返回一个假结果，证明流程通了
    return "PDF 处理功能尚未实现，但接口调用成功！"