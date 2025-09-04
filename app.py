# app.py
import streamlit as st
import pandas as pd
import re

# ================== НАСТРОЙКИ СТРАНИЦЫ ==================
st.set_page_config(page_title="CS2 Конфигуратор", page_icon="🎮", layout="centered")

# ---------- КОНФИГ ВСТРОЕК ----------
TWITCH_CHANNEL = "melevik"                   # <-- твой Twitch-канал
TWITCH_PARENT_DOMAIN = "your-app.streamlit.app"  # <-- домен твоего приложения
YOUTUBE_LAST_VIDEO_ID = "dQw4w9WgXcQ"        # <-- ID последнего полноформатного видео

# ================== СТИЛИ ==================
st.markdown("""
<style>
.reco-box {
  background:#0b0b0b; color:#e6e6e6; border:1px solid #2a2a2a;
  border-radius:10px; padding:16px 18px; line-height:1.5; font-size:0.98rem;
}
.btn-row { display:flex; gap:10px; flex-wrap:wrap; }
.btn { display:inline-flex; align-items:center; gap:8px; padding:10px 14px;
       border-radius:8px; text-decoration:none; font-weight:600; color:#fff; border:none; }
.btn-yt { background:#FF0000; }
.btn-twitch { background:#9146FF; }
.btn-tt { background:#000000; border:1px solid #222; }
.pulse-wrap {
  border-radius:12px; padding:14px 16px; border:1px solid #3a3000;
  background:linear-gradient(180deg,#2b2500,#1c1800);
  position:relative; box-shadow:0 0 0 0 rgba(255,213,0,0.45); animation:pulse 2.4s ease-in-out infinite;
}
@keyframes pulse {
  0% { box-shadow:0 0 0 0 rgba(255,213,0,0.36); }
  70% { box-shadow:0 0 20px 8px rgba(255,213,0,0.10); }
  100% { box-shadow:0 0 0 0 rgba(255,213,0,0.0); }
}
.pulse-title { color:#FFD700; font-weight:800; margin:0 0 6px 0; }
.pulse-text { color:#f1f1c0; margin:6px 0 0 0; }
.note {
  background:#121212; border:1px solid #2a2a2a; border-radius:8px;
  padding:10px 12px; color:#d9d9d9; font-size:0.95rem;
}
.embed-card { background:#0b0b0b; border:1px solid #2a2a2a; border-radius:10px; padding:10px; }
.embed-title { color:#ddd; font-weight:700; font-size:1rem; margin-bottom:8px; }
</style>
""", unsafe_allow_html=True)

# ================== УТИЛИТЫ НОРМАЛИЗАЦИИ ==================
def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())

def cpu_key(s: str) -> str:
    s = s.lower()
    s = s.replace("®","").replace("™","")
    s = s.replace("intel ","intel ").replace("amd ","amd ")
    s = s.replace("core ","core ")
    s = s.replace("ryzen ","ryzen ")
    s = s.replace("  ", " ")
    s = re.sub(r"[^a-z0-9\-\s]", "", s)
    return norm_space(s)

def gpu_key(s: str) -> str:
    s = s.lower()
    s = s.replace("nvidia ","nvidia ").replace("geforce ","geforce ")
    s = s.replace("amd ","amd ").replace("radeon ","radeon ")
    s = s.replace("  ", " ")
    s = re.sub(r"[^a-z0-9\-\s]", "", s)
    return norm_space(s)

def ram_gb_val(s: str):
    if s is None:
        return None
    s = str(s).lower().replace("гб","gb")
    digits = re.findall(r"\d+", s)
    if not digits:
        return None
    try:
        return int(digits[0])
    except:
        return None

def clean_launch_options(s: str) -> str:
    if not isinstance(s, str): return ""
    banned = {"-novid", "-nojoy"}
    tokens = [t for t in s.split() if t not in banned]
    cleaned = " ".join(tokens).strip()
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned

