import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

print("🔍 开始诊断数据库...")
print(f"📌 连接字符串: {DB_URL[:50]}...")

try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    # 1. 检查表是否存在
    print("\n1️⃣ 检查表是否存在...")
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'knowledge_base'
        );
    """)
    exists = cur.fetchone()[0]
    print(f"   knowledge_base 表存在: {exists}")
    
    if not exists:
        print("   ❌ 表不存在！请先创建表！")
        exit()
    
    # 2. 检查表结构
    print("\n2️⃣ 检查表结构...")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'knowledge_base';
    """)
    columns = cur.fetchall()
    for col in columns:
        print(f"   - {col[0]}: {col[1]}")
    
    # 3. 检查数据总数
    print("\n3️⃣ 检查数据总数...")
    cur.execute("SELECT COUNT(*) FROM knowledge_base;")
    count = cur.fetchone()[0]
    print(f"   总共有 {count} 条数据")
    
    if count == 0:
        print("   ❌ 表是空的！请先运行 ingest.py 导入数据！")
        exit()
    
    # 4. 查看前 2 条数据
    print("\n4️⃣ 查看前 2 条数据...")
    cur.execute("SELECT id, source, page_number, LEFT(content, 50) FROM knowledge_base LIMIT 2;")
    rows = cur.fetchall()
    for row in rows:
        print(f"   ID: {row[0]} | 来源: {row[1]} | 页码: {row[2]}")
        print(f"   内容: {row[3]}...")
    
    # 5. 检查 embedding 字段
    print("\n5️⃣ 检查 embedding 向量...")
    cur.execute("SELECT embedding FROM knowledge_base LIMIT 1;")
    emb = cur.fetchone()[0]
    if emb:
        print(f"   ✅ embedding 存在，维度: {len(emb)}")
    else:
        print("   ❌ embedding 为空！")
    
    # 6. 检查 pgvector 扩展
    print("\n6️⃣ 检查 pgvector 扩展...")
    cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
    ext = cur.fetchone()
    if ext:
        print(f"   ✅ pgvector 扩展已安装")
    else:
        print("   ❌ pgvector 扩展未安装！这是问题所在！")
        print("   请在 Supabase SQL Editor 中运行: CREATE EXTENSION vector;")
    
    cur.close()
    conn.close()
    print("\n✅ 诊断完成！")
    
except Exception as e:
    print(f"\n💥 连接失败: {e}")
