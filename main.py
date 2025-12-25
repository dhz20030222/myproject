from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from openai import OpenAI  # <--- 1. 引入调用 AI 的工具

# ================= 配置区域 =================
# 请把下面的 sk-xxxx 换成你自己的 DeepSeek API Key
MY_API_KEY = "sk-0de74063189c469aadf55709fe3c267e" 
# ===========================================

# 初始化 AI 客户端
client = OpenAI(
    api_key=MY_API_KEY, 
    base_url="https://api.deepseek.com"  # DeepSeek 的官方地址
)

class Question(BaseModel):
    text: str

app = FastAPI()

@app.post("/chat")
def chat_endpoint(input_data: Question):
    user_question = input_data.text
    print(f"正在问 DeepSeek: {user_question}")
    
    # 2. 这里是真正调用 AI 的代码
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",  # 指定模型
            messages=[
                {"role": "system", "content": "你是一个考研助手，说话要幽默风趣。"},
                {"role": "user", "content": user_question}
            ],
            stream=False
        )
        # 拿到 AI 的回答
        ai_answer = response.choices[0].message.content
        
    except Exception as e:
        ai_answer = f"哎呀，AI 脑子卡住了: {str(e)}"

    return {"data": ai_answer}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)