# ================== ЗАГРУЗКА БАЗЫ ==================
@st.cache_data
def load_builds():
    try:
        df = pd.read_csv("builds.csv")
    except FileNotFoundError:
        st.error("Файл builds.csv не найден в корне репозитория. Залей его и нажми «🔄 Обновить базу».")
        return pd.DataFrame()

    # Канонизация колонок
    df.columns = [c.strip() for c in df.columns]
    canon = {
        "CPU": ["CPU","cpu","Cpu","Процессор"],
        "GPU": ["GPU","gpu","Gpu","Видеокарта"],
        "RAM": ["RAM","ram","Ram","ОЗУ","Memory","RAM (GB)","ram_gb"],
        "Game Settings": ["Game Settings","Settings","GameSettings","Настройки игры"],
        "Launch Options": ["Launch Options","Launch","Params","LaunchOptions","Параметры запуска"],
        "Control Panel": ["Control Panel","ControlPanel","Driver Settings","Driver","Панель драйвера"],
        "Windows Optimization": ["Windows Optimization","Windows","Windows Opt","Оптимизация Windows"],
        "FPS Estimate": ["FPS Estimate","FPS","FPS Range","Estimate","Ожидаемый FPS"],
        "Source": ["Source","Источник"]
    }
    for target, vars_ in canon.items():
        if target not in df.columns:
            for v in vars_:
                if v in df.columns:
                    df[target] = df[v]
                    break
        if target not in df.columns:
            df[target] = ""

    # Нормализованные ключи для стабильного поиска
    df["cpu_key"] = df["CPU"].astype(str).apply(cpu_key)
    df["gpu_key"] = df["GPU"].astype(str).apply(gpu_key)
    df["ram_gb"]  = df["RAM"].apply(ram_gb_val)

    # Формат RAM для отображения
    def fmt_ram_disp(x):
        return f"{x} GB" if pd.notnull(x) else ""
    df["RAM_display"] = df["ram_gb"].apply(fmt_ram_disp)

    # Убираем явные мусорные строки
    df = df[df["cpu_key"]!=""]
    df = df[df["gpu_key"]!=""]
    df = df[df["ram_gb"].notnull()]

    # Дедуп по ключам
    df = df.drop_duplicates(subset=["cpu_key","gpu_key","ram_gb"], keep="first").reset_index(drop=True)
    return df

builds = load_builds()

# ================== UI: ШАПКА ==================
st.title("⚙️ CS2 Конфигуратор")
st.caption("Подбери готовые настройки (игра, панель драйвера, параметры запуска, системные оптимизации).")

