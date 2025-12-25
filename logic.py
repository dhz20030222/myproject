import os
from openai import OpenAI
from dotenv import load_dotenv # 专门读取 .env 的工具

# 1. 加载 .env 里的变量
load_dotenv()

# 2. 初始化 AI 客户端 (自动从 .env 里拿 Key)
client = OpenAI(
    api_key=os.getenv("API_KEY"), 
    base_url=os.getenv("BASE_URL")
)

# 3. 定义一个函数：专门负责问 AI
def ask_deepseek(question_text):
    print(f"正在逻辑层处理问题: {question_text}")
    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",  # 记得确认你的模型名字
            messages=[
                {"role": "system", "content": "你是一个考研助手，说话要幽默风趣。"},
                {"role": "user", "content": question_text}
            ],
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"逻辑层报错啦: {str(e)}"