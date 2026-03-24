# core/workflow.py
from langgraph.graph import StateGraph, START, END
from core.state import GraphState
from core.agents.profiler import run_profiler
from core.agents.trend_hunter import run_trend_hunter
from core.agents.writer import run_writer

def build_workflow():
    """构建多智能体工作流"""
    # 1. 初始化图结构
    workflow = StateGraph(GraphState)
    
    # 2. 注册节点 (把前面写的函数注册进来)
    workflow.add_node("Profiler", run_profiler)
    workflow.add_node("TrendHunter", run_trend_hunter)
    workflow.add_node("ScriptWriter", run_writer)
    
    # 3. 定义流转边 (严格定义执行顺序)
    workflow.add_edge(START, "Profiler")
    workflow.add_edge("Profiler", "TrendHunter")
    workflow.add_edge("TrendHunter", "ScriptWriter")
    workflow.add_edge("ScriptWriter", END)
    
    # 4. 编译并返回可执行的 App
    app = workflow.compile()
    return app