import pandas as pd
import streamlit as st
from pathlib import Path

# ---------------------------------------
# БАЗОВЫЕ НАСТРОЙКИ СТРАНИЦЫ
# ---------------------------------------
st.set_page_config(
    page_title="CS2 Конфигуратор",
    page_icon="🎮",
    layout="wide"
)

# ------------ НАСТРОЙКИ ССЫЛОК/ВИДЖЕТОВ (меняешь ТОЛЬКО здесь) -------------
TIKTOK_URL  = "https://www.tiktok.com/@melevik?_t=ZS-8zQkTQnA4Pf&_r=1"
YOUTUBE_URL = "https://youtube.com/@melevik-avlaron?si=kRXrCD7GUrVnk478"
TWITCH_URL  = "https://m.twitch.tv/melevik/home"
DONATE_URL  = "https://www.donationalerts.com/r/melevik"

# Twitch embed (плеер). Подставь свой канал (в нижнем/мобильном — live/офлайн покажет сам Twitch)
TWITCH_EMBED_IFRAME = """
<iframe
  src="https://player.twitch.tv/?channel=melevik&parent=share.streamlit.io&muted=true"
  height="378"
  width="620"
  allowfullscreen="true">
</iframe>
"""

# YouTube embed: сюда поставь ID своего ПОСЛЕДНЕГО полноценного видео (не Shorts).
# Пример: https://www.youtube.com/watch?v=VIDEO_ID
YOUTUBE_VIDEO_ID = "dQw4w9WgXcQ"  # замени на актуальный
YOUTUBE_EMBED_IFRAME = f"""
<iframe width="620" height="349"
src="https://www.youtube.com/embed/{YOUTUBE_VIDEO_ID}"
title="YouTube video player" frameborder="0"
allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
allowfullscreen>
</iframe>
"""

