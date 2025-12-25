from fastapi import APIRouter
from pydantic import BaseModel
# 引入刚才写的 logic 文件
import logic 

# 创建一个路由器 (相当于一个小分队)
chat_router = APIRouter()

# 定义接收的数据格式
class Question(BaseModel):
    text: str

# 定义接口：只负责接收请求，然后指挥 logic 去干活
@chat_router.post("/chat")
def chat_endpoint(input_data: Question):
    # 1. 拿到用户问题
    user_question = input_data.text
    
    # 2. 指挥 logic 去问 AI
    ai_answer = logic.ask_deepseek(user_question)
    
    # 3. 把结果包好返回给前端
    return {"data": ai_answer}