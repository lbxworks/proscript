# app.py
from datetime import datetime
import html
import os
import sqlite3
import threading
from urllib.parse import urlparse
import streamlit as st
from core.compliance_config import MARKETS, get_region_for_country
from core.compliance_kb import (
    get_knowledge_index_status,
    initialize_knowledge_runtime,
    normalize_raw_knowledge_files,
    rebuild_knowledge_runtime,
)
from core.workflow import build_workflow
from utils.tavily_client import search_viral_video_benchmarks

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'app.db')
LANG_OPTIONS = {"简体中文": "zh", "English": "en", "Español": "es"}

# =====================================================================
# UI_STRINGS: Centralized i18n Translation Dictionary
# =====================================================================
UI_STRINGS = {
    "en": {
        # Page
        "page_title": "Pro-Script AI | Professional Shooting Script Generator",
        # Header
        "title_badge": "🎬 Professional Production Tool",
        "title_main": "Pro-Script AI",
        "subtitle": "Professional Shooting Script Generator — Powered by Multi-Agent AI",
        # Sidebar
        "sidebar_settings": "## ⚙️ Production Settings",
        "sidebar_lang_label": "🌏 Language / 语言 / Idioma",
        "section_creator": "### 🎭 Creator Profile",
        "select_creator": "Select Creator Profile:",
        "db_not_connected": "⚠️ Database not connected",
        "section_localization": "### 🌐 Localization",
        "output_languages": "Output Languages (Dialogue / VO):",
        "section_distribution": "### 📺 Distribution",
        "target_platform": "Target Platform:",
        "video_duration": "Video Duration:",
        "section_ai_params": "### 🎛️ AI Parameters",
        "creativity_label": "AI Creativity (Temperature):",
        "creativity_help": "Higher values produce more creative and experimental scripts.",
        "powered_by": "🚀 Powered by LangGraph + Google Priority + DeepSeek Fallback",
        "target_market": "Target Market:",
        "target_region_pack": "Region Pack",
        "plat_x": "X / Twitter",
        "plat_reddit": "Reddit",
        "plat_discord": "Discord",
        "distribution_mode": "Distribution Mode:",
        "mode_organic": "Organic Post",
        "mode_branded": "Branded Content",
        "mode_paid": "Paid Ads",
        "product_category": "Product Category:",
        "brand_id": "Brand ID:",
        "cat_general": "General Merchandise",
        "cat_beauty": "Beauty & Personal Care",
        "cat_electronics": "Electronics",
        "cat_fashion": "Fashion",
        "cat_food": "Food & Beverage",
        "cat_health": "Health / Supplement",
        "output_compliance_title": "🛡 Compliance Review",
        "output_workflow_title": "🧭 Workflow Trace",
        "workflow_subtitle": "Each stage below ran in sequence. Trend Hunter shows whether live search succeeded.",
        "workflow_profiler": "Profiler",
        "workflow_trend": "Trend Hunter",
        "workflow_writer": "Script Writer",
        "workflow_scope": "Scope Resolver",
        "workflow_retriever": "Compliance Retriever",
        "workflow_rules": "Rule Engine",
        "workflow_reviewer": "Compliance Reviewer",
        "workflow_rewriter": "Compliance Rewriter",
        "workflow_stage_done": "Done",
        "workflow_stage_live": "Live",
        "workflow_stage_fallback": "Fallback",
        "output_trend_title": "🌍 Trend Hunter Signals",
        "trend_status_label": "Trend Status",
        "trend_sources_label": "Sources Found",
        "trend_query_label": "Search Query",
        "trend_summary_label": "Trend Summary",
        "trend_results_label": "Matched Results",
        "trend_live_status": "Live Search Active",
        "trend_fallback_status": "Fallback Summary",
        "trend_preview_label": "Preview",
        "trend_preview_hint": "Hover over a title to preview the source.",
        "trend_preview_empty": "No preview text is available for this source.",
        "trend_no_results": "No source cards were returned for this search.",
        "compliance_status_label": "Review Status",
        "compliance_risk_label": "Risk Level",
        "compliance_market_label": "Market Scope",
        "compliance_evidence_label": "Issues Found",
        "compliance_no_issues": "No material issues were flagged in the current review.",
        "compliance_no_citations": "No citation available",
        "compliance_script_excerpt": "Quoted Script",
        "compliance_reason": "Risk Analysis",
        "compliance_fix": "Revision Suggestion",
        "compliance_citations": "Supporting Citations",
        "compliance_closing": "Overall Commentary",
        "approved_script_title": "✅ Recommended Revision",
        "script_model_badge": "Model Used",
        "script_model_fallback": "Fallback",
        "runtime_progress_start": "Preparing the compliance runtime...",
        "runtime_progress_check": "Checking cached model and Qdrant index...",
        "runtime_progress_ready": "Compliance runtime ready.",
        "runtime_status_title": "Preparing multilingual compliance retrieval",
        "runtime_status_done": "Compliance runtime ready",
        "runtime_status_error": "Compliance runtime initialization failed",
        "runtime_error_message": "Failed to prepare the compliance runtime.",
        "status_scope": ">> 🧭 [Compliance Scope] Resolving platform, market, and language scope...",
        "status_retriever": ">> 📚 [Compliance Retriever] Querying Qdrant and scoped evidence blocks...",
        "status_rules": ">> 🧪 [Rule Engine] Checking disclosure, risky wording, and unsupported claims...",
        "status_reviewer": ">> 🛡️ [Compliance Reviewer] Synthesizing evidence, rule hits, and revisions...",
        "status_rewriter": ">> ✍️ [Compliance Rewriter] Drafting a safer revised script when needed...",
        "health_card_title": "Compliance Runtime Health",
        "health_card_subtitle": "Local Qdrant index and multilingual embedding status",
        "health_ready_title": "System Healthy (Ready)",
        "health_ready_body": "Multilingual retrieval is online and ready for compliance review.",
        "health_empty_title": "Knowledge Base Empty",
        "health_empty_body": "The runtime is initialized, but no usable compliance documents are indexed yet.",
        "health_missing_title": "Initialization Needed",
        "health_missing_body": "No local index was found yet. The app will build it when needed.",
        "health_unknown_title": "Status Pending",
        "health_unknown_body": "The runtime loaded, but the health snapshot is still incomplete.",
        "health_model_label": "Current Model",
        "health_docs_label": "Documents",
        "health_chunks_label": "Chunks",
        "health_built_at": "Last built",
        "rebuild_button": "🔄 Update / Rebuild Knowledge Base",
        "rebuild_progress_start": "Scanning local knowledge files and preparing rebuild...",
        "rebuild_status_title": "Rebuilding multilingual compliance knowledge base",
        "rebuild_progress_check": "Checking model files and rebuilding the local Qdrant index...",
        "rebuild_status_error": "Knowledge base rebuild failed",
        "rebuild_error_message": "The knowledge base rebuild failed. Please check the logs and try again.",
        "rebuild_progress_done": "Knowledge base updated successfully.",
        "rebuild_status_done": "Knowledge base rebuild complete",
        "rebuild_success_message": "Knowledge base updated successfully!",
        "runtime_sidebar_hint": "Tip: add new local knowledge files, then click the rebuild button above to refresh the index.",
        # Duration options
        "dur_15s": "15s (Flash)",
        "dur_30s": "30s (Standard)",
        "dur_60s": "60s (Immersive)",
        "dur_3min": "3min (Deep Dive)",
        # Platform options
        "plat_tiktok": "TikTok (International)",
        "plat_youtube": "YouTube Shorts",
        "plat_instagram": "Instagram Reels",
        "plat_douyin": "Douyin / WeChat Channels",
        # Input area
        "input_label": "Script Topic",
        "input_placeholder": "✍️ Enter your video concept, e.g. 'A 60-second cyberpunk product launch for a new smartwatch, targeting Gen-Z on TikTok...'",
        "btn_generate": "🎬 Generate Shooting Script",
        # Errors & Status
        "error_empty": "⚠️ Please enter a video topic and ensure the database is connected.",
        "status_running": "⚙️ Multi-Agent Pipeline Running...",
        "status_profiler": ">> 📋 [Profiler Agent] Loading creator style profile from database...",
        "status_trend": ">> 🌍 [Trend Hunter] Scanning platform trends and viral factors...",
        "status_writer": ">> 🎬 [Script Writer] Generating professional shooting script...",
        "status_done": "✅ Shooting Script Generated Successfully",
        "status_error": "❌ Pipeline Error",
        "output_title": "🎬 Professional Shooting Script",
        "save_success": "✅ Script saved to local database (app.db)",
        # Gallery
        "section_viral": "🔥 Viral Tech Video Benchmarks",
        "section_viral_subtitle": "Live Tavily scan of public {scope} posts from the last 3 days in {country}. Only results with 1M+ view signals are shown.",
        "section_viral_live": "Live via Tavily",
        "section_viral_mixed_scope": "TikTok / Instagram / X",
        "section_viral_window": "Last 3 days",
        "section_viral_views": "views",
        "section_viral_open": "Open video",
        "section_viral_refresh": "🔄 Refresh",
        "section_viral_note": "View counts are parsed heuristically from public snippets returned by Tavily.",
        "section_viral_empty": "No recent public TikTok / Instagram / X videos with 1M+ view signals were detected for this market.",
        "section_viral_loading": "Scanning recent public platform videos...",
        # Templates
        "section_templates": "🎨 Pro Script Templates",
        "tpl_1_title": "🖥 Tech Unboxing Long Take",
        "tpl_1_sub": "Best for: YouTube MKBHD Style",
        "tpl_2_title": "👟 Bullet-Time Street Style",
        "tpl_2_sub": "Best for: TikTok Product Drop",
        "tpl_3_title": "💫 Concept Drama Short",
        "tpl_3_sub": "Best for: Instagram Reels Narrative",
        "tpl_4_title": "🧬 Macro-to-Cosmos Explainer",
        "tpl_4_sub": "Best for: Bilibili / YouTube Science",
    },
    "zh": {
        # Page
        "page_title": "脚本生成增强版AI | 专业拍摄脚本生成器",
        # Header
        "title_badge": "🎬 专业影视制作工具",
        "title_main": "Pro-Script AI",
        "subtitle": "专业拍摄脚本生成器 — 多智能体 AI 驱动",
        # Sidebar
        "sidebar_settings": "## ⚙️ 制作设置",
        "sidebar_lang_label": "🌏 Language / 语言 / Idioma",
        "section_creator": "### 🎭 创作者档案",
        "select_creator": "选择创作者档案：",
        "db_not_connected": "⚠️ 数据库未连接",
        "section_localization": "### 🌐 语言本地化",
        "output_languages": "输出语种（对白/旁白）：",
        "section_distribution": "### 📺 分发渠道",
        "target_platform": "目标平台：",
        "video_duration": "视频时长：",
        "section_ai_params": "### 🎛️ AI 参数",
        "creativity_label": "AI 创造力（温度值）：",
        "creativity_help": "数值越高，生成的脚本越具创意和实验性。",
        "powered_by": "🚀 由 LangGraph + Google 主路由 + DeepSeek 兜底驱动",
        "target_market": "目标市场：",
        "target_region_pack": "区域包",
        "plat_x": "X / Twitter",
        "plat_reddit": "Reddit",
        "plat_discord": "Discord",
        "distribution_mode": "分发方式：",
        "mode_organic": "自然发布",
        "mode_branded": "品牌合作内容",
        "mode_paid": "付费广告",
        "product_category": "产品类别：",
        "brand_id": "品牌 ID：",
        "cat_general": "通用消费品",
        "cat_beauty": "美妆个护",
        "cat_electronics": "电子产品",
        "cat_fashion": "时尚服饰",
        "cat_food": "食品饮料",
        "cat_health": "健康 / 保健品",
        "output_compliance_title": "🛡 合规审查",
        "output_workflow_title": "🧭 工作流追踪",
        "workflow_subtitle": "下面展示的是本次顺序执行的完整链路，其中 Trend Hunter 会标明是否成功完成实时搜索。",
        "workflow_profiler": "风格分析师",
        "workflow_trend": "趋势猎手",
        "workflow_writer": "脚本编剧",
        "workflow_scope": "范围解析器",
        "workflow_retriever": "合规检索器",
        "workflow_rules": "规则引擎",
        "workflow_reviewer": "合规审查员",
        "workflow_rewriter": "合规改写器",
        "workflow_stage_done": "已完成",
        "workflow_stage_live": "实时生效",
        "workflow_stage_fallback": "兜底模式",
        "output_trend_title": "🌍 趋势猎手情报",
        "trend_status_label": "趋势状态",
        "trend_sources_label": "命中来源",
        "trend_query_label": "搜索查询",
        "trend_summary_label": "趋势摘要",
        "trend_results_label": "搜索结果",
        "trend_live_status": "实时搜索已生效",
        "trend_fallback_status": "使用兜底摘要",
        "trend_preview_label": "内容预览",
        "trend_preview_hint": "将鼠标移到标题上可查看来源预览。",
        "trend_preview_empty": "该来源暂无可用预览文本。",
        "trend_no_results": "这次搜索没有返回可展示的来源卡片。",
        "compliance_status_label": "审查状态",
        "compliance_risk_label": "风险等级",
        "compliance_market_label": "市场范围",
        "compliance_evidence_label": "发现的问题数",
        "compliance_no_issues": "本轮审查没有发现明显的实质性问题。",
        "compliance_no_citations": "暂无引文",
        "compliance_script_excerpt": "引用文案",
        "compliance_reason": "风险分析",
        "compliance_fix": "修改建议",
        "compliance_citations": "支持引文",
        "compliance_closing": "整体点评",
        "approved_script_title": "✅ 推荐修改稿",
        "script_model_badge": "生成模型",
        "script_model_fallback": "已切换兜底",
        "runtime_progress_start": "正在准备合规运行时...",
        "runtime_progress_check": "正在检查缓存模型和 Qdrant 索引...",
        "runtime_progress_ready": "合规运行时已就绪。",
        "runtime_status_title": "正在准备多语种合规检索",
        "runtime_status_done": "合规运行时已就绪",
        "runtime_status_error": "合规运行时初始化失败",
        "runtime_error_message": "合规运行时准备失败，请检查日志。",
        "status_scope": ">> 🧭 [合规范围解析] 正在确定平台、市场与语言范围...",
        "status_retriever": ">> 📚 [合规检索器] 正在查询 Qdrant 与范围内证据块...",
        "status_rules": ">> 🧪 [规则引擎] 正在检查披露要求、风险措辞和未经支持的 claim...",
        "status_reviewer": ">> 🛡️ [合规审查员] 正在综合证据、规则命中和修改建议...",
        "status_rewriter": ">> ✍️ [合规改写器] 正在生成更安全的修订文案...",
        "health_card_title": "合规运行时健康检查",
        "health_card_subtitle": "本地 Qdrant 索引与多语种向量模型状态",
        "health_ready_title": "系统健康 (Ready)",
        "health_ready_body": "多语种检索运行正常，当前索引可直接用于合规审查。",
        "health_empty_title": "知识库为空",
        "health_empty_body": "运行时已初始化，但还没有可用的法规或平台文档被索引。",
        "health_missing_title": "等待初始化",
        "health_missing_body": "暂未检测到本地索引，系统会在需要时自动构建。",
        "health_unknown_title": "状态待确认",
        "health_unknown_body": "运行时已加载，但健康检查数据暂未完整返回。",
        "health_model_label": "当前模型",
        "health_docs_label": "法规文档",
        "health_chunks_label": "知识块",
        "health_built_at": "最近构建",
        "rebuild_button": "🔄 更新/重建知识库",
        "rebuild_progress_start": "正在扫描本地知识文件并准备重建...",
        "rebuild_status_title": "正在重建多语种合规知识库",
        "rebuild_progress_check": "正在检查模型文件并重建本地 Qdrant 索引...",
        "rebuild_status_error": "知识库重建失败",
        "rebuild_error_message": "知识库重建失败，请查看日志后重试。",
        "rebuild_progress_done": "知识库已更新完成。",
        "rebuild_status_done": "知识库重建完成",
        "rebuild_success_message": "知识库更新成功！",
        "runtime_sidebar_hint": "提示：新增本地知识文件后，点击上方按钮即可刷新索引。",
        # Duration options
        "dur_15s": "15秒（极速）",
        "dur_30s": "30秒（标准）",
        "dur_60s": "60秒（沉浸）",
        "dur_3min": "3分钟（深度）",
        # Platform options
        "plat_tiktok": "TikTok（国际版）",
        "plat_youtube": "YouTube Shorts",
        "plat_instagram": "Instagram Reels",
        "plat_douyin": "抖音 / 视频号",
        # Input area
        "input_label": "脚本主题",
        "input_placeholder": "✍️ 输入你的视频概念，例如：「60秒赛博朋克新品发布短片，面向TikTok Z世代...」",
        "btn_generate": "🎬 生成拍摄脚本",
        # Errors & Status
        "error_empty": "⚠️ 请输入视频主题并确保数据库已连接。",
        "status_running": "⚙️ 多智能体流水线运行中...",
        "status_profiler": ">> 📋 [风格分析师] 正在从数据库加载创作者风格档案...",
        "status_trend": ">> 🌍 [趋势猎手] 正在扫描全网热点与爆款因子...",
        "status_writer": ">> 🎬 [脚本编剧] 正在生成专业拍摄脚本...",
        "status_done": "✅ 拍摄脚本生成成功",
        "status_error": "❌ 流水线错误",
        "output_title": "🎬 专业拍摄脚本",
        "save_success": "✅ 脚本已保存至本地数据库 (app.db)",
        # Gallery
        "section_viral": "🔥 近三天科技热视频基准",
        "section_viral_subtitle": "通过 Tavily 实时扫描 {country} 市场近 3 天内的公开 {scope} 内容，仅展示检测到 100 万以上播放信号的视频结果。",
        "section_viral_live": "Tavily 实时数据",
        "section_viral_mixed_scope": "TikTok / Instagram / X",
        "section_viral_window": "近 3 天",
        "section_viral_views": "播放",
        "section_viral_open": "打开视频",
        "section_viral_refresh": "🔄 换一换",
        "section_viral_note": "播放量来自 Tavily 返回的公开片段文本解析，属于启发式识别结果。",
        "section_viral_empty": "当前市场下，暂未检索到近 3 天内带有 100 万以上播放信号的公开 TikTok / Instagram / X 科技热视频。",
        "section_viral_loading": "正在扫描最近公开平台热视频...",
        # Templates
        "section_templates": "🎨 专业脚本模板",
        "tpl_1_title": "🖥 科技开箱长镜头",
        "tpl_1_sub": "适用：YouTube MKBHD 风格",
        "tpl_2_title": "👟 子弹时间街拍",
        "tpl_2_sub": "适用：TikTok 潮品发售",
        "tpl_3_title": "💫 概念短剧",
        "tpl_3_sub": "适用：Instagram Reels 叙事",
        "tpl_4_title": "🧬 微观到宇宙科普",
        "tpl_4_sub": "适用：B站 / YouTube 科普",
    },
    "es": {
        # Page
        "page_title": "Pro-Script AI | Generador Profesional de Guiones de Rodaje",
        # Header
        "title_badge": "🎬 Herramienta de Producción Profesional",
        "title_main": "Pro-Script AI",
        "subtitle": "Generador Profesional de Guiones de Rodaje — Impulsado por IA Multi-Agente",
        # Sidebar
        "sidebar_settings": "## ⚙️ Ajustes de Producción",
        "sidebar_lang_label": "🌏 Language / 语言 / Idioma",
        "section_creator": "### 🎭 Perfil del Creador",
        "select_creator": "Seleccionar Perfil del Creador:",
        "db_not_connected": "⚠️ Base de datos no conectada",
        "section_localization": "### 🌐 Localización",
        "output_languages": "Idiomas de Salida (Diálogo / VO):",
        "section_distribution": "### 📺 Distribución",
        "target_platform": "Plataforma Objetivo:",
        "video_duration": "Duración del Vídeo:",
        "section_ai_params": "### 🎛️ Parámetros de IA",
        "creativity_label": "Creatividad de IA (Temperatura):",
        "creativity_help": "Valores más altos producen guiones más creativos y experimentales.",
        "powered_by": "🚀 Impulsado por LangGraph + Google prioritario + fallback DeepSeek",
        "target_market": "Mercado objetivo:",
        "target_region_pack": "Paquete regional",
        "plat_x": "X / Twitter",
        "plat_reddit": "Reddit",
        "plat_discord": "Discord",
        "distribution_mode": "Modo de distribución:",
        "mode_organic": "Publicación orgánica",
        "mode_branded": "Contenido de marca",
        "mode_paid": "Anuncios pagados",
        "product_category": "Categoría del producto:",
        "brand_id": "ID de marca:",
        "cat_general": "Mercancía general",
        "cat_beauty": "Belleza y cuidado personal",
        "cat_electronics": "Electrónica",
        "cat_fashion": "Moda",
        "cat_food": "Alimentos y bebidas",
        "cat_health": "Salud / Suplementos",
        "output_compliance_title": "🛡 Revisión de Compliance",
        "output_workflow_title": "🧭 Trazado del Workflow",
        "workflow_subtitle": "Las etapas de abajo se ejecutaron en secuencia. Trend Hunter indica si la búsqueda en vivo funcionó.",
        "workflow_profiler": "Profiler",
        "workflow_trend": "Trend Hunter",
        "workflow_writer": "Guionista",
        "workflow_scope": "Resolutor de alcance",
        "workflow_retriever": "Retriever de Compliance",
        "workflow_rules": "Motor de Reglas",
        "workflow_reviewer": "Revisor de Compliance",
        "workflow_rewriter": "Reescritor de Compliance",
        "workflow_stage_done": "Listo",
        "workflow_stage_live": "En vivo",
        "workflow_stage_fallback": "Respaldo",
        "output_trend_title": "🌍 Señales de Trend Hunter",
        "trend_status_label": "Estado de tendencia",
        "trend_sources_label": "Fuentes encontradas",
        "trend_query_label": "Consulta de búsqueda",
        "trend_summary_label": "Resumen de tendencias",
        "trend_results_label": "Resultados encontrados",
        "trend_live_status": "Búsqueda en vivo activa",
        "trend_fallback_status": "Resumen de respaldo",
        "trend_preview_label": "Vista previa",
        "trend_preview_hint": "Pasa el cursor sobre un título para previsualizar la fuente.",
        "trend_preview_empty": "No hay texto de vista previa disponible para esta fuente.",
        "trend_no_results": "Esta búsqueda no devolvió tarjetas de fuente para mostrar.",
        "compliance_status_label": "Estado de revisión",
        "compliance_risk_label": "Nivel de riesgo",
        "compliance_market_label": "Alcance del mercado",
        "compliance_evidence_label": "Problemas detectados",
        "compliance_no_issues": "No se detectaron problemas materiales en la revisión actual.",
        "compliance_no_citations": "Sin cita disponible",
        "compliance_script_excerpt": "Texto citado",
        "compliance_reason": "Análisis de riesgo",
        "compliance_fix": "Sugerencia de revisión",
        "compliance_citations": "Citas de respaldo",
        "compliance_closing": "Comentario general",
        "approved_script_title": "✅ Versión recomendada",
        "script_model_badge": "Modelo usado",
        "script_model_fallback": "Fallback activado",
        "runtime_progress_start": "Preparando el runtime de compliance...",
        "runtime_progress_check": "Verificando el modelo en caché y el índice de Qdrant...",
        "runtime_progress_ready": "El runtime de compliance está listo.",
        "runtime_status_title": "Preparando la recuperación multilingüe de compliance",
        "runtime_status_done": "Runtime de compliance listo",
        "runtime_status_error": "Falló la inicialización del runtime de compliance",
        "runtime_error_message": "No se pudo preparar el runtime de compliance.",
        "status_scope": ">> 🧭 [Ámbito de Compliance] Resolviendo plataforma, mercado e idioma...",
        "status_retriever": ">> 📚 [Retriever de Compliance] Consultando Qdrant y bloques de evidencia filtrados...",
        "status_rules": ">> 🧪 [Motor de Reglas] Revisando disclosure, lenguaje riesgoso y claims no sustentados...",
        "status_reviewer": ">> 🛡️ [Revisor de Compliance] Integrando evidencia, reglas y revisiones...",
        "status_rewriter": ">> ✍️ [Reescritor de Compliance] Generando una versión más segura cuando hace falta...",
        "health_card_title": "Estado del Runtime de Compliance",
        "health_card_subtitle": "Estado del índice local de Qdrant y del modelo multilingüe",
        "health_ready_title": "Sistema Saludable (Ready)",
        "health_ready_body": "La recuperación multilingüe está disponible y lista para la revisión de compliance.",
        "health_empty_title": "Base de conocimiento vacía",
        "health_empty_body": "El runtime está inicializado, pero todavía no hay documentos útiles indexados.",
        "health_missing_title": "Falta inicialización",
        "health_missing_body": "Aún no se detectó un índice local. La app lo construirá cuando haga falta.",
        "health_unknown_title": "Estado pendiente",
        "health_unknown_body": "El runtime cargó, pero el resumen de salud aún no está completo.",
        "health_model_label": "Modelo actual",
        "health_docs_label": "Documentos",
        "health_chunks_label": "Bloques",
        "health_built_at": "Última construcción",
        "rebuild_button": "🔄 Actualizar / Reconstruir Base de Conocimiento",
        "rebuild_progress_start": "Escaneando archivos locales y preparando la reconstrucción...",
        "rebuild_status_title": "Reconstruyendo la base multilingüe de compliance",
        "rebuild_progress_check": "Verificando archivos del modelo y reconstruyendo el índice local de Qdrant...",
        "rebuild_status_error": "Falló la reconstrucción de la base",
        "rebuild_error_message": "La reconstrucción falló. Revisa los logs e inténtalo de nuevo.",
        "rebuild_progress_done": "Base de conocimiento actualizada correctamente.",
        "rebuild_status_done": "Reconstrucción completada",
        "rebuild_success_message": "¡Base de conocimiento actualizada con éxito!",
        "runtime_sidebar_hint": "Consejo: añade nuevos archivos locales y luego usa el botón superior para refrescar el índice.",
        # Duration options
        "dur_15s": "15s (Rápido)",
        "dur_30s": "30s (Estándar)",
        "dur_60s": "60s (Inmersivo)",
        "dur_3min": "3min (Profundo)",
        # Platform options
        "plat_tiktok": "TikTok (Internacional)",
        "plat_youtube": "YouTube Shorts",
        "plat_instagram": "Instagram Reels",
        "plat_douyin": "Douyin / WeChat Channels",
        # Input area
        "input_label": "Tema del Guion",
        "input_placeholder": "✍️ Ingresa tu concepto de vídeo, ej: 'Un lanzamiento cyberpunk de 60 segundos para un smartwatch, dirigido a Gen-Z en TikTok...'",
        "btn_generate": "🎬 Generar Guion de Rodaje",
        # Errors & Status
        "error_empty": "⚠️ Por favor, ingresa un tema de vídeo y asegúrate de que la base de datos esté conectada.",
        "status_running": "⚙️ Pipeline Multi-Agente en Ejecución...",
        "status_profiler": ">> 📋 [Agente Perfilador] Cargando perfil de estilo del creador...",
        "status_trend": ">> 🌍 [Cazador de Tendencias] Escaneando tendencias y factores virales...",
        "status_writer": ">> 🎬 [Guionista] Generando guion profesional de rodaje...",
        "status_done": "✅ Guion de Rodaje Generado Exitosamente",
        "status_error": "❌ Error en el Pipeline",
        "output_title": "🎬 Guion Profesional de Rodaje",
        "save_success": "✅ Guion guardado en la base de datos local (app.db)",
        # Gallery
        "section_viral": "🔥 Referencias de videos virales tech",
        "section_viral_subtitle": "Escaneo en vivo con Tavily de publicaciones públicas de {scope} en {country} durante los últimos 3 días. Solo se muestran resultados con señales de más de 1M de vistas.",
        "section_viral_live": "En vivo con Tavily",
        "section_viral_mixed_scope": "TikTok / Instagram / X",
        "section_viral_window": "Últimos 3 días",
        "section_viral_views": "vistas",
        "section_viral_open": "Abrir video",
        "section_viral_refresh": "🔄 Cambiar",
        "section_viral_note": "Las vistas se estiman heurísticamente a partir de fragmentos públicos devueltos por Tavily.",
        "section_viral_empty": "No se detectaron videos públicos recientes de TikTok / Instagram / X con señales de más de 1M de vistas para este mercado.",
        "section_viral_loading": "Escaneando videos públicos recientes...",
        # Templates
        "section_templates": "🎨 Plantillas de Guion Profesional",
        "tpl_1_title": "🖥 Unboxing Tech Plano Largo",
        "tpl_1_sub": "Ideal para: YouTube estilo MKBHD",
        "tpl_2_title": "👟 Bullet-Time Estilo Urbano",
        "tpl_2_sub": "Ideal para: TikTok Lanzamiento de Producto",
        "tpl_3_title": "💫 Cortometraje Conceptual",
        "tpl_3_sub": "Ideal para: Instagram Reels Narrativa",
        "tpl_4_title": "🧬 Del Micro al Cosmos",
        "tpl_4_sub": "Ideal para: Bilibili / YouTube Divulgación",
    },
}