# Встройки: Twitch + YouTube (как было)
colA, colB = st.columns(2, gap="large")
with colA:
    st.markdown('<div class="embed-card"><div class="embed-title">🔴 Twitch — LIVE статус</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <iframe
        src="https://player.twitch.tv/?channel={TWITCH_CHANNEL}&parent={TWITCH_PARENT_DOMAIN}&muted=true"
        height="260" width="100%" frameborder="0" scrolling="no" allowfullscreen="true">
    </iframe>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with colB:
    st.markdown('<div class="embed-card"><div class="embed-title">▶️ Последнее видео на YouTube</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <iframe
        width="100%" height="260"
        src="https://www.youtube.com/embed/{YOUTUBE_LAST_VIDEO_ID}"
        title="YouTube video player" frameborder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
        allowfullscreen>
    </iframe>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ================== ПОИСК НАСТРОЕК ==================
st.subheader("🔍 Подбор по железу")

if builds.empty:
    st.info("Загрузи корректный builds.csv и нажми «🔄 Обновить базу».")
else:
    # Опции для селектов — показываем как в базе, но матчим по ключам
    cpu_options = sorted(builds["CPU"].unique(), key=lambda s: cpu_key(str(s)))
    gpu_options = sorted(builds["GPU"].unique(), key=lambda s: gpu_key(str(s)))
    ram_options = sorted(builds["ram_gb"].dropna().unique())  # числа
    ram_display = [f"{int(x)} GB" for x in ram_options]

    cpu_sel = st.selectbox("🖥 Процессор (CPU)", cpu_options)
    gpu_sel = st.selectbox("🎮 Видеокарта (GPU)", gpu_options)
    ram_sel = st.selectbox("💾 Оперативная память (RAM)", ram_display)

    if st.button("Найти настройки"):
        cpu_k = cpu_key(str(cpu_sel))
        gpu_k = gpu_key(str(gpu_sel))
        ram_g = int(re.findall(r"\d+", ram_sel)[0]) if re.findall(r"\d+", ram_sel) else None

        result = builds[
            (builds["cpu_key"] == cpu_k) &
            (builds["gpu_key"] == gpu_k) &
            (builds["ram_gb"]  == ram_g)
        ]

        st.markdown("---")

        if result.empty:
            st.error("❌ Подходящей конфигурации не найдено. Проверь точность CPU/GPU/RAM в builds.csv или обнови базу ниже.")
        else:
            row = result.iloc[0].to_dict()
            launch_clean = clean_launch_options(row.get("Launch Options",""))

            st.markdown('<div class="reco-box">', unsafe_allow_html=True)
            st.markdown(f"""
**🖥 Процессор:** {row.get('CPU','')}
**🎮 Видеокарта:** {row.get('GPU','')}
**💾 ОЗУ:** {row.get('RAM_display', row.get('RAM',''))}

**🎮 Настройки игры:**  
{row.get('Game Settings','—')}

**🚀 Параметры запуска (очищенные):**  
`{launch_clean if launch_clean else "—"}`

**🎛 Панель драйвера (NVIDIA/AMD):**  
{row.get('Control Panel','—')}

**🪟 Оптимизация Windows (по желанию):**  
{row.get('Windows Optimization','—')}

**📊 Ожидаемый FPS:** {row.get('FPS Estimate','—')}
**🔗 Источник:** {row.get('Source','—')}
""")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="note">💡 Если у тебя одноканальная память (1× модуль), FPS будет ниже, чем при двухканале (2× одинаковых модулей). Для CS2 двухканал даёт заметный прирост.</div>', unsafe_allow_html=True)

            profile_txt = (
                f"CPU: {row.get('CPU','')}\n"
                f"GPU: {row.get('GPU','')}\n"
                f"RAM: {row.get('RAM_display', row.get('RAM',''))}\n\n"
                f"[Game Settings]\n{row.get('Game Settings','')}\n\n"
                f"[Launch Options]\n{launch_clean}\n\n"
                f"[Control Panel]\n{row.get('Control Panel','')}\n\n"
                f"[Windows Optimization]\n{row.get('Windows Optimization','')}\n\n"
                f"FPS Estimate: {row.get('FPS Estimate','—')}\n"
                f"Source: {row.get('Source','')}\n"
            )
            st.download_button("💾 Скачать профиль (.txt)", data=profile_txt, file_name="cs2_profile.txt")

# Кнопка обновления базы (очистка кэша)
if st.button("🔄 Обновить базу (очистить кэш)"):
    load_builds.clear()
    st.success("Кэш очищен. Обнови страницу (Ctrl/Cmd + R), чтобы подтянуть свежий builds.csv.")

st.markdown("---")

# ================== ПРЕДУПРЕЖДЕНИЯ ПО ДРАЙВЕРАМ ==================
st.subheader("⚠️ Важно про глобальные настройки драйвера")
st.markdown('<div class="note">', unsafe_allow_html=True)
st.markdown("""
**AMD (Adrenalin)**  
• Не меняй глобально «Продуктивность/Качество» и Anti-Lag+, лучше создай **профиль только для CS2**.  
• Radeon Chill/Boost включай осознанно — они могут ограничивать кадры и менять поведение частот.

**NVIDIA (Control Panel)**  
• «Предпочтительный режим энергопитания: Максимальная производительность» выставляй **в профиле для CS2**, а не глобально.  
• V-Sync держи «Выключено» (или «Управляется приложением») — чтобы не ловить лишнюю задержку.
""")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ================== ПОДДЕРЖКА ПРОЕКТА ==================
st.subheader("Поддержи проект")
st.markdown("""
<div class="pulse-wrap">
  <div class="pulse-title">Каждый, кто поддержит рублём — попадёт в следующий ролик 🙌</div>
  <div class="pulse-text">Твоя поддержка ускоряет обновления базы и новые гайды.</div>
  <div style="margin-top:10px;">
    <a class="btn btn-tt" href="https://www.donationalerts.com/r/melevik" target="_blank">💸 DonatPay</a>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ================== СОЦСЕТИ (ЦВЕТА ПЛОЩАДОК) ==================
st.subheader("Подписывайся, чтобы не пропускать обновления и новые видео")
st.markdown("""
<div class="btn-row">
  <a class="btn btn-tt" href="https://www.tiktok.com/@melevik?_t=ZS-8zQkTQnA4Pf&_r=1" target="_blank">TikTok</a>
  <a class="btn btn-yt" href="https://youtube.com/@melevik-avlaron?si=kRXrCD7GUrVnk478" target="_blank">YouTube</a>
  <a class="btn btn-twitch" href="https://m.twitch.tv/melevik/home" target="_blank">Twitch</a>
</div>
""", unsafe_allow_html=True)

st.caption("База регулярно пополняется. Если не нашёл свою конфигурацию — напиши в комментариях к видео, добавлю.")
