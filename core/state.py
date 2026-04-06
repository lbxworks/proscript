# core/state.py
from typing import Any, Dict, List, Optional, TypedDict

class GraphState(TypedDict):
    """升级版全局状态字典 (支持多语言与高级配置)"""
    # --- 基础输入 ---
    user_id: int              
    topic: str                
    
    # --- 高级配置  ---
    target_languages: List[str]   # 目标语言列表 (如: 中文, 英语, 阿拉伯语)
    video_duration: str           # 预估时长 (如: 60秒以内)
    target_platform: str          # 目标发布平台 (如: TikTok, YouTube Shorts)
    target_country: str           # 目标国家 (如: US, BR, AE)
    target_region_pack: str       # 目标大区 (如: LATAM, EU, MENA)
    distribution_mode: str        # 发布方式 (如: organic, branded_content, paid_ads)
    product_category: str         # 产品类别 (如: beauty, electronics)
    brand_id: str                 # 品牌标识
    creativity: float             # AI 创造力 (温度值参考)
    
    # --- 中间状态 ---
    style_prompt: Optional[str]   
    few_shot: Optional[str]       
    trend_data: Optional[str]     
    trend_query: Optional[str]
    trend_sources: Optional[List[Dict[str, Any]]]
    compliance_scope: Optional[Dict[str, Any]]
    knowledge_languages: Optional[List[str]]
    retrieved_evidence: Optional[List[Dict[str, Any]]]
    evidence_count: Optional[int]
    retrieval_debug: Optional[Dict[str, Any]]
    rule_issues: Optional[List[Dict[str, Any]]]
    compliance_report: Optional[Dict[str, Any]]
    
    # --- 输出信息 ---
    final_script: Optional[str]
    approved_script: Optional[str]