# =====================================================================
# Helper Functions
# =====================================================================
def get_users():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, style_prompt FROM users")
        users = cursor.fetchall()
        conn.close()
        return users
    except:
        return []

def save_script(user_id, topic, platform, duration, creativity, lang, content):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO scripts (user_id, topic, platform, duration, creativity, language, content)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, topic, platform, duration, creativity, lang, content))
        conn.commit()
    except Exception as e:
        print(f"❌ DB Save Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def format_citation(item: dict) -> str:
    source_title = item.get("source_title", "Untitled source")
    country_code = item.get("country_code", "GLOBAL") or "GLOBAL"
    page_num = item.get("page_num", "") or "N/A"
    heading_path = item.get("heading_path", "") or "N/A"
    source_url = item.get("source_url", "") or ""
    source_link = f" · <a href='{html.escape(source_url)}' target='_blank'>source</a>" if source_url else ""
    return (
        f"<span class='citation-chip'>"
        f"{html.escape(source_title)} · {html.escape(country_code)} · p.{html.escape(str(page_num))} · "
        f"{html.escape(str(heading_path))}{source_link}</span>"
    )


def _trend_is_live(state: dict) -> bool:
    trend_sources = state.get("trend_sources", []) or []
    trend_data = str(state.get("trend_data", "") or "")
    return bool(trend_sources) or "[Live Trend Intelligence]" in trend_data


def _get_market_label(country_code: str) -> str:
    for market in MARKETS:
        if market["code"] == country_code:
            return market["label"]
    return country_code


@st.cache_data(ttl=1800, show_spinner=False)
def get_cached_viral_benchmarks(target_platform: str, target_country: str, refresh_token: int = 0) -> list[dict]:
    return search_viral_video_benchmarks(
        platform=target_platform,
        country_label=_get_market_label(target_country),
        days=3,
        max_results=4,
    )


def _extract_trend_summary(trend_data: str) -> str:
    if not trend_data:
        return ""
    for line in trend_data.splitlines():
        if line.startswith("- Summary:"):
            return line.replace("- Summary:", "", 1).strip()

    cleaned_lines = []
    for line in trend_data.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("[") or stripped.startswith("- Market:") or stripped.startswith("- Platform:") or stripped.startswith("- Search Query:"):
            continue
        cleaned_lines.append(stripped.lstrip("- ").strip())
    return " ".join(cleaned_lines[:2]).strip()


def _format_source_domain(url: str) -> str:
    if not url:
        return "unknown"
    try:
        return urlparse(url).netloc.replace("www.", "") or "unknown"
    except Exception:
        return "unknown"


def build_workflow_trace_html(state: dict, t: dict) -> str:
    trend_is_live = _trend_is_live(state)
    trend_label = t.get("workflow_stage_live", "Live") if trend_is_live else t.get("workflow_stage_fallback", "Fallback")
    trend_state_class = "step-live" if trend_is_live else "step-fallback"

    steps = [
        (t.get("workflow_profiler", "Profiler"), t.get("workflow_stage_done", "Done"), "step-done"),
        (t.get("workflow_trend", "Trend Hunter"), trend_label, trend_state_class),
        (t.get("workflow_writer", "Script Writer"), t.get("workflow_stage_done", "Done"), "step-done"),
        (t.get("workflow_scope", "Scope Resolver"), t.get("workflow_stage_done", "Done"), "step-done"),
        (t.get("workflow_retriever", "Compliance Retriever"), t.get("workflow_stage_done", "Done"), "step-done"),
        (t.get("workflow_rules", "Rule Engine"), t.get("workflow_stage_done", "Done"), "step-done"),
        (t.get("workflow_reviewer", "Compliance Reviewer"), t.get("workflow_stage_done", "Done"), "step-done"),
        (t.get("workflow_rewriter", "Compliance Rewriter"), t.get("workflow_stage_done", "Done"), "step-done"),
    ]
    step_html = "".join(
        (
            f'<div class="workflow-step {status_class}">'
            f'<div class="workflow-step-name">{html.escape(name)}</div>'
            f'<div class="workflow-step-badge">{html.escape(status)}</div>'
            f"</div>"
        )
        for name, status, status_class in steps
    )

    return (
        '<div class="workflow-shell">'
        f'<div class="section-title" style="margin-top: 18px;">{html.escape(t.get("output_workflow_title", "🧭 Workflow Trace"))}</div>'
        f'<div class="workflow-subtitle">{html.escape(t.get("workflow_subtitle", ""))}</div>'
        f'<div class="workflow-grid">{step_html}</div>'
        "</div>"
    )


def build_trend_hunter_html(state: dict, t: dict) -> str:
    trend_data = str(state.get("trend_data", "") or "")
    trend_query = str(state.get("trend_query", "") or "")
    trend_sources = state.get("trend_sources", []) or []
    trend_is_live = _trend_is_live(state)
    trend_status = t.get("trend_live_status", "Live Search Active") if trend_is_live else t.get("trend_fallback_status", "Fallback Summary")
    summary = _extract_trend_summary(trend_data) or t.get("trend_preview_empty", "No preview text is available for this source.")

    source_cards = ""
    for item in trend_sources[:5]:
        title = item.get("title", "") or "Untitled source"
        url = item.get("url", "") or ""
        score = item.get("score", "")
        preview = item.get("content", "") or t.get("trend_preview_empty", "No preview text is available for this source.")
        domain = _format_source_domain(url)
        score_label = f"score {float(score):.2f}" if isinstance(score, (int, float)) else ""
        preview_html = html.escape(preview)
        source_cards += (
            '<div class="trend-source-card">'
            f'<a class="trend-source-title" href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">{html.escape(title)}</a>'
            f'<div class="trend-source-meta">{html.escape(domain)}{" · " + html.escape(score_label) if score_label else ""}</div>'
            '<div class="trend-source-tooltip">'
            f'<div class="trend-source-tooltip-label">{html.escape(t.get("trend_preview_label", "Preview"))}</div>'
            f'<div class="trend-source-tooltip-body">{preview_html}</div>'
            "</div>"
            "</div>"
        )

    if not source_cards:
        source_cards = f"<div class='trend-empty'>{html.escape(t.get('trend_no_results', 'No source cards were returned for this search.'))}</div>"

    return (
        '<div class="trend-shell">'
        f'<div class="section-title" style="margin-top: 18px;">{html.escape(t.get("output_trend_title", "🌍 Trend Hunter Signals"))}</div>'
        '<div class="trend-meta-grid">'
        '<div class="trend-meta-card">'
        f'<div class="metric-label">{html.escape(t.get("trend_status_label", "Trend Status"))}</div>'
        f'<div class="metric-value">{html.escape(trend_status)}</div>'
        "</div>"
        '<div class="trend-meta-card">'
        f'<div class="metric-label">{html.escape(t.get("trend_sources_label", "Sources Found"))}</div>'
        f'<div class="metric-value">{html.escape(str(len(trend_sources)))}</div>'
        "</div>"
        "</div>"
        f'<div class="issue-row-label">{html.escape(t.get("trend_query_label", "Search Query"))}</div>'
        f'<div class="trend-query">{html.escape(trend_query or "N/A")}</div>'
        f'<div class="issue-row-label">{html.escape(t.get("trend_summary_label", "Trend Summary"))}</div>'
        f'<div class="trend-summary">{html.escape(summary)}</div>'
        f'<div class="issue-row-label">{html.escape(t.get("trend_results_label", "Matched Results"))}</div>'
        f'<div class="trend-preview-hint">{html.escape(t.get("trend_preview_hint", "Hover over a title to preview the source."))}</div>'
        f'<div class="trend-source-grid">{source_cards}</div>'
        "</div>"
    )


def render_trend_hunter_panel(state: dict, t: dict):
    if not state:
        return

    st.markdown(build_workflow_trace_html(state, t), unsafe_allow_html=True)
    st.markdown(build_trend_hunter_html(state, t), unsafe_allow_html=True)


def build_viral_benchmarks_html(items: list[dict], target_platform: str, target_country: str, t: dict) -> str:
    supported_platforms = {"tiktok", "instagram", "x"}
    platform_labels = {
        "tiktok": t.get("plat_tiktok", "TikTok"),
        "instagram": t.get("plat_instagram", "Instagram Reels"),
        "x": t.get("plat_x", "X"),
    }
    item_platforms = {str(item.get("platform_key", "") or "") for item in items if item.get("platform_key")}
    if target_platform in supported_platforms and item_platforms == {target_platform}:
        scope_label = platform_labels.get(target_platform, target_platform.title())
    elif target_platform in supported_platforms and not item_platforms:
        scope_label = platform_labels.get(target_platform, target_platform.title())
    else:
        scope_label = t.get("section_viral_mixed_scope", "TikTok / Instagram / X")
    subtitle = t.get(
        "section_viral_subtitle",
        "Live Tavily scan of public {scope} posts from the last 3 days in {country}. Only results with 1M+ view signals are shown.",
    ).format(scope=scope_label, country=_get_market_label(target_country))

    if not items:
        cards_html = f"<div class='viral-empty'>{html.escape(t.get('section_viral_empty', 'No recent videos were found.'))}</div>"
    else:
        cards = []
        for item in items:
            image_url = str(item.get("image_url", "") or "").strip()
            title = str(item.get("title", "") or "Untitled video")
            summary = str(item.get("summary", "") or "")
            url = str(item.get("url", "") or "").strip()
            platform = str(item.get("platform", "") or "Platform")
            views_label = f"{item.get('view_count_label', '1.0M')} {t.get('section_viral_views', 'views')}"
            image_block = (
                f"<div class='viral-card-image' style=\"background-image: linear-gradient(180deg, rgba(15,23,42,0.02) 0%, rgba(15,23,42,0.12) 100%), url('{html.escape(image_url, quote=True)}');\"></div>"
                if image_url
                else f"<div class='viral-card-image viral-card-fallback'>{html.escape(platform)}</div>"
            )
            cards.append(
                "<div class='viral-card'>"
                f"<a class='viral-card-media' href='{html.escape(url, quote=True)}' target='_blank' rel='noopener noreferrer'>{image_block}</a>"
                "<div class='viral-card-body'>"
                "<div class='viral-card-topline'>"
                f"<span class='viral-platform-chip'>{html.escape(platform)}</span>"
                f"<span class='viral-views-pill'>{html.escape(views_label)}</span>"
                "</div>"
                f"<a class='viral-card-title' href='{html.escape(url, quote=True)}' target='_blank' rel='noopener noreferrer'>{html.escape(title)}</a>"
                f"<div class='viral-card-summary'>{html.escape(summary)}</div>"
                "<div class='viral-card-meta'>"
                f"<span>{html.escape(t.get('section_viral_window', 'Last 3 days'))}</span>"
                f"<span>·</span><span>{html.escape(t.get('section_viral_open', 'Open video'))}</span>"
                "</div>"
                "</div>"
                "</div>"
            )
        cards_html = "".join(cards)

    return (
        "<div class='viral-shell'>"
        f"<div class='viral-subtitle'>{html.escape(subtitle)}</div>"
        f"<div class='viral-grid'>{cards_html}</div>"
        f"<div class='viral-note'>{html.escape(t.get('section_viral_note', 'View counts are parsed heuristically from public snippets returned by Tavily.'))}</div>"
        "</div>"
    )


def render_viral_benchmarks_section(target_platform: str, target_country: str, t: dict):
    scope_key = f"{target_country}:{target_platform}"
    session_cache = st.session_state.setdefault("viral_benchmark_results", {})
    refresh_tokens = st.session_state.setdefault("viral_benchmark_refresh_tokens", {})

    title_col, button_col = st.columns([6, 1])
    with title_col:
        st.markdown(
            f"<div class='section-title'>{html.escape(t.get('section_viral', '🔥 Viral Tech Video Benchmarks'))}</div>",
            unsafe_allow_html=True,
        )
    with button_col:
        refresh_clicked = st.button(
            t.get("section_viral_refresh", "🔄 Refresh"),
            key=f"viral_refresh_{scope_key}",
            use_container_width=True,
        )

    if refresh_clicked:
        refresh_tokens[scope_key] = int(refresh_tokens.get(scope_key, 0) or 0) + 1
        session_cache.pop(scope_key, None)

    try:
        if scope_key not in session_cache:
            with st.spinner(t.get("section_viral_loading", "Scanning recent public platform videos...")):
                session_cache[scope_key] = get_cached_viral_benchmarks(
                    target_platform,
                    target_country,
                    refresh_tokens.get(scope_key, 0),
                )
        items = session_cache.get(scope_key, [])
    except Exception as exc:
        st.info(f"{t.get('section_viral_empty', 'No recent videos were found.')} ({exc})")
        return

    st.markdown(
        build_viral_benchmarks_html(items, target_platform, target_country, t),
        unsafe_allow_html=True,
    )


def render_compliance_review(report: dict, state: dict, t: dict):
    if not report:
        return

    overall_status = report.get("overall_status", "needs_revision")
    overall_risk = report.get("overall_risk", "medium")
    headline = report.get("headline", "Compliance review")
    overall_commentary = report.get("overall_commentary", "")
    closing_note = report.get("closing_note", "")
    issues = report.get("issues", []) or []
    issue_count = len(issues)

    summary_html = f"""
    <div class="compliance-shell">
        <div class="section-title" style="margin-top: 18px;">{html.escape(t.get("output_compliance_title", "🛡 Compliance Review"))}</div>
        <div class="compliance-grid">
            <div class="compliance-card">
                <div class="metric-label">{html.escape(t.get("compliance_status_label", "Review Status"))}</div>
                <div class="metric-value">{html.escape(overall_status.replace('_', ' ').title())}</div>
            </div>
            <div class="compliance-card">
                <div class="metric-label">{html.escape(t.get("compliance_risk_label", "Risk Level"))}</div>
                <div class="metric-value">{html.escape(overall_risk.title())}</div>
            </div>
            <div class="compliance-card">
                <div class="metric-label">{html.escape(t.get("compliance_market_label", "Market Scope"))}</div>
                <div class="metric-value">{html.escape(str(state.get('target_country', 'GLOBAL')))} / {html.escape(str(state.get('target_platform', 'all')))}</div>
            </div>
            <div class="compliance-card">
                <div class="metric-label">{html.escape(t.get("compliance_evidence_label", "Issues Found"))}</div>
                <div class="metric-value">{html.escape(str(issue_count))}</div>
            </div>
        </div>
        <div class="compliance-headline">{html.escape(headline)}</div>
        <div class="compliance-note">{html.escape(overall_commentary)}</div>
    </div>
    """
    st.markdown(summary_html, unsafe_allow_html=True)

    if not issues:
        st.info(t.get("compliance_no_issues", "No material issues were flagged in the current review."))
    else:
        for index, issue in enumerate(issues, start=1):
            citations = issue.get("citations", []) or []
            citation_html = "".join(format_citation(item) for item in citations) or (
                f"<span class='citation-chip'>{html.escape(t.get('compliance_no_citations', 'No citation available'))}</span>"
            )
            issue_html = f"""
            <div class="issue-card">
                <div class="issue-topline">
                    <div class="issue-index">Issue {index}</div>
                    <div class="risk-pill risk-{html.escape(issue.get('risk_level', 'medium').lower())}">
                        {html.escape(issue.get('risk_level', 'medium').title())}
                    </div>
                </div>
                <div class="issue-row-label">{html.escape(t.get("compliance_script_excerpt", "Quoted Script"))}</div>
                <div class="issue-quote">{html.escape(issue.get("excerpt", "No excerpt provided"))}</div>
                <div class="issue-row-label">{html.escape(t.get("compliance_reason", "Risk Analysis"))}</div>
                <div class="issue-copy">{html.escape(issue.get("reason", "No reason provided"))}</div>
                <div class="issue-row-label">{html.escape(t.get("compliance_fix", "Revision Suggestion"))}</div>
                <div class="issue-copy">{html.escape(issue.get("suggested_fix", "No suggestion provided"))}</div>
                <div class="issue-row-label">{html.escape(t.get("compliance_citations", "Supporting Citations"))}</div>
                <div class="citation-wrap">{citation_html}</div>
            </div>
            """
            st.markdown(issue_html, unsafe_allow_html=True)

    if closing_note:
        st.markdown(
            f"""
            <div class="compliance-shell" style="margin-top: 16px;">
                <div class="issue-row-label">{html.escape(t.get("compliance_closing", "Overall Commentary"))}</div>
                <div class="compliance-note">{html.escape(closing_note)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_approved_script(original_script: str, approved_script: str, t: dict):
    if not approved_script.strip():
        return
    if approved_script.strip() == original_script.strip():
        return

    st.markdown(
        f"<div class='section-title'>{html.escape(t.get('approved_script_title', '✅ Recommended Revision'))}</div>",
        unsafe_allow_html=True,
    )
    with st.container(border=False):
        st.markdown("<div class='script-output'>", unsafe_allow_html=True)
        st.markdown(approved_script)
        st.markdown("</div>", unsafe_allow_html=True)


def render_script_model_badge(state: dict, t: dict):
    provider = str(state.get("script_model_provider", "") or "").strip()
    model_name = str(state.get("script_model_name", "") or "").strip()
    fallback_used = bool(state.get("script_model_fallback_used", False))
    if not provider:
        return

    provider_label = provider.title()
    badge = f"{t.get('script_model_badge', 'Model Used')}: {provider_label}"
    if model_name:
        badge += f" · {model_name}"
    if fallback_used:
        badge += f" · {t.get('script_model_fallback', 'Fallback')}"
    st.caption(badge)


class ComplianceRuntimeController:
    def __init__(self):
        self._lock = threading.RLock()
        self._runtime_status: dict | None = None

    def _merge_with_live(self, runtime_status: dict | None = None) -> dict:
        live_status = get_knowledge_index_status()
        merged = dict(runtime_status or {})
        merged.update(live_status)
        if not merged.get("embedding_backend"):
            merged["embedding_backend"] = (runtime_status or {}).get("model_name", "unknown")
        if runtime_status is not None:
            self._runtime_status = dict(merged)
        return merged

    def ensure_initialized(self, progress_callback=None) -> dict:
        with self._lock:
            if self._runtime_status is not None:
                return self._merge_with_live(self._runtime_status)
            status = initialize_knowledge_runtime(progress_callback=progress_callback)
            return self._merge_with_live(status)

    def normalize_and_rebuild(self, normalize_callback=None, rebuild_callback=None) -> dict:
        with self._lock:
            normalize_raw_knowledge_files(progress_callback=normalize_callback)
            status = rebuild_knowledge_runtime(progress_callback=rebuild_callback)
            return self._merge_with_live(status)

    def reset(self) -> None:
        with self._lock:
            self._runtime_status = None


@st.cache_resource(show_spinner=False)
def get_compliance_runtime_controller():
    return ComplianceRuntimeController()


def safe_status_update(status_box, **kwargs):
    try:
        if hasattr(status_box, "update"):
            status_box.update(**kwargs)
    except Exception:
        return


def format_health_timestamp(value: str) -> str:
    if not value:
        return ""
    try:
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
    except Exception:
        return value


def get_live_runtime_health(runtime_status: dict | None = None) -> dict:
    controller = get_compliance_runtime_controller()
    return controller._merge_with_live(runtime_status)


def render_sidebar_health_card(health_status: dict, t: dict):
    status_value = str(health_status.get("status", "unknown")).lower()
    status_map = {
        "ready": (
            "✅",
            t.get("health_ready_title", "系统健康 (Ready)"),
            t.get("health_ready_body", "多语种检索运行正常，当前索引可直接用于合规审查。"),
        ),
        "empty": (
            "⚠️",
            t.get("health_empty_title", "知识库为空 (Empty)"),
            t.get("health_empty_body", "索引已初始化，但还没有可用的法规或平台文档。"),
        ),
        "missing": (
            "🛠️",
            t.get("health_missing_title", "等待初始化 (Missing)"),
            t.get("health_missing_body", "还没有检测到本地索引，系统会在需要时自动构建。"),
        ),
    }
    icon, title, subtitle = status_map.get(
        status_value,
        (
            "ℹ️",
            t.get("health_unknown_title", "状态待确认 (Unknown)"),
            t.get("health_unknown_body", "运行时状态已加载，但后端还没有返回完整健康信息。"),
        ),
    )

    model_name = health_status.get("embedding_backend") or health_status.get("model_name") or "unknown"
    documents = int(health_status.get("documents", 0) or 0)
    chunks = int(health_status.get("chunks", 0) or 0)
    built_at = format_health_timestamp(str(health_status.get("built_at", "")))

    with st.container(border=True):
        st.markdown(f"**{t.get('health_card_title', 'Compliance Runtime Health')}**")
        st.caption(t.get("health_card_subtitle", "Local Qdrant index and multilingual embedding status"))
        st.markdown(f"### {icon} {title}")
        st.caption(subtitle)

        st.markdown(f"**{t.get('health_model_label', 'Current Model')}**")
        st.caption(str(model_name))

        metric_col1, metric_col2 = st.columns(2)
        metric_col1.metric(t.get("health_docs_label", "Documents"), documents)
        metric_col2.metric(t.get("health_chunks_label", "Chunks"), chunks)

        if built_at:
            st.caption(f"{t.get('health_built_at', 'Last built')}: {built_at}")


def run_sidebar_kb_rebuild(t: dict):
    controller = get_compliance_runtime_controller()
    if not st.button(
        t.get("rebuild_button", "🔄 更新/重建知识库"),
        type="primary",
        use_container_width=True,
    ):
        return

    controller.reset()
    st.session_state.pop("compliance_runtime_status", None)

    progress = st.progress(
        0,
        text=t.get("rebuild_progress_start", "Scanning local knowledge files and preparing rebuild..."),
    )
    status_box = st.status(
        t.get("rebuild_status_title", "Rebuilding multilingual compliance knowledge base"),
        expanded=True,
    )
    seen_messages = set()

    def progress_callback(stage: str, message: str, ratio: float | None):
        if ratio is not None:
            bounded = max(0.0, min(1.0, ratio))
            progress.progress(int(bounded * 100), text=message)
        if message not in seen_messages:
            if hasattr(status_box, "write"):
                status_box.write(message)
            else:
                st.write(message)
            seen_messages.add(message)

    def phase_callback(start: float, end: float):
        def _inner(stage: str, message: str, ratio: float | None):
            scaled = None
            if ratio is not None:
                bounded = max(0.0, min(1.0, ratio))
                scaled = start + (end - start) * bounded
            progress_callback(stage, message, scaled)

        return _inner

    progress_callback(
        "rebuild_start",
        t.get("rebuild_progress_check", "Checking model files and rebuilding the local Qdrant index..."),
        0.01,
    )

    try:
        runtime_status = controller.normalize_and_rebuild(
            normalize_callback=phase_callback(0.02, 0.18),
            rebuild_callback=phase_callback(0.18, 1.0),
        )
    except Exception as exc:
        safe_status_update(
            status_box,
            label=t.get("rebuild_status_error", "Knowledge base rebuild failed"),
            state="error",
            expanded=True,
        )
        progress.empty()
        st.error(
            t.get(
                "rebuild_error_message",
                f"Knowledge base rebuild failed: {exc}",
            )
        )
        return

    progress_callback(
        "rebuild_done",
        t.get(
            "rebuild_progress_done",
            f"Knowledge base updated · {runtime_status.get('documents', 0)} docs · {runtime_status.get('chunks', 0)} chunks",
        ),
        1.0,
    )
    safe_status_update(
        status_box,
        label=t.get("rebuild_status_done", "Knowledge base rebuild complete"),
        state="complete",
        expanded=False,
    )
    progress.empty()

    st.session_state["compliance_runtime_status"] = runtime_status
    st.session_state["knowledge_rebuild_notice"] = t.get("rebuild_success_message", "知识库更新成功！")
    get_compliance_runtime_controller.clear()
    st.rerun()


def ensure_compliance_runtime_ui(t: dict) -> dict:
    cached_status = st.session_state.get("compliance_runtime_status")
    if cached_status:
        refreshed_status = get_live_runtime_health(cached_status)
        if str(refreshed_status.get("status", "")).lower() != "missing":
            st.session_state["compliance_runtime_status"] = refreshed_status
            return refreshed_status

    progress = st.progress(
        0,
        text=t.get("runtime_progress_start", "Preparing the compliance runtime..."),
    )
    status_box = st.status(
        t.get("runtime_status_title", "Preparing multilingual compliance retrieval"),
        expanded=True,
    )
    seen_messages = set()

    def progress_callback(stage: str, message: str, ratio: float | None):
        if ratio is not None:
            bounded = max(0.0, min(1.0, ratio))
            progress.progress(int(bounded * 100), text=message)
        if message not in seen_messages:
            if hasattr(status_box, "write"):
                status_box.write(message)
            else:
                st.write(message)
            seen_messages.add(message)

    progress_callback(
        "startup",
        t.get("runtime_progress_check", "Checking cached model and Qdrant index..."),
        0.01,
    )

    try:
        runtime_status = get_compliance_runtime_controller().ensure_initialized(
            progress_callback=progress_callback
        )
    except Exception as exc:
        safe_status_update(
            status_box,
            label=t.get("runtime_status_error", "Compliance runtime initialization failed"),
            state="error",
            expanded=True,
        )
        progress.empty()
        st.error(
            t.get(
                "runtime_error_message",
                f"Failed to prepare the compliance runtime: {exc}",
            )
        )
        st.stop()

    progress_callback(
        "startup_done",
        t.get(
            "runtime_progress_ready",
            f"Compliance runtime ready · {runtime_status.get('documents', 0)} docs · {runtime_status.get('chunks', 0)} chunks",
        ),
        1.0,
    )
    safe_status_update(
        status_box,
        label=t.get("runtime_status_done", "Compliance runtime ready"),
        state="complete",
        expanded=False,
    )
    progress.empty()
    st.session_state["compliance_runtime_status"] = runtime_status
    return runtime_status

# =====================================================================
# 1. PAGE CONFIG & SESSION STATE
# =====================================================================
if 'ui_lang' not in st.session_state:
    st.session_state.ui_lang = 'en'

st.set_page_config(
    page_title=UI_STRINGS[st.session_state.ui_lang]["page_title"],
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    selected_lang_name = st.selectbox(
        UI_STRINGS[st.session_state.ui_lang]["sidebar_lang_label"],
        list(LANG_OPTIONS.keys()),
        index=list(LANG_OPTIONS.values()).index(st.session_state.ui_lang),
        key="ui_lang_selector",
    )

selected_ui_lang = LANG_OPTIONS[selected_lang_name]
if selected_ui_lang != st.session_state.ui_lang:
    st.session_state.ui_lang = selected_ui_lang
    st.rerun()

t = UI_STRINGS[st.session_state.ui_lang]
runtime_status = ensure_compliance_runtime_ui(t)
health_status = get_live_runtime_health(runtime_status)

# =====================================================================
# 2. CSS
# =====================================================================
st.markdown("""
<style>
/* Reset and Edge-to-Edge Layout */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1440px !important;
}
.stApp {
    background-color: #000000;
    color: #ffffff;
}

/* Hide defaults — but preserve sidebar toggle button */
header[data-testid="stHeader"] {
    background: transparent !important;
    backdrop-filter: none !important;
}
footer {visibility: hidden;}

/* Sidebar Toggle Button — ALWAYS visible and clickable */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"] {
    visibility: visible !important;
    display: flex !important;
    color: #FFFFFF !important;
    background-color: rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px;
    z-index: 9999 !important;
    opacity: 1 !important;
}
[data-testid="stSidebarCollapseButton"]:hover,
[data-testid="collapsedControl"]:hover {
    background-color: #3B82F6 !important;
}
[data-testid="stSidebarCollapseButton"] svg,
[data-testid="collapsedControl"] svg {
    fill: #FFFFFF !important;
    stroke: #FFFFFF !important;
}

