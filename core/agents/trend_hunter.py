def run_trend_hunter(state: dict) -> dict:
    print("🤖 [Agent] Trend Hunter 执行中: 正在全网检索热点...")
    topic = state.get("topic")
    
    # MVP 阶段：用假数据占位，保证流程通畅
    mock_trend = f"关于【{topic}】的最新热点：最近各大平台都在讨论它的痛点和反常识点..."
    
    return {"trend_data": mock_trend}