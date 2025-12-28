import shutil
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# 👇 关键：同时引入两个文件
import logic 
import ingest

router = APIRouter()

class ChatRequest(BaseModel):
    text: str
    filename: str | None = None 

# --- 1. 上传接口 (调用 upload_handler) ---
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    temp_path = f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 👇 修改：调用 upload_handler 里的函数
        result = upload_handler.process_uploaded_file(temp_path, file.filename)
        return {"message": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# --- 2. 聊天接口 (调用 logic) ---
@router.post("/chat")
async def chat(request: ChatRequest):
    # 👇 这里的 ask_deepseek 还在 logic 里
    return StreamingResponse(
        logic.ask_deepseek(request.text, request.filename), 
        media_type="text/event-stream"
    )

# --- 3. 列表接口 (调用 logic) ---
@router.get("/files")
def get_files():
    # 👇 列表查询也在 logic 里
    files = logic.get_file_list()
    return {"files": files}