/* Typography */
h1, h2, h3, h4 {
    font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* Title gradient */
.title-glow {
    text-align: center;
    font-size: 60px;
    font-weight: 900;
    margin-bottom: 10px;
    background: linear-gradient(90deg, #0EA5E9, #6366F1, #A855F7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.title-badge {
    text-align: center;
    display: inline-block;
    width: 100%;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: #0EA5E9;
    margin-bottom: 8px;
}
.subtitle {
    text-align: center;
    font-size: 18px;
    color: #888888;
    margin-bottom: 40px;
}

/* Button style */
.stButton>button {
    background: linear-gradient(90deg, #0EA5E9, #6366F1);
    color: white;
    border: none;
    height: 56px;
    border-radius: 28px;
    font-size: 20px;
    font-weight: bold;
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
    transition: all 0.3s ease;
    width: 100%;
    margin-top: 10px;
}
.stButton>button:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 8px 30px rgba(99, 102, 241, 0.8);
    background: linear-gradient(90deg, #38BDF8, #818CF8);
}
.stButton>button>div>p {
    font-size: 18px !important;
}

/* Text area — dark text on light background for max visibility */
.stTextArea textarea {
    color: #1E1E1E !important;
    background-color: #F8F9FB !important;
    -webkit-text-fill-color: #1E1E1E !important;
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 20px;
    font-size: 16px;
    padding: 20px;
    transition: all 0.2s;
}
.stTextArea textarea:focus {
    border-color: #6366F1;
    box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);
}
.stTextArea label {
    display: none;
}

/* Text input — dark text on light background */
.stTextInput input {
    color: #1E1E1E !important;
    background-color: #F8F9FB !important;
    -webkit-text-fill-color: #1E1E1E !important;
}

/* Ensure widget labels are bright white on the dark page */
.stWidgetLabel p {
    color: #FFFFFF !important;
    font-weight: 600;
}

/* Placeholder text */
::placeholder {
    color: #6B7280 !important;
    opacity: 0.8;
}

/* Hero banner */
.hero-gif {
    width: 100%;
    height: 420px;
    object-fit: cover;
    border-radius: 24px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.8);
    margin-top: 30px;
    margin-bottom: 50px;
    border: 1px solid rgba(255,255,255,0.08);
}

/* Section titles */
.section-title {
    font-size: 28px;
    font-weight: 800;
    margin-top: 60px;
    margin-bottom: 24px;
    color: #ffffff;
}

/* Gallery captions */
.gallery-caption {
    font-size: 14px;
    color: #bbbbbb;
    margin-top: 10px;
    text-align: center;
    font-weight: 500;
}

/* Script output table styling */
.script-output {
    background: rgba(14, 165, 233, 0.04);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 16px;
    padding: 24px;
}
.script-output table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}
.script-output th {
    background: rgba(99, 102, 241, 0.2);
    color: #A5B4FC;
    padding: 10px 14px;
    text-align: left;
    border: 1px solid rgba(99, 102, 241, 0.25);
    font-weight: 700;
    letter-spacing: 0.5px;
}
.script-output td {
    padding: 10px 14px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    vertical-align: top;
    line-height: 1.6;
    color: #e2e8f0;
}
.script-output tr:hover td {
    background: rgba(99, 102, 241, 0.06);
}

