# app.py
import streamlit as st
import sqlite3
import os
from core.workflow import build_workflow

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'app.db')

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
        "powered_by": "🚀 Powered by LangGraph + DeepSeek V3",
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
        "section_viral": "🔥 Platform Viral Benchmarks",
        "gallery_1": "「Cyberpunk Cat」▶ 9.8M Views — TikTok",
        "gallery_2": "「Neon City Retro」▶ 12.1M Views — YouTube Shorts",
        "gallery_3": "「AI Epoch」▶ 15.6M Views — Instagram Reels",
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
        "powered_by": "🚀 由 LangGraph + DeepSeek V3 驱动",
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
        "section_viral": "🔥 全球爆款视频参考",
        "gallery_1": "「赛博朋克猫」▶ 980万播放 — TikTok",
        "gallery_2": "「霓虹复古城市」▶ 1210万播放 — YouTube Shorts",
        "gallery_3": "「AI 纪元」▶ 1560万播放 — Instagram Reels",
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
        "powered_by": "🚀 Impulsado por LangGraph + DeepSeek V3",
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
        "section_viral": "🔥 Referencias Virales de Plataformas",
        "gallery_1": "「Cyberpunk Cat」▶ 9.8M Vistas — TikTok",
        "gallery_2": "「Neon City Retro」▶ 12.1M Vistas — YouTube Shorts",
        "gallery_3": "「AI Epoch」▶ 15.6M Vistas — Instagram Reels",
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

# =====================================================================
# 1. PAGE CONFIG & SESSION STATE
# =====================================================================
if 'ui_lang' not in st.session_state:
    st.session_state.ui_lang = 'en'

st.set_page_config(page_title="增强脚本生成AI | Shooting Script Generator", page_icon="🎬", layout="wide", initial_sidebar_state="expanded")
# Shorthand: current language strings
t = UI_STRINGS[st.session_state.ui_lang]

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
    # --- Language Switcher (top of sidebar) ---
    lang_options = {"简体中文": "zh", "English": "en", "Español": "es"}
    selected_lang_name = st.selectbox(
        t["sidebar_lang_label"],
        list(lang_options.keys()),
        index=list(lang_options.values()).index(st.session_state.ui_lang),
    )
    st.session_state.ui_lang = lang_options[selected_lang_name]
    # Refresh shorthand after potential change
    t = UI_STRINGS[st.session_state.ui_lang]

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
        ["中文 (Chinese)", "English", "Español (Spanish)", "Français (French)", "العربية (Arabic)", "日本語 (Japanese)"],
        default=["中文 (Chinese)", "English"],
    )

    st.markdown(t["section_distribution"])
    platform_options = [t["plat_tiktok"], t["plat_youtube"], t["plat_instagram"], t["plat_douyin"]]
    target_platform = st.selectbox(t["target_platform"], platform_options)

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

        with st.status(t["status_running"], expanded=True) as status:
            st.write(t["status_profiler"])
            st.write(t["status_trend"])
            st.write(f"{t['status_writer']}\n   🎯 {t['target_platform']}: {target_platform} | "
                     f"{t['video_duration']}: {video_duration}")

            try:
                app_workflow = build_workflow()
                initial_state = {
                    "user_id": selected_user_id,
                    "topic": topic,
                    "target_languages": target_languages,
                    "video_duration": video_duration,
                    "target_platform": target_platform,
                    "creativity": creativity,
                }

                final_state = app_workflow.invoke(initial_state)
                final_script = final_state.get("final_script", "Script generation failed.")

                status.update(label=t["status_done"], state="complete", expanded=False)
                
                # Determine comma-separated string of saved languages
                saved_lang = ", ".join(target_languages) if target_languages else "English"
                save_script(selected_user_id, topic, target_platform, video_duration, creativity, saved_lang, final_script)

            except Exception as e:
                status.update(label=t["status_error"], state="error", expanded=True)
                st.error(f"DEBUG: {e}")
                final_script = None

        if final_script:
            st.markdown(f"<div class='section-title'>{t['output_title']}</div>", unsafe_allow_html=True)
            with st.container(border=False):
                st.markdown("<div class='script-output'>", unsafe_allow_html=True)
                st.markdown(final_script)
                st.markdown("</div>", unsafe_allow_html=True)
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
st.markdown(f"<div class='section-title'>{t['section_viral']}</div>", unsafe_allow_html=True)
vcol1, vcol2, vcol3 = st.columns(3)

with vcol1:
    st.image("https://media.tenor.com/P4WmbwG8qSMAAAAd/cybercat.gif", use_container_width=True)
    st.markdown(f"<div class='gallery-caption'>{t['gallery_1']}</div>", unsafe_allow_html=True)

with vcol2:
    st.image("https://media.tenor.com/PihZ-UcwH0oAAAAC/neon-city-retro.gif", use_container_width=True)
    st.markdown(f"<div class='gallery-caption'>{t['gallery_2']}</div>", unsafe_allow_html=True)

with vcol3:
    st.image("https://media.tenor.com/p_N7b0qB23oAAAAC/ai-artificial-intelligence.gif", use_container_width=True)
    st.markdown(f"<div class='gallery-caption'>{t['gallery_3']}</div>", unsafe_allow_html=True)

# =====================================================================
# 8. Pro Templates
# =====================================================================
st.markdown(f"<div class='section-title'>{t['section_templates']}</div>", unsafe_allow_html=True)
tcol1, tcol2, tcol3, tcol4 = st.columns(4)

with tcol1:
    st.image("https://images.unsplash.com/photo-1531297122539-5692f69f41b3?auto=format&fit=crop&w=400&q=80", use_container_width=True)
    st.markdown(f"**{t['tpl_1_title']}**<br/><span style='color:gray; font-size:13px'>{t['tpl_1_sub']}</span>", unsafe_allow_html=True)

with tcol2:
    st.image("https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=400&q=80", use_container_width=True)
    st.markdown(f"**{t['tpl_2_title']}**<br/><span style='color:gray; font-size:13px'>{t['tpl_2_sub']}</span>", unsafe_allow_html=True)

with tcol3:
    st.image("https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=400&q=80", use_container_width=True)
    st.markdown(f"**{t['tpl_3_title']}**<br/><span style='color:gray; font-size:13px'>{t['tpl_3_sub']}</span>", unsafe_allow_html=True)

with tcol4:
    st.image("https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=400&q=80", use_container_width=True)
    st.markdown(f"**{t['tpl_4_title']}**<br/><span style='color:gray; font-size:13px'>{t['tpl_4_sub']}</span>", unsafe_allow_html=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)