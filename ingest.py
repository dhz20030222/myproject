import os
import psycopg2
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. 加载环境变量
load_dotenv()
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com" 

# 2. 数据库连接配置
DB_URL = os.getenv("DATABASE_URL")

# 3. 初始化向量模型
print("正在加载 AI 模型 (第一次运行会下载，稍等)...")
model = SentenceTransformer('BAAI/bge-large-zh-v1.5') 

# --- 核心功能: 处理上传并入库 (原 import_pdf 改名而来) ---
def process_uploaded_file(temp_file_path, original_filename):
    """
    temp_file_path: 硬盘上那个 temp_xxx.pdf 的路径 (用来读取内容)
    original_filename: 用户原本的文件名 (用来存入数据库 source 字段)
    """
    print(f"📘 [逻辑层] 正在处理文件: {original_filename}")
    
    try:
        # --- A. 读 PDF ---
        # 注意：这里我们要读的是 temp_file_path (临时文件)
        loader = PyPDFLoader(temp_file_path)
        pages = loader.load()
        print(f"   ✅ 读到了 {len(pages)} 页")

        # --- B. 切 PDF ---
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, 
            chunk_overlap=50
        )
        docs = text_splitter.split_documents(pages)
        print(f"   ✅ 切成了 {len(docs)} 个豆腐块")

        # --- C. 连接数据库 ---
        conn = psycopg2.connect(DB_URL)
        
        # 🌟 关键补充：注册 pgvector 适配器
        register_vector(conn) 
        
        cur = conn.cursor()

        print("   🚀 开始存入数据库...")
        
        for i, doc in enumerate(docs):
            # 1. 拿到文字内容
            content = doc.page_content
            # 2. 拿到页码
            page_num = doc.metadata.get('page', 0) + 1
            
            # 3. 拿到文件名 (注意：这里我们要用原始文件名，而不是 temp_xxx)
            source_name = original_filename
            
            # 4. 向量化
            embedding_vector = model.encode(content).tolist()
            
            # 5. 插入数据库
            sql = """
                INSERT INTO knowledge_base (content, source, page_number, embedding)
                VALUES (%s, %s, %s, %s);
            """
            cur.execute(sql, (content, source_name, page_num, embedding_vector))
            
            if i % 10 == 0:
                print(f"      已存储 {i}/{len(docs)} 块...", end="\r")

        conn.commit()
        cur.close()
        conn.close()
        
        # ✅ 改动点：原来是 print，现在要 return 字符串给 API
        return f"成功！《{source_name}》已全部存入知识库，共 {len(docs)} 条数据。"

    except Exception as e:
        print(f"❌ 处理失败: {e}")
        # 把错误往外抛，让 API 知道出错了
        raise e

# --- 占位符：防止 api.py 报错 ---
def ask_deepseek(question, file_filter=None):
    return "提问功能稍后上线..."