.workflow-shell,
.trend-shell,
.compliance-shell {
    background: rgba(14, 165, 233, 0.04);
    border: 1px solid rgba(56, 189, 248, 0.18);
    border-radius: 18px;
    padding: 22px;
}
.workflow-subtitle {
    color: #94A3B8;
    line-height: 1.7;
    margin-bottom: 16px;
}
.workflow-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
}
.workflow-step {
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 14px;
    padding: 14px;
    min-height: 92px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.workflow-step-name {
    font-size: 14px;
    font-weight: 700;
    color: #F8FAFC;
    line-height: 1.5;
}
.workflow-step-badge {
    width: fit-content;
    border-radius: 999px;
    padding: 6px 10px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.step-done .workflow-step-badge {
    background: rgba(34, 197, 94, 0.16);
    color: #86EFAC;
}
.step-live .workflow-step-badge {
    background: rgba(56, 189, 248, 0.16);
    color: #7DD3FC;
}
.step-fallback .workflow-step-badge {
    background: rgba(245, 158, 11, 0.16);
    color: #FCD34D;
}
.compliance-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
    margin-bottom: 18px;
}
.compliance-card {
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 14px;
    padding: 14px;
}
.metric-label {
    font-size: 12px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #94A3B8;
    margin-bottom: 8px;
}
.metric-value {
    font-size: 18px;
    font-weight: 800;
    color: #F8FAFC;
}
.compliance-headline {
    font-size: 24px;
    font-weight: 800;
    color: #E0F2FE;
    margin-bottom: 10px;
}
.compliance-note {
    color: #CBD5E1;
    line-height: 1.7;
}
.trend-meta-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
    margin-bottom: 18px;
}
.trend-meta-card {
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 14px;
    padding: 14px;
}
.trend-query,
.trend-summary {
    color: #CBD5E1;
    line-height: 1.8;
    word-break: break-word;
}
.trend-preview-hint {
    color: #7DD3FC;
    margin-top: 4px;
    margin-bottom: 12px;
    font-size: 13px;
}
.trend-source-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}
.trend-source-card {
    position: relative;
    background: rgba(15, 23, 42, 0.86);
    border: 1px solid rgba(99, 102, 241, 0.18);
    border-radius: 16px;
    padding: 16px;
    min-height: 108px;
}
.trend-source-title {
    color: #E0F2FE;
    font-size: 15px;
    font-weight: 700;
    text-decoration: none;
    line-height: 1.6;
}
.trend-source-title:hover {
    color: #7DD3FC;
}
.trend-source-meta {
    color: #94A3B8;
    font-size: 12px;
    margin-top: 8px;
    letter-spacing: 0.03em;
}
.trend-source-tooltip {
    position: absolute;
    left: 16px;
    right: 16px;
    top: calc(100% + 10px);
    z-index: 20;
    opacity: 0;
    transform: translateY(8px);
    pointer-events: none;
    transition: opacity 0.18s ease, transform 0.18s ease;
    background: #0B1120;
    border: 1px solid rgba(56, 189, 248, 0.22);
    border-radius: 14px;
    box-shadow: 0 18px 40px rgba(2, 6, 23, 0.8);
    padding: 14px;
}
.trend-source-card:hover .trend-source-tooltip {
    opacity: 1;
    transform: translateY(0);
}
.trend-source-tooltip-label {
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #7DD3FC;
    margin-bottom: 8px;
}
.trend-source-tooltip-body {
    color: #E2E8F0;
    font-size: 13px;
    line-height: 1.7;
}
.trend-empty {
    background: rgba(15, 23, 42, 0.72);
    border: 1px dashed rgba(148, 163, 184, 0.2);
    border-radius: 14px;
    padding: 16px;
    color: #CBD5E1;
}
.viral-shell {
    background: rgba(14, 165, 233, 0.04);
    border: 1px solid rgba(56, 189, 248, 0.18);
    border-radius: 18px;
    padding: 22px;
}
.viral-subtitle {
    color: #94A3B8;
    line-height: 1.7;
    margin-bottom: 18px;
}
.viral-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 18px;
}
.viral-card {
    overflow: hidden;
    background: rgba(15, 23, 42, 0.82);
    border: 1px solid rgba(99, 102, 241, 0.18);
    border-radius: 18px;
    transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}
