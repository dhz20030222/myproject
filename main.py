import uvicorn
from fastapi import FastAPI
from api import  chat_router # 引入 api.py 里的路由器

app = FastAPI()

# 把 api.py 里定义的接口“挂载”到主程序上
app.include_router(chat_router)

if __name__ == "__main__":
    print("服务正在启动...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)