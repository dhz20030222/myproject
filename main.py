import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import chat_router  # 引入 apCORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # "*" 代表允许任何网址连过来 (生产环境通常填具体的前端网址)
    allow_credentials=True,
    allow_methods=["*"],  # 允许 GET, POST 等所有方法
    allow_headers=["*"],  # 允许所有 Header
)

# 把 api.py 里定义的接口“挂载”到主程序上
app.include_router(chat_router)

if __name__ == "__main__":
    print("服务正在启动...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)