.viral-card:hover {
    transform: translateY(-3px);
    border-color: rgba(56, 189, 248, 0.4);
    box-shadow: 0 18px 30px rgba(2, 6, 23, 0.5);
}
.viral-card-media {
    display: block;
    text-decoration: none;
}
.viral-card-image {
    display: block;
    width: 100%;
    height: 220px;
    background-color: #111827;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}
.viral-card-fallback {
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(14, 165, 233, 0.28), rgba(99, 102, 241, 0.28));
    color: #E0F2FE;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 0.04em;
}
.viral-card-body {
    padding: 16px;
}
.viral-card-topline {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
}
.viral-platform-chip {
    border-radius: 999px;
    padding: 6px 10px;
    background: rgba(56, 189, 248, 0.12);
    color: #BAE6FD;
    font-size: 12px;
    font-weight: 700;
}
.viral-views-pill {
    color: #E5E7EB;
    font-size: 12px;
    font-weight: 700;
}
.viral-shell a.viral-card-title,
.viral-shell a.viral-card-title:link,
.viral-shell a.viral-card-title:visited {
    display: block;
    color: #F8FAFC !important;
    font-size: 22px;
    font-weight: 800;
    line-height: 1.35;
    text-decoration: none !important;
    margin-bottom: 10px;
}
.viral-shell a.viral-card-title:hover {
    color: #7DD3FC !important;
    text-decoration: none !important;
}
.viral-card-summary {
    color: #CBD5E1;
    font-size: 14px;
    line-height: 1.7;
    min-height: 72px;
}
.viral-card-meta {
    margin-top: 14px;
    color: #94A3B8;
    font-size: 12px;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    align-items: center;
}
.viral-note {
    color: #64748B;
    font-size: 12px;
    margin-top: 16px;
    line-height: 1.7;
}
.viral-empty {
    background: rgba(15, 23, 42, 0.72);
    border: 1px dashed rgba(148, 163, 184, 0.2);
    border-radius: 14px;
    padding: 18px;
    color: #CBD5E1;
}
.issue-card {
    margin-top: 16px;
    background: rgba(15, 23, 42, 0.86);
    border: 1px solid rgba(99, 102, 241, 0.18);
    border-radius: 18px;
    padding: 20px;
}
.issue-topline {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin-bottom: 14px;
}
.issue-index {
    font-size: 14px;
    font-weight: 700;
    color: #A5B4FC;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.risk-pill {
    border-radius: 999px;
    padding: 6px 10px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.risk-high {
    background: rgba(239, 68, 68, 0.18);
    color: #FCA5A5;
}
.risk-medium {
    background: rgba(245, 158, 11, 0.18);
    color: #FCD34D;
}
.risk-low {
    background: rgba(34, 197, 94, 0.18);
    color: #86EFAC;
}
.issue-row-label {
    font-size: 12px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #7DD3FC;
    margin-top: 14px;
    margin-bottom: 8px;
}
.issue-quote {
    background: rgba(148, 163, 184, 0.08);
    border-left: 3px solid rgba(56, 189, 248, 0.75);
    padding: 12px 14px;
    border-radius: 0 12px 12px 0;
    color: #F8FAFC;
    line-height: 1.7;
}
.issue-copy {
    color: #CBD5E1;
    line-height: 1.7;
}
.citation-wrap {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 6px;
}
.citation-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 10px;
    border-radius: 999px;
    background: rgba(56, 189, 248, 0.12);
    border: 1px solid rgba(56, 189, 248, 0.15);
    color: #BAE6FD;
    font-size: 12px;
}
.citation-chip a {
    color: #E0F2FE;
    text-decoration: none;
}

