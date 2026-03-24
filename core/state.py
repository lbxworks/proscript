# core/state.py
from typing import TypedDict, Optional, List

class GraphState(TypedDict):
    """升级版全局状态字典 (支持多语言与高级配置)"""
    # --- 基础输入 ---
    user_id: int              
    topic: str                
    
    # --- 高级配置  ---
    target_languages: List[str]   # 目标语言列表 (如: 中文, 英语, 阿拉伯语)
    video_duration: str           # 预估时长 (如: 60秒以内)
    target_platform: str          # 目标发布平台 (如: TikTok, YouTube Shorts)
    creativity: float             # AI 创造力 (温度值参考)
    
    # --- 中间状态 ---
    style_prompt: Optional[str]   
    few_shot: Optional[str]       
    trend_data: Optional[str]     
    
    # --- 输出信息 ---
    final_script: Optional[str]