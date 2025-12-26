import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import psycopg2

# 1. 加载环境变量 (读取密码)
load_dotenv()

# 2. 数据库连接配置
DB_URL = os.getenv("DATABASE_URL")

# 3. 初始化向量模型 (这个模型会下载到你本地，专门把中文变成 1024 维向量)
print("正在加载 AI 模型 (第一次运行会下载，稍等)...")
# ⚠️ 必须用这个模型，因为它刚好输出 1024 维，对应你数据库的 vector(1024)
model = SentenceTransformer('BAAI/bge-large-zh-v1.5') 

def import_pdf(file_path):
    print(f"📘 正在处理文件: {file_path}")
    
    # --- A. 读 PDF ---
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    print(f"   ✅ 读到了 {len(pages)} 页")

    # --- B. 切 PDF (关键步骤) ---
    # chunkSize=500: 每块大约500字
    # overlap=50: 每块之间重叠50字 (防止把一句话切断)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, 
        chunk_overlap=50
    )
    docs = text_splitter.split_documents(pages)
    print(f"   ✅ 切成了 {len(docs)} 个豆腐块")

    # --- C. 连接数据库 ---
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    print("   🚀 开始存入数据库 (可能需要一点时间)...")
    
    for i, doc in enumerate(docs):
        # 1. 拿到文字内容
        content = doc.page_content
        # 2. 拿到页码 (pypdf 从 0 开始，所以我们要 +1)
        page_num = doc.metadata.get('page', 0) + 1
        # 3. 拿到文件名
        source_name = os.path.basename(file_path)
        
        # 4. 【最核心】把文字变成向量 (1024 个数字)
        embedding_vector = model.encode(content).tolist()
        
        # 5. 插入数据库 SQL
        sql = """
            INSERT INTO knowledge_base (content, source, page_number, embedding)
            VALUES (%s, %s, %s, %s);
        """
        cur.execute(sql, (content, source_name, page_num, embedding_vector))
        
        if i % 10 == 0:
            print(f"      已存储 {i}/{len(docs)} 块...", end="\r")

    conn.commit() # 提交事务
    cur.close()
    conn.close()
    print(f"\n🎉 成功！《{source_name}》已全部存入知识库！")

# --- 运行测试 ---
if __name__ == "__main__":
    import_pdf("D:/winter/docs/rule.pdf")
    
    print("请修改代码最后一行，填入你真实的 PDF 路径！")