@media (max-width: 1024px) {
    .workflow-grid,
    .compliance-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .viral-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .trend-source-grid {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 640px) {
    .workflow-grid,
    .compliance-grid {
        grid-template-columns: 1fr;
    }
    .viral-grid {
        grid-template-columns: 1fr;
    }
    .trend-meta-grid {
        grid-template-columns: 1fr;
    }
    .trend-source-tooltip {
        position: static;
        opacity: 1;
        transform: none;
        pointer-events: auto;
        margin-top: 12px;
    }
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #0a0a0f;
    border-right: 1px solid #1a1a2e;
}
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 3. SIDEBAR
# =====================================================================
with st.sidebar:
    render_sidebar_health_card(health_status, t)
    notice = st.session_state.pop("knowledge_rebuild_notice", None)
    if notice:
        st.success(notice)
    run_sidebar_kb_rebuild(t)
    st.markdown("---")

    st.markdown(t["sidebar_settings"])
    st.markdown("---")

    st.markdown(t["section_creator"])
    users = get_users()
    user_dict = {f"ID:{u[0]} - {u[1]}": u for u in users} if users else {}
    selected_name = st.selectbox(
        t["select_creator"],
        list(user_dict.keys()) if user_dict else [t["db_not_connected"]],
    )

    st.markdown(t["section_localization"])
    target_languages = st.multiselect(
        t["output_languages"],
        [
            "中文 (Chinese)",
            "English",
            "Español (Spanish)",
            "Português (Portuguese)",
            "Français (French)",
            "Deutsch (German)",
            "العربية (Arabic)",
            "日本語 (Japanese)",
        ],
        default=["English"],
    )

    st.markdown(t["section_distribution"])
    market_options = [market["code"] for market in MARKETS]
    market_labels = {
        market["code"]: f"{market['label']} ({market['code']})"
        for market in MARKETS
    }
    target_country = st.selectbox(
        t.get("target_market", "Target Market:"),
        market_options,
        format_func=lambda code: market_labels[code],
        index=0,
    )
    target_region_pack = get_region_for_country(target_country)
    st.caption(f"{t.get('target_region_pack', 'Region Pack')}: {target_region_pack}")

    platform_labels = {
        "tiktok": t["plat_tiktok"],
        "youtube": t["plat_youtube"],
        "instagram": t["plat_instagram"],
        "x": t.get("plat_x", "X / Twitter"),
        "reddit": t.get("plat_reddit", "Reddit"),
        "discord": t.get("plat_discord", "Discord"),
        "douyin": t["plat_douyin"],
    }
    target_platform = st.selectbox(
        t["target_platform"],
        list(platform_labels.keys()),
        format_func=lambda key: platform_labels[key],
    )

    distribution_labels = {
        "organic": t.get("mode_organic", "Organic Post"),
        "branded_content": t.get("mode_branded", "Branded Content"),
        "paid_ads": t.get("mode_paid", "Paid Ads"),
    }
    distribution_mode = st.selectbox(
        t.get("distribution_mode", "Distribution Mode:"),
        list(distribution_labels.keys()),
        format_func=lambda key: distribution_labels[key],
        index=1,
    )

    product_labels = {
        "general": t.get("cat_general", "General Merchandise"),
        "beauty": t.get("cat_beauty", "Beauty & Personal Care"),
        "electronics": t.get("cat_electronics", "Electronics"),
        "fashion": t.get("cat_fashion", "Fashion"),
        "food_beverage": t.get("cat_food", "Food & Beverage"),
        "health_supplement": t.get("cat_health", "Health / Supplement"),
    }
    product_category = st.selectbox(
        t.get("product_category", "Product Category:"),
        list(product_labels.keys()),
        format_func=lambda key: product_labels[key],
    )

    brand_id = st.text_input(t.get("brand_id", "Brand ID:"), value="default")

    duration_options = [t["dur_15s"], t["dur_30s"], t["dur_60s"], t["dur_3min"]]
    video_duration = st.select_slider(
        t["video_duration"],
        options=duration_options,
        value=t["dur_60s"],
    )

    st.markdown(t["section_ai_params"])
    creativity = st.slider(t["creativity_label"], 0.1, 1.0, 0.8, 0.1, help=t["creativity_help"])
    st.markdown("---")
    st.caption(t["powered_by"])
    st.caption(t.get("runtime_sidebar_hint", "Tip: add new knowledge files locally, then click the rebuild button above to refresh the index."))

# =====================================================================
# 4. HERO & MAIN UI
# =====================================================================
st.markdown(f"<div class='title-badge'>{t['title_badge']}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='title-glow'>{t['title_main']}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='subtitle'>{t['subtitle']}</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 8, 1])
with col2:
    topic = st.text_area(
        t["input_label"],
        placeholder=t["input_placeholder"],
        height=130,
    )

    btn_col1, btn_col2, btn_col3 = st.columns([1, 1.5, 1])
    with btn_col2:
        generate_btn = st.button(t["btn_generate"])

# =====================================================================
# 5. WORKFLOW PROCESSING & OUTPUT
# =====================================================================
if generate_btn:
    if not topic.strip() or not user_dict:
        st.error(t["error_empty"])
    else:
        st.markdown("---")
        selected_user_id = user_dict[selected_name][0]
        final_state = {}
        compliance_report = None

        with st.status(t["status_running"], expanded=True) as status:
            st.write(t["status_profiler"])
            st.write(t["status_trend"])
            st.write(f"{t['status_writer']}\n   🎯 {t['target_platform']}: {platform_labels[target_platform]} | "
                     f"{t['video_duration']}: {video_duration}")
            st.write(t.get("status_scope", ">> 🧭 [Compliance Scope] Resolving platform, market, and language scope..."))
            st.write(t.get("status_retriever", ">> 📚 [Compliance Retriever] Querying Qdrant and scoped evidence blocks..."))
            st.write(t.get("status_rules", ">> 🧪 [Rule Engine] Checking disclosure, risky wording, and unsupported claims..."))
            st.write(t.get("status_reviewer", ">> 🛡️ [Compliance Reviewer] Synthesizing evidence, rule hits, and revisions..."))
            st.write(t.get("status_rewriter", ">> ✍️ [Compliance Rewriter] Drafting a safer revised script when needed..."))

            try:
                app_workflow = build_workflow()
                initial_state = {
                    "user_id": selected_user_id,
                    "topic": topic,
                    "target_languages": target_languages,
                    "video_duration": video_duration,
                    "target_platform": target_platform,
                    "target_country": target_country,
                    "target_region_pack": target_region_pack,
                    "distribution_mode": distribution_mode,
                    "product_category": product_category,
                    "brand_id": brand_id,
                    "creativity": creativity,
                }

                final_state = app_workflow.invoke(initial_state)
                final_script = final_state.get("final_script", "Script generation failed.")
                approved_script = final_state.get("approved_script", final_script)
                compliance_report = final_state.get("compliance_report")

                status.update(label=t["status_done"], state="complete", expanded=False)
                
                # Determine comma-separated string of saved languages
                saved_lang = ", ".join(target_languages) if target_languages else "English"
                save_script(selected_user_id, topic, target_platform, video_duration, creativity, saved_lang, final_script)

            except Exception as e:
                status.update(label=t["status_error"], state="error", expanded=True)
                st.error(f"DEBUG: {e}")
                final_script = None
                approved_script = None
                compliance_report = None

        if final_script:
            render_trend_hunter_panel(final_state, t)
            st.markdown(f"<div class='section-title'>{t['output_title']}</div>", unsafe_allow_html=True)
            render_script_model_badge(final_state, t)
            with st.container(border=False):
                st.markdown("<div class='script-output'>", unsafe_allow_html=True)
                st.markdown(final_script)
                st.markdown("</div>", unsafe_allow_html=True)
            render_compliance_review(compliance_report or {}, final_state, t)
            render_approved_script(final_script, approved_script or "", t)
            st.success(t["save_success"])
            st.stop()

# =====================================================================
# 6. HERO GIF
# =====================================================================
st.markdown("""
<img src="https://media.tenor.com/_qX4Jk316VMAAAAC/cyberpunk.gif" class="hero-gif" alt="Pro-Script AI Hero">
""", unsafe_allow_html=True)

# =====================================================================
# 7. Viral Reference Gallery
# =====================================================================
render_viral_benchmarks_section(target_platform, target_country, t)

# =====================================================================
# 8. Pro Templates
# =====================================================================
st.markdown(f"<div class='section-title'>{t['section_templates']}</div>", unsafe_allow_html=True)
tcol1, tcol2, tcol3, tcol4 = st.columns(4)

with tcol1:
    st.image("https://images.unsplash.com/photo-1531297122539-5692f69f41b3?auto=format&fit=crop&w=400&q=80", width="stretch")
    st.markdown(f"**{t['tpl_1_title']}**<br/><span style='color:gray; font-size:13px'>{t['tpl_1_sub']}</span>", unsafe_allow_html=True)

with tcol2:
    st.image("https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=400&q=80", width="stretch")
    st.markdown(f"**{t['tpl_2_title']}**<br/><span style='color:gray; font-size:13px'>{t['tpl_2_sub']}</span>", unsafe_allow_html=True)

with tcol3:
    st.image("https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=400&q=80", width="stretch")
    st.markdown(f"**{t['tpl_3_title']}**<br/><span style='color:gray; font-size:13px'>{t['tpl_3_sub']}</span>", unsafe_allow_html=True)

with tcol4:
    st.image("https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=400&q=80", width="stretch")
    st.markdown(f"**{t['tpl_4_title']}**<br/><span style='color:gray; font-size:13px'>{t['tpl_4_sub']}</span>", unsafe_allow_html=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)
