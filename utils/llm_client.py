import os
from pathlib import Path
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# --- 核心修改开始 ---
# 1. 自动定位项目根目录 (即 utils 文件夹的上一级)
# __file__ 是当前脚本的路径，parent 是 utils，parent.parent 就是项目根目录
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
env_path = project_root / '.env'

# 2. 打印调试信息 (告诉你它在去哪里找文件)
print(f"🔍 正在尝试加载配置: {env_path}")

# 3. 指定路径加载
is_loaded = load_dotenv(dotenv_path=env_path)
if not is_loaded:
    print("⚠️ 警告: load_dotenv 返回 False，可能文件不存在或为空！")
# --- 核心修改结束 ---

def get_llm(temperature: float = 0.7):
    """
    获取配置好的 DeepSeek LLM 实例
    Args:
        temperature: AI creativity level (0.0-1.0), mapped from GraphState.creativity
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    # 打印部分 Key 用于验证 (只显示前5位，安全)
    if api_key:
        print(f"🔑 检测到 Key: {api_key[:5]}******")
    else:
        print("❌ 错误: 环境变量中未读取到 Key")
        raise ValueError("请检查 .env 文件是否存在且内容正确")

    return ChatOpenAI(
        model="deepseek-chat", 
        openai_api_key=api_key,
        openai_api_base="https://api.deepseek.com", 
        temperature=temperature
    )

if __name__ == "__main__":
    print("🔄 正在尝试连接 DeepSeek...")
    try:
        llm = get_llm()
        response = llm.invoke("你好，请回复'系统连接成功'这六个字。")
        print(f"✅ 测试通过: {response.content}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")