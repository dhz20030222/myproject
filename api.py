from fastapi import APIRouter
from pydantic import BaseModel
import logic ,ingest
from fastapi import FastAPI,UploadFile, File, HTTPException,APIRouter
import shutil  # 👈 必须有这一行，用来保存文件
import os      # 👈 必须有这一行，用来删除临时文件


router = APIRouter()

# ... 下面的代码保持不变 ...

# 创建一个路由器 (相当于一个小分队)
router = APIRouter()

# 定义接收的数据格式
class Question(BaseModel):
    text: str

# 定义接口：只负责接收请求，然后指挥 logic 去干活
@router.post("/chat")
def chat_endpoint(input_data: Question):
    # 1. 拿到用户问题
    user_question = input_data.text
    
    # 2. 指挥 logic 去问 AI
    ai_answer = logic.ask_deepseek(user_question)
    
    # 3. 把结果包好返回给前端
    return {"data": ai_answer}

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):###fastapi的语法  告诉fastapi 这个参数是一个文件  并且...是内容不能为空
    # A. 确定临时文件路径   格式化字符串
    temp_path = f"temp_{file.filename}"
    try:
        # B. 把上传的文件流写入硬盘 “逻辑层为什么不直接读内存里的数据？为什么要先存成临时文件再读？”
        #1 若用户太多 内存爆     2 后面切片langchain需要的参数是文件路径
        with open(temp_path, "wb") as buffer: # with 代码出了缩进块自动关文件
            shutil.copyfileobj(file.file, buffer)# shutil每次只往内存读16KB
            
        print(f"✅ [接口层] 文件已暂存到: {temp_path}")

        # C. 调用逻辑层 (我们刚才写的那个空函数)
        # 注意：这里我们把“硬盘上的路径”和“原始文件名”传过去
        result = ingest.process_uploaded_file(temp_path, file.filename)
        
        return {"message": f"上传成功！逻辑层返回: {result}"}
        
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # D. 清理战场：无论成功失败，都要删掉临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
            print(f"🧹 [接口层] 临时文件已清理: {temp_path}")