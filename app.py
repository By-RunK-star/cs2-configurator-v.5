# app.py
import streamlit as st
import pandas as pd

# ============ БАЗОВЫЕ НАСТРОЙКИ САЙТА ============
st.set_page_config(page_title="CS2 Конфигуратор", page_icon="🎮", layout="centered")

# ------------ КОНФИГ ДЛЯ ВСТРОЕК ------------
TWITCH_CHANNEL = "melevik"  # <-- твой Twitch-канал
# Укажи точный домен твоего Streamlit-приложения (для Twitch embed):
# пример: "cs2-configurator-v-5-username.streamlit.app"
TWITCH_PARENT_DOMAIN = "your-subdomain.streamlit.app"
YOUTUBE_LAST_VIDEO_ID = "dQw4w9WgXcQ"  # <-- сюда вставляй ID последнего полноформатного видео

# ------------ СТИЛИ ------------
st.markdown("""
<style>
/* Темный бокс для рекомендуемых настроек */
.reco-box {
  background: #0b0b0b;
  color: #e6e6e6;
  border: 1px solid #2a2a2a;
  border-radius: 10px;
  padding: 16px 18px;
  line-height: 1.5;
  font-size: 0.98rem;
}

/* Соц-кнопки — цвета площадок */
.btn-row { display: flex; gap: 10px; flex-wrap: wrap; }
.btn {
  display:inline-flex; align-items:center; gap:8px;
  padding:10px 14px; border-radius:8px; text-decoration:none;
  font-weight:600; color:#fff; border:none;
}
.btn-yt { background:#FF0000; }
.btn-twitch { background:#9146FF; }
.btn-tt { background:#000000; border:1px solid #222; }

/* Пульсация доната (мягкая) */
.pulse-wrap {
  border-radius:12px;
  padding:14px 16px;
  border:1px solid #3a3000;
  background: linear-gradient(180deg, #2b2500, #1c1800);
  position: relative;
  box-shadow: 0 0 0 0 rgba(255, 213, 0, 0.45);
  animation: pulse 2.4s ease-in-out infinite;
}
@keyframes pulse {
  0%   { box-shadow: 0 0 0 0 rgba(255, 213, 0, 0.36); }
  70%  { box-shadow: 0 0 20px 8px rgba(255, 213, 0, 0.10);}
  100% { box-shadow: 0 0 0 0 rgba(255, 213, 0, 0.0); }
}
.pulse-title { color:#FFD700; font-weight:800; margin:0 0 6px 0; }
.pulse-text { color:#f1f1c0; margin:6px 0 0 0; }

/* Аккуратное предупреждение */
.note {
  background:#121212; border:1px solid #2a2a2a; border-radius:8px;
  padding:10px 12px; color:#d9d9d9; font-size:0.95rem;
}

/* Карточки встроек */
.embed-card {
  background:#0b0b0b; border:1px solid #2a2a2a; border-radius:10px; padding:10px;
}
.embed-title { color:#ddd; font-weight:700; font-size:1rem; margin-bottom:8px; }
</style>
""", unsafe_allow_html=True)

# ============ ЗАГРУЗКА ДАННЫХ ============
@st.cache_data
def load_builds():
    df = pd.read_csv("builds.csv")
    # нормализуем названия колонок
    df.columns = df.columns.str.strip()
    # Канонические имена:
    canon = {
        "CPU": ["CPU", "cpu", "Cpu", "Процессор"],
        "GPU": ["GPU", "gpu", "Gpu", "Видеокарта"],
        "RAM": ["RAM", "ram", "Ram", "ОЗУ", "Memory", "RAM (GB)", "ram_gb"],
        "Game Settings": ["Game Settings", "Settings", "GameSettings", "Настройки игры"],
        "Launch Options": ["Launch Options", "Launch", "Params", "LaunchOptions", "Параметры запуска"],
        "Control Panel": ["Control Panel", "ControlPanel", "Driver Settings", "Driver", "Панель драйвера"],
        "Windows Optimization": ["Windows Optimization", "Windows", "Windows Opt", "Оптимизация Windows"],
        "FPS Estimate": ["FPS Estimate", "FPS", "FPS Range", "Estimate", "Ожидаемый FPS"],
        "Source": ["Source", "Источник"]
    }
    for target, variants in canon.items():
        for v in variants:
            if v in df.columns:
                df[target] = df[v]
                break
        if target not in df.columns:
            df[target] = ""

    # Приводим RAM к аккуратной строке (например "16 GB")
    if "RAM" in df.columns:
        def fmt_ram(x):
            s = str(x).strip()
            s = s.replace("ГБ","GB").replace("гб","GB").replace("Gb","GB")
            s = s.replace(" ", "")
            # вытаскиваем число
            for suf in ["GB","gb","ГБ","гб"]:
                s = s.replace(suf, "")
            if s.isdigit():
                return f"{int(s)} GB"
            return s if "GB" in s else f"{s} GB" if s else ""
        df["RAM"] = df["RAM"].apply(fmt_ram)

    # Убираем дубликаты
    df = df.drop_duplicates(subset=["CPU", "GPU", "RAM"], keep="first").reset_index(drop=True)
    return df

builds = load_builds()

# Утилита очистки launch options от неактуальных флагов
def clean_launch_options(s: str) -> str:
    if not isinstance(s, str): return ""
    banned = {"-novid", "-nojoy"}
    tokens = [t for t in s.split() if t not in banned]
    cleaned = " ".join(tokens).strip()
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned

# ============ ШАПКА ============

st.title("⚙️ CS2 Конфигуратор")
st.caption("Подбери готовые настройки (игра, панель драйвера, параметры запуска, системные оптимизации).")

