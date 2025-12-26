import os
import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# 1. 强制使用国内镜像
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# 2. 加载环境
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

# 3. 加载模型
print("正在加载模型 (不要急)...")
model = SentenceTransformer('BAAI/bge-large-zh-v1.5')

def debug_search(keyword):
    print(f"\n🔎 正在测试搜索关键词: 【{keyword}】")
    
    # 生成向量
    # 注意：这里加了 BAAI 推荐的搜索前缀，能提高准确率
    instruction = "为这个句子生成表示以用于检索相关文章："
    vector = model.encode(instruction + keyword).tolist()
    
    # 连数据库
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # 强制把所有匹配结果都拿出来看看 (LIMIT 5)
        sql = """
            SELECT id, content, source, embedding <=> %s::vector as distance 
            FROM knowledge_base 
            ORDER BY distance ASC 
            LIMIT 5;
        """
        cur.execute(sql, (vector,))
        results = cur.fetchall()
        
        print(f"✅ 数据库里找到了 {len(results)} 条最相关的：")
        for i, row in enumerate(results):
            db_id = row[0]
            content = row[1]
            source = row[2]
            distance = row[3] # 距离越小越好 (小于 0.6 算相关)
            
            print("-" * 50)
            print(f"🏆 第 {i+1} 名 (ID: {db_id}) | 距离: {distance:.4f}")
            print(f"📄 来源: {source}")
            # 打印内容的关键部分，看看里面有没有 STL
            print(f"📝 内容摘要: {content[:100]}......") 
            if "STL" in content or "stl" in content:
                print("✨✨✨ 发现关键词 'STL' 在这段话里！✨✨✨")
            else:
                print("❌ 这段话里没提到 STL")
                
        cur.close()
        conn.close()
    except Exception as e:
        print(f"💥 数据库报错: {e}")

if __name__ == "__main__":
    # 直接运行这个脚本，测试你的核心问题
    debug_search("机试能不能用stl")