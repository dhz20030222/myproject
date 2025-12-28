import os
import psycopg2
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 👇 关键点：从 logic.py 借用 get_model，不要自己再 import SentenceTransformer 了
from logic import get_model 

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

def process_uploaded_file(temp_file_path, original_filename):
    print(f"📘 [上传层] 正在处理文件: {original_filename}")
    
    try:
        # 1. 读 PDF
        loader = PyPDFLoader(temp_file_path)
        pages = loader.load()

        # 2. 切分
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = text_splitter.split_documents(pages)

        # 3. 存入数据库
        conn = psycopg2.connect(DB_URL)
        register_vector(conn)
        cur = conn.cursor()
        
        # 4. 循环插入
        for doc in docs:
            content = doc.page_content
            page_num = doc.metadata.get('page', 0) + 1
            
            # 👇 这里调用 logic 里的模型来生成向量
            embedding_vector = get_model().encode(content).tolist()
            
            sql = "INSERT INTO knowledge_base (content, source, page_number, embedding) VALUES (%s, %s, %s, %s)"
            cur.execute(sql, (content, original_filename, page_num, embedding_vector))

        conn.commit()
        cur.close()
        conn.close()
        
        return f"成功！《{original_filename}》已全部存入知识库，共 {len(docs)} 条数据。"

    except Exception as e:
        print(f"❌ 处理失败: {e}")
        raise e