# test_graph.py
from core.workflow import build_workflow

if __name__ == "__main__":
    # 1. 构建工作流
    app = build_workflow()
    
    # 2. 准备初始输入状态 (指定你在 Navicat 里录入的 ID: 1 和你要写的主题)
    initial_state = {
        "user_id": 1, 
        "topic": "为什么年轻人不爱换手机了"
    }
    
    print("🚀 开始运行 LangGraph...")
    # 3. 执行图，invoke 会自动跑完所有节点
    final_state = app.invoke(initial_state)
    
    print("\n🎉 执行完毕！最终生成的脚本如下：\n")
    print(final_state["final_script"])