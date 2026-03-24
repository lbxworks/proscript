import sqlite3
import os

# 动态获取 app.db 的绝对路径
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/app.db')

def run_profiler(state: dict) -> dict:
    print("🤖 [Agent] Profiler 执行中: 正在分析达人风格...")
    user_id = state.get("user_id")
    
    # 连接数据库查询
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT style_prompt, few_shot FROM users WHERE id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        style_prompt, few_shot = result
    else:
        style_prompt, few_shot = "默认客观风格", ""
        print("⚠️ 警告: 未找到该达人，使用默认风格")

    # 返回需要更新到全局状态的数据
    return {"style_prompt": style_prompt, "few_shot": few_shot}