# Встройки: Twitch (лайв), YouTube (последнее полноформатное видео)
colA, colB = st.columns(2, gap="large")

with colA:
    st.markdown('<div class="embed-card"><div class="embed-title">🔴 Twitch — LIVE статус</div>', unsafe_allow_html=True)
    twitch_iframe = f"""
    <iframe
        src="https://player.twitch.tv/?channel={TWITCH_CHANNEL}&parent={TWITCH_PARENT_DOMAIN}&muted=true"
        height="260" width="100%" frameborder="0" scrolling="no" allowfullscreen="true">
    </iframe>
    """
    st.markdown(twitch_iframe, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with colB:
    st.markdown('<div class="embed-card"><div class="embed-title">▶️ Последнее видео на YouTube</div>', unsafe_allow_html=True)
    yt_iframe = f"""
    <iframe
        width="100%" height="260"
        src="https://www.youtube.com/embed/{YOUTUBE_LAST_VIDEO_ID}"
        title="YouTube video player" frameborder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
        allowfullscreen>
    </iframe>
    """
    st.markdown(yt_iframe, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ============ ПОИСК НАСТРОЕК ============
st.subheader("🔍 Подбор по железу")

cpu = st.selectbox("🖥 Процессор (CPU)", sorted([x for x in builds["CPU"].unique() if str(x).strip()]))
gpu = st.selectbox("🎮 Видеокарта (GPU)", sorted([x for x in builds["GPU"].unique() if str(x).strip()]))
ram = st.selectbox("💾 Оперативная память (RAM)", sorted([x for x in builds["RAM"].unique() if str(x).strip()], key=lambda s: int(str(s).split()[0]) if str(s).split()[0].isdigit() else 0))

find = st.button("Найти настройки")

if find:
    result = builds[(builds["CPU"] == cpu) & (builds["GPU"] == gpu) & (builds["RAM"] == ram)]
    st.markdown("---")
    if result.empty:
        st.error("❌ Подходящей конфигурации не найдено в базе. Обнови базу или напиши мне в комментариях — добавлю.")
    else:
        row = result.iloc[0].to_dict()
        launch_clean = clean_launch_options(row.get("Launch Options", ""))

        # Рекомендации в тёмном боксе
        st.markdown('<div class="reco-box">', unsafe_allow_html=True)
        st.markdown(f"""
**🖥 Процессор:** {row.get('CPU','')}
**🎮 Видеокарта:** {row.get('GPU','')}
**💾 ОЗУ:** {row.get('RAM','')}

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

        # Предупреждение про одноканал/двухканал
        st.markdown('<div class="note">💡 Если у тебя одноканальная память (1× модуль), FPS будет ниже, чем при двухканале (2× одинаковых модуля). Для CS2 двухканал даёт заметный прирост.</div>', unsafe_allow_html=True)

        # Кнопка скачать профиль
        profile_txt = (
            f"CPU: {row.get('CPU','')}\n"
            f"GPU: {row.get('GPU','')}\n"
            f"RAM: {row.get('RAM','')}\n\n"
            f"[Game Settings]\n{row.get('Game Settings','')}\n\n"
            f"[Launch Options]\n{launch_clean}\n\n"
            f"[Control Panel]\n{row.get('Control Panel','')}\n\n"
            f"[Windows Optimization]\n{row.get('Windows Optimization','')}\n\n"
            f"FPS Estimate: {row.get('FPS Estimate','—')}\n"
            f"Source: {row.get('Source','')}\n"
        )
        st.download_button("💾 Скачать профиль (.txt)", data=profile_txt, file_name="cs2_profile.txt")

# Кнопка очистки кэша (обновление базы)
if st.button("🔄 Обновить базу (очистить кэш)"):
    load_builds.clear()
    st.success("Кэш очищен. Обнови страницу браузера (Ctrl/Cmd + R), чтобы подтянуть свежий builds.csv.")

st.markdown("---")

# ============ ПРЕДУПРЕЖДЕНИЯ ПО ДРАЙВЕРАМ ============
st.subheader("⚠️ Важно про глобальные настройки драйвера")
st.markdown('<div class="note">', unsafe_allow_html=True)
st.markdown("""
**AMD (Adrenalin)**  
• Не меняй глобально «Продуктивность/Качество» и Anti-Lag+, если не понимаешь — лучше создавай **профиль только для CS2**.  
• Radeon Chill/Boost включай осознанно: они могут ограничивать кадры или менять поведение частот.

**NVIDIA (Control Panel)**  
• «Предпочтительный режим энергопитания: Максимальная производительность» лучше ставить **в профиле для CS2**, а не глобально.  
• V-Sync держи «Выключено» (или «Управляется приложением») — лишняя задержка не нужна.
""")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ============ ПОДДЕРЖКА ПРОЕКТА ============
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

# ============ СОЦСЕТИ ============
st.subheader("Подписывайся, чтобы не пропускать обновления и новые видео")
st.markdown("""
<div class="btn-row">
  <a class="btn btn-tt" href="https://www.tiktok.com/@melevik?_t=ZS-8zQkTQnA4Pf&_r=1" target="_blank">TikTok</a>
  <a class="btn btn-yt" href="https://youtube.com/@melevik-avlaron?si=kRXrCD7GUrVnk478" target="_blank">YouTube</a>
  <a class="btn btn-twitch" href="https://m.twitch.tv/melevik/home" target="_blank">Twitch</a>
</div>
""", unsafe_allow_html=True)

st.caption("База регулярно пополняется. Если не нашёл свою конфигурацию — напиши в комментариях к видео, добавлю.")