# ---------------------------------------
# CSS (аккуратно, без смены твоего лэйаута)
# ---------------------------------------
st.markdown("""
<style>
/* Карточка рекомендаций — тёмный фон */
.reco-card {
  background: #0f1117;
  border: 1px solid #2a2d3a;
  border-radius: 10px;
  padding: 16px 18px;
  color: #e6e6e6;
  font-size: 15px;
}

/* Бейджики/лейблы */
.badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 6px;
  margin-right: 6px;
  font-size: 12px;
  font-weight: 600;
}

/* Соц-кнопки: цвета площадок */
.btn-row { display:flex; gap:10px; flex-wrap:wrap; margin-top:8px; }
.btn {
  padding: 10px 14px; border-radius: 8px; text-decoration:none; font-weight:700; color:#fff;
  display:inline-flex; align-items:center; gap:8px; box-shadow: 0 2px 8px rgba(0,0,0,0.25);
}
.btn:hover { opacity: .9; }

.btn-tiktok  { background:#000000; }   /* TikTok: чёрный */
.btn-youtube { background:#FF0000; }   /* YouTube: красный */
.btn-twitch  { background:#9146FF; }   /* Twitch: фиолетовый */

/* Донат-блок: мягкая жёлтая пульсация рамки */
.donate-wrap {
  border: 2px solid #f5c84b;
  border-radius: 12px;
  padding: 12px 14px;
  position: relative;
  background: #171923;
  color: #fff1c2;
  box-shadow: 0 0 0 0 rgba(245,200,75,0.5);
  animation: pulse 2.4s ease-in-out infinite;
}
@keyframes pulse {
  0%   { box-shadow: 0 0 0 0 rgba(245,200,75,0.55); }
  70%  { box-shadow: 0 0 16px 8px rgba(245,200,75,0.10); }
  100% { box-shadow: 0 0 0 0 rgba(245,200,75,0.0); }
}

/* Предупреждения */
.warn {
  background: #2b1f1f; color: #ffd9d9; border: 1px solid #7a3a3a;
  border-radius: 8px; padding: 10px 12px; margin: 8px 0;
}
.info {
  background: #1e2430; color:#d7e3ff; border: 1px solid #2f3b52;
  border-radius: 8px; padding: 10px 12px; margin: 8px 0;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------
# ЗАГРУЗКА БАЗЫ
# ---------------------------------------
@st.cache_data
def load_builds():
    p = Path("builds.csv")
    df = pd.read_csv(p)
    # Нормализация названий столбцов
    df.columns = [c.strip() for c in df.columns]
    # Обязательные колонки (если нет — создаём пустые, чтобы не падать)
    needed = [
        "CPU", "GPU", "RAM",
        "Game Settings", "Launch Options",
        "Control Panel", "Windows Optimization",
        "FPS Estimate", "Source"
    ]
    for col in needed:
        if col not in df.columns:
            df[col] = ""

    # Стандартизируем RAM представление
    df["RAM"] = df["RAM"].astype(str).str.replace("GB", " GB", regex=False)
    df["RAM"] = df["RAM"].str.replace(r"\s+", " ", regex=True).str.strip()
    return df

builds = load_builds()

# ---------------------------------------
# ВСПОМОГАТЕЛЬНОЕ
# ---------------------------------------
def clean_launch_options(s: str) -> str:
    if not isinstance(s, str):
        return ""
    tokens = s.split()
    banned = {"-novid", "-nojoy"}  # CS2: не используем
    tokens = [t for t in tokens if t not in banned]
    return " ".join(tokens).strip()

def enrich_if_too_short(text: str, fallback_block: str) -> str:
    """Если поле урезанное (слишком коротко), подменяем полноценным шаблоном."""
    if not isinstance(text, str) or len(text.strip()) < 40:
        return fallback_block.strip()
    return text

def gpu_vendor(gpu_name: str) -> str:
    s = (gpu_name or "").lower()
    if "nvidia" in s or "rtx" in s or "gtx" in s:
        return "nvidia"
    if "radeon" in s or "rx " in s or "amd " in s:
        return "amd"
    if "intel" in s or "arc" in s or "iris" in s:
        return "intel"
    return "other"

# Полные блоки-шаблоны (подставляем если строка в CSV «урезана»)
GAME_SETTINGS_FULL = """\
• Разрешение: 1920×1080 или 1280×960 (stretched), режим «Во весь экран».
• Тени: Низко
• Текстуры: Средние (повышай только если VRAM позволяет)
• Эффекты и шейдеры: Низко
• Сглаживание (MSAA/FXAA): Выкл
• Фильтрация текстур: 4× или 8×
• NVIDIA Reflex / AMD Anti-Lag: Вкл (если стабильно), иначе Выкл
"""

CONTROL_PANEL_NVIDIA_FULL = """\
• Выбор GPU: High-performance NVIDIA processor (если ноутбук)
• Режим электропитания: Предпочтительный режим максимальной производительности
• Режим низкой задержки (Low Latency): Вкл
• Вертикальная синхронизация (V-Sync): Выкл
• Качество фильтрации текстур: Высокая производительность
• Анизотропная фильтрация: Управляется приложением
• Тройная буферизация: Выкл
• Предпочтительная частота обновления: Высшая доступная
• Кэш шейдеров: По умолчанию
• Настрой профиль ТОЛЬКО для CS2, не в «Global»
"""

CONTROL_PANEL_AMD_FULL = """\
• Настрой профиль ТОЛЬКО для CS2 (не меняй Global Graphics!)
• Radeon Anti-Lag / Anti-Lag+: Вкл (если стабильно), иначе Выкл
• Radeon Chill / Boost / Enhanced Sync: Выкл
• Режим текстурной фильтрации: Производительность
• Анизотропная фильтрация: Управляется приложением
• Морфологическое сглаживание (MLAA): Выкл
• Radeon Super Resolution (RSR): Выкл глобально; если используешь — включай в профиле CS2
• В ноутбуках — режим питания «Максимальная производительность»
"""

CONTROL_PANEL_INTEL_FULL = """\
• Режим электропитания: Максимальная производительность
• Качество/Производительность: Смещай в сторону производительности
• V-Sync: Выкл
• Анизотропная фильтрация: Управляется приложением
• Перепроверь, что CS2 запущена на дискретной карте (если гибридная графика)
"""

WINDOWS_OPT_FULL = """\
• Windows Game Mode: Вкл; Xbox Game Bar и DVR: Выкл
• Питание: «Высокая производительность» или «Макс. производительность»
• Совместимость cs2.exe: «Отключить оптимизации во весь экран»
• Планировщик GPU (HAGS): Вкл (Windows 11)
• Отключи оверлеи (Discord, GeForce, Steam) и лишний автозапуск
• Обнови драйверы GPU и чипсета; добавь Steam в исключения защитника
"""

# ---------------------------------------
# ЛЕЙАУТ
# ---------------------------------------
st.title("⚙️ CS2 Конфигуратор")
st.caption("Подбери готовые настройки под свою сборку. Полезно и безопасно — без глобального ковыряния драйверов.")

# Фильтры
colL, colR = st.columns([1, 1])
with colL:
    cpu = st.selectbox("Выбери процессор", sorted(builds["CPU"].dropna().unique()))
    gpu = st.selectbox("Выбери видеокарту", sorted(builds["GPU"].dropna().unique()))
    ram = st.selectbox("Выбери объём ОЗУ", sorted(builds["RAM"].dropna().unique()))
with colR:
    if st.button("🔄 Обновить базу (builds.csv)"):
        st.cache_data.clear()
        st.success("База обновлена из репозитория. Нажми «Найти настройки» ещё раз.")
    st.markdown(
        '<div class="info">ℹ️ Если у тебя <b>одноканальная ОЗУ</b> (1 планка), '
        'ожидай −10–25% FPS по сравнению с двухканалом (2×8/2×16). Рекомендуется двухканал.</div>',
        unsafe_allow_html=True
    )

# Поиск
if st.button("🔍 Найти настройки"):
    result = builds[(builds["CPU"] == cpu) & (builds["GPU"] == gpu) & (builds["RAM"] == ram)]

    st.markdown("---")

    if result.empty:
        st.error("❌ Подходящей конфигурации не найдено в базе. Проверь точные названия CPU/GPU/RAM.")
    else:
        row = result.iloc[0].copy()

        # Обогащаем поля, если были урезаны
        gs = enrich_if_too_short(row["Game Settings"], GAME_SETTINGS_FULL)

        vend = gpu_vendor(row["GPU"])
        if vend == "nvidia":
            cp = enrich_if_too_short(row["Control Panel"], CONTROL_PANEL_NVIDIA_FULL)
        elif vend == "amd":
            cp = enrich_if_too_short(row["Control Panel"], CONTROL_PANEL_AMD_FULL)
        elif vend == "intel":
            cp = enrich_if_too_short(row["Control Panel"], CONTROL_PANEL_INTEL_FULL)
        else:
            cp = row["Control Panel"]

        winopt = enrich_if_too_short(row["Windows Optimization"], WINDOWS_OPT_FULL)
        launch_clean = clean_launch_options(row["Launch Options"])

        # Карточка на тёмном фоне
        st.markdown('<div class="reco-card">', unsafe_allow_html=True)
        st.markdown(
            f"""
<span class="badge" style="background:#243; color:#cfe;">CPU</span> {row['CPU']}  
<span class="badge" style="background:#342; color:#e6ffd8;">GPU</span> {row['GPU']}  
<span class="badge" style="background:#233; color:#d9f;">RAM</span> {row['RAM']}  

**🎮 Настройки игры:**  
{gs}

**🚀 Параметры запуска (очищено):**  
`{launch_clean}`

**🎛 Панель драйвера (NVIDIA/AMD/Intel):**  
{cp}

**🪟 Оптимизация Windows (по желанию):**  
{winopt}

**📊 Ожидаемый FPS:** {row.get('FPS Estimate', '—')}  
**🔗 Источник:** {row.get('Source', '')}
""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Предупреждения по драйверам
        if vend == "amd":
            st.markdown(
                '<div class="warn">⚠️ AMD: не меняй <b>Global Graphics</b>. '
                'Делай профиль именно для CS2. '
                'Chill/Boost/Enhanced Sync — держи <b>Выкл</b>, включай только если понимаешь эффект. '
                'RSR включай только в профиле, не глобально.</div>',
                unsafe_allow_html=True
            )
        if vend == "intel":
            st.markdown(
                '<div class="info">ℹ️ Intel iGPU/Arc: проверь, что CS2 реально запускается на дискретной карте '
                '(если гибридная графика), и выкручена «Максимальная производительность».</div>',
                unsafe_allow_html=True
            )

        # Скачать профиль .txt
        profile_txt = (
            f"CPU: {row['CPU']}\n"
            f"GPU: {row['GPU']}\n"
            f"RAM: {row['RAM']}\n\n"
            f"[Game Settings]\n{gs}\n\n"
            f"[Launch Options]\n{launch_clean}\n\n"
            f"[Control Panel]\n{cp}\n\n"
            f"[Windows Optimization]\n{winopt}\n\n"
            f"FPS Estimate: {row.get('FPS Estimate','—')}\n"
            f"Source: {row.get('Source','')}\n"
        )
        st.download_button("💾 Скачать профиль (.txt)", data=profile_txt, file_name="cs2_profile.txt")

# ---------------------------------------
# Соц-кнопки (цвета площадок) — НЕ МЕНЯЛ РАСПОЛОЖЕНИЕ
# ---------------------------------------
st.markdown("---")
st.subheader("Подписывайся, чтобы следить за актуальными обновлениями и контентом автора")
st.markdown(
    f"""
<div class="btn-row">
  <a class="btn btn-tiktok"  href="{TIKTOK_URL}"  target="_blank" rel="noopener">TikTok</a>
  <a class="btn btn-youtube" href="{YOUTUBE_URL}" target="_blank" rel="noopener">YouTube</a>
  <a class="btn btn-twitch"  href="{TWITCH_URL}"  target="_blank" rel="noopener">Twitch</a>
</div>
""",
    unsafe_allow_html=True
)

# ---------------------------------------
# Донат (мягкая пульсация, без крика)
# ---------------------------------------
st.markdown("---")
st.subheader("Поддержи проект")
st.markdown(
    f"""
<div class="donate-wrap">
  Любой, кто поддержит рублём — попадёт в следующий ролик (в благодарности в конце).
  <div style="margin-top:8px;">
    <a class="btn" style="background:#f5c84b;color:#000;" href="{DONATE_URL}" target="_blank" rel="noopener">
      💛 Поддержать
    </a>
  </div>
</div>
""",
    unsafe_allow_html=True
)

# ---------------------------------------
# Twitch / YouTube блоки (не меняю логику)
# ---------------------------------------
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Twitch — стрим (онлайн/оффлайн видно в плеере)")
    st.components.v1.html(TWITCH_EMBED_IFRAME, height=400, scrolling=False)
with col2:
    st.subheader("YouTube — последнее видео")
    st.components.v1.html(YOUTUBE_EMBED_IFRAME, height=360, scrolling=False)

