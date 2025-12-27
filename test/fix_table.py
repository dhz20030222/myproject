import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

print("🔧 开始修复数据库表...")

try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    # 1. 删除旧表
    print("1️⃣ 删除旧表...")
    cur.execute("DROP TABLE IF EXISTS knowledge_base;")
    print("   ✅ 旧表已删除")
    
    # 2. 创建新表（正确的维度：1279）
    print("2️⃣ 创建新表（vector(1279)）...")
    cur.execute("""
        CREATE TABLE knowledge_base (
            id BIGSERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            source VARCHAR(255),
            page_number INTEGER,
            metadata JSONB,
            embedding vector(1279)
        );
    """)
    print("   ✅ 新表已创建")
    
    # 3. 创建向量索引（加速搜索）
    print("3️⃣ 创建向量索引...")
    cur.execute("""
        CREATE INDEX ON knowledge_base 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)
    print("   ✅ 索引已创建")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n✅ 修复完成！现在请重新运行 ingest.py 导入数据！")
    
except Exception as e:
    print(f"💥 修复失败: {e}")
