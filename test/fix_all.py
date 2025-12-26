import os
import psycopg2
from pgvector.psycopg2 import register_vector # 👈 关键：引入向量适配器
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# 1. 基础配置
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com" # 镜像加速
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

# 2. 加载模型
print("📥 正在加载模型...")
model = SentenceTransformer('BAAI/bge-large-zh-v1.5')

def run_fix():
    print("\n🧹 正在连接数据库...")
    conn = psycopg2.connect(DB_URL)
    
    # 【核心修复】告诉数据库：这是向量，不是字符串！
    register_vector(conn) 
    
    cur = conn.cursor()

    # 3. 清空旧表，确保 vector(1024) 维度正确
    print("🗑️ 清空旧数据...")
    cur.execute("DROP TABLE IF EXISTS knowledge_base;")
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute("""
        CREATE TABLE knowledge_base (
            id SERIAL PRIMARY KEY,
            content TEXT,
            source TEXT,
            page_number INTEGER,
            embedding vector(1024) 
        );
    """)
    conn.commit()

    # 4. 重新读取 PDF
    pdf_path = "D:/winter/docs/rule.pdf" # ⚠️ 确认路径对不对
    print(f"📘 正在重新读取: {pdf_path}")
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = text_splitter.split_documents(pages)
    print(f"✅ 切分完成: 共 {len(docs)} 个片段")

    # 5. 正确存入
    print("🚀 正在重新入库 (使用正确格式)...")
    for doc in docs:
        content = doc.page_content
        page = doc.metadata.get('page', 0) + 1
        source = os.path.basename(pdf_path)
        # 生成向量
        vec = model.encode(content).tolist()
        
        # 直接存入！不需要手动转 string，适配器会帮我们要搞定
        cur.execute(
            "INSERT INTO knowledge_base (content, source, page_number, embedding) VALUES (%s, %s, %s, %s)",
            (content, source, page, vec)
        )
    conn.commit()
    print("🎉 入库完成！")

    # 6. 立即测试搜索
    print("\n🔎 正在进行最终测试：搜索【机试能不能用stl】...")
    query = "为这个句子生成表示以用于检索相关文章：机试能不能用stl"
    q_vec = model.encode(query).tolist()
    
    # 这里的查询也变得简单了，不需要 cast
    cur.execute("SELECT content, embedding <=> %s::vector FROM knowledge_base ORDER BY embedding <=> %s::vector LIMIT 3", (q_vec, q_vec))
    results = cur.fetchall()
    # 注意：两个 %s 后面都要加 ::vector
    
    if len(results) > 0:
        print(f"✅ 成功搜到 {len(results)} 条结果！")
        print(f"📄 第一条内容预览: {results[0][0][:50]}...")
    else:
        print("❌ 依然搜不到... 请检查 PDF 内容是否真的包含关键词。")

    cur.close()
    conn.close()

if __name__ == "__main__":
    run_fix()