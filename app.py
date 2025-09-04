import re
import requests
import pandas as pd
import streamlit as st

# feedparser — опционально (для YouTube RSS). Без него будет fallback.
try:
    import feedparser  # type: ignore
    HAS_FEEDPARSER = True
except Exception:
    HAS_FEEDPARSER = False

st.set_page_config(page_title="CS2 Конфигуратор", page_icon="🎯", layout="centered")

# ----------------------------- СТИЛИ (аккуратно, ничего лишнего) -----------------------------
st.markdown(
    """
    <style>
      /* Карточка результатов — тёмный фон */
      .cs2-card {
        background: #0f1116;
        border: 1px solid #222630;
        border-radius: 10px;
        padding: 18px 18px 10px 18px;
        color: #e6e6e6;
        font-size: 15px;
        line-height: 1.55;
      }
      .cs2-card code { background: #141820; color: #e6e6e6; }
      .cs2-key { color:#9ecbff; font-weight:600; }

      /* Пульсирующая жёлтая плашка доната — мягкая */
      .donate-pulse {
        position: relative;
        background: linear-gradient(90deg, #2a2e36, #1f232b);
        border: 1px solid #3a3f4a;
        border-radius: 10px;
        padding: 14px 16px;
        color: #f9e79f;
        overflow: hidden;
      }
      .donate-pulse::after {
        content: "";
        position: absolute;
        left: -50%;
        top: 0;
        width: 200%;
        height: 100%;
        background: radial-gradient(circle at 50% 50%, rgba(255, 220, 70, .20), transparent 45%);
        animation: pulse 2.8s ease-in-out infinite;
        pointer-events: none;
      }
      @keyframes pulse {
        0%   { transform: translateX(-20%); opacity: .45; }
        50%  { transform: translateX( 20%); opacity: .25; }
        100% { transform: translateX(-20%); opacity: .45; }
      }
      .donate-link a { color:#ffd54d; text-decoration:none; font-weight:700; }
      .donate-link a:hover { text-decoration: underline; }

      /* Соц-кнопки в цветах платформ */
      .socials { display:flex; gap:10px; flex-wrap:wrap; }
      .btn-social {
        display:inline-block; padding:10px 14px; border-radius:8px; color:#fff; font-weight:600;
        text-decoration:none; border:0; transition: transform .06s ease-in-out; font-size:14px;
      }
      .btn-social:hover { transform: translateY(-1px); }
      .btn-yt   { background:#FF0000; }
      .btn-tktk { background:#000000; border:1px solid #222; }
      .btn-tktk span { background: linear-gradient(90deg, #25F4EE, #FE2C55); -webkit-background-clip:text; background-clip:text; color:transparent; }
      .btn-tw   { background:#9146FF; }

      /* Встраиваемые блоки (iframe) в контейнере */
      .embed-box {
        border: 1px solid #222630; border-radius: 10px; overflow:hidden;
        background:#0f1116; margin-bottom: 8px;
      }

      /* Маленький серый дисклеймер */
      .hint { color:#9aa4b2; font-size:13px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------ ЗАГРУЗКА ДАННЫХ ---------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("builds.csv")

    # Нормализуем названия столбцов → приводим к каноническим
    def ensure_col(df, canon, variants):
        for v in variants:
            if v in df.columns:
                df[canon] = df[v]
                break
        if canon not in df.columns:
            df[canon] = ""
        return df

    df = ensure_col(df, "Game Settings", ["Game Settings", "Settings", "GameSettings"])
    df = ensure_col(df, "Launch Options", ["Launch Options", "Launch", "Params", "LaunchOptions"])
    df = ensure_col(df, "Control Panel", ["Control Panel", "ControlPanel", "Driver Settings", "Driver"])
    df = ensure_col(df, "Windows Optimization", ["Windows Optimization", "Windows Optimizations", "Windows", "Windows Opt"])
    df = ensure_col(df, "FPS Estimate", ["FPS Estimate", "FPS", "FPS Range", "Estimate"])
    df = ensure_col(df, "Source", ["Source"])

    # RAM → привести к формату "16 GB"
    if "RAM" in df.columns:
        df["RAM"] = (
            df["RAM"]
            .astype(str)
            .str.replace("ГБ", " GB", regex=False)
            .str.replace("GB", " GB", regex=False)
            .str.replace("  ", " ", regex=False)
            .str.strip()
        )

    return df

df = load_data()

# Очистка параметров запуска от неподдерживаемых/бесполезных флагов
def clean_launch_options(s: str) -> str:
    if not isinstance(s, str):
        return ""
    tokens = s.split()
    banned = {"-novid", "-nojoy"}  # Убрали неактуальные для CS2
    tokens = [t for t in tokens if t not in banned]
    cleaned = " ".join(tokens)
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned.strip()

# ---------------------------------------- ШАПКА ---------------------------------------------
st.title("⚙️ CS2 Конфигуратор")
st.caption("Подбери готовые настройки по своей сборке: игра • панель драйвера • параметры запуска • Windows-оптимизации.")

# Фильтры
col1, col2, col3 = st.columns(3)
with col1:
    cpu = st.selectbox("🖥 Процессор (CPU)", sorted(df["CPU"].dropna().unique()))
with col2:
    gpu = st.selectbox("🎮 Видеокарта (GPU)", sorted(df["GPU"].dropna().unique()))
with col3:
    ram = st.selectbox("💾 ОЗУ (RAM)", sorted(df["RAM"].dropna().unique()))

# Предупреждение про одноканал/двухканал
st.info("ℹ️ Если у вас **одноканальная** память — ожидайте на 10–30% ниже FPS. **Двухканал** даёт ощутимый прирост.", icon="ℹ️")

# Кнопки действий
c1, c2 = st.columns([1, 1])
with c1:
    find_clicked = st.button("🔍 Найти настройки")
with c2:
    if st.button("🔄 Обновить базу (builds.csv)"):
        st.cache_data.clear()
        st.rerun()

# ------------------------------------- РЕЗУЛЬТАТ ПОИСКА -------------------------------------
if find_clicked:
    result = df[(df["CPU"] == cpu) & (df["GPU"] == gpu) & (df["RAM"] == ram)]
    st.markdown("---")
    if result.empty:
        st.error("❌ Подходящей конфигурации не найдено в базе.")
    else:
        row = result.iloc[0].to_dict()
        launch_clean = clean_launch_options(row.get("Launch Options", ""))

        st.subheader("✅ Рекомендованные настройки")
        # Тёмная карточка
        st.markdown('<div class="cs2-card">', unsafe_allow_html=True)
        st.markdown(
            f"""
<span class="cs2-key">🖥 Процессор:</span> {row.get('CPU','')}  
<span class="cs2-key">🎮 Видеокарта:</span> {row.get('GPU','')}  
<span class="cs2-key">💾 ОЗУ:</span> {row.get('RAM','')}

**🎮 Настройки игры:**  
{row.get('Game Settings','')}

**🚀 Параметры запуска (очищено):**  
<code>{launch_clean}</code>

**🎛 Панель драйвера (NVIDIA/AMD):**  
{row.get('Control Panel','')}

**🪟 Оптимизация Windows (по желанию):**  
{row.get('Windows Optimization','')}

**📊 Ожидаемый FPS:** {row.get('FPS Estimate','—')}  
**🔗 Источник:** {row.get('Source','')}
            """,
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # Кнопка скачать профиль .txt
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

# ----------------------------------- ВАЖНЫЕ ПРЕДУПРЕЖДЕНИЯ ----------------------------------
with st.expander("⚠️ Важно: не меняйте опасные глобальные тумблеры драйвера"):
    st.markdown(
        """
- **AMD**: не включайте **Anti-Lag+**, **Chill**, **Radeon Boost**, **Radeon Super Resolution** **глобально** — задавайте **только для CS2** в профиле игры.  
- **NVIDIA**: «**Режим управления электропитанием → Максимальная производительность**» включайте **только в профиле CS2**, а не глобально.  
- **Intel (iGPU)**: не включайте глобально **V-Sync**, **тройную буферизацию**; задавайте параметры **пер-приложение**.  
- Параметры запуска **очищены**: мы автоматически убираем флаги `-novid` и `-nojoy`, т.к. они неактуальны для CS2.
        """
    )

# ------------------------------------- ПОДДЕРЖИ ПРОЕКТ --------------------------------------
st.markdown(
    """
<div class="donate-pulse">
  <div style="font-weight:700; margin-bottom:6px;">Поддержи проект</div>
  <div class="donate-link">
    Каждый, кто поддержит рублём, попадёт в **следующий ролик** в благодарности.
    <br/>👉 <a href="https://www.donationalerts.com/r/melevik" target="_blank">DonatPay (DonationAlerts)</a>
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------ СОЦИАЛЬНЫЕ СЕТИ ---------------------------------------
st.markdown("#### Подписывайся, чтобы следить за актуальными обновлениями и контентом автора")
st.markdown(
    """
<div class="socials">
  <a class="btn-social btn-tktk" href="https://www.tiktok.com/@melevik?_t=ZS-8zQkTQnA4Pf&_r=1" target="_blank">TikTok <span>★</span></a>
  <a class="btn-social btn-yt"   href="https://youtube.com/@melevik-avlaron" target="_blank">YouTube</a>
  <a class="btn-social btn-tw"   href="https://m.twitch.tv/melevik/home" target="_blank">Twitch</a>
</div>
<p class="hint">Спасибо за подписку — это помогает развивать базу и выпускать обновления быстрее.</p>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------- TWITCH EMBED -----------------------------------------
with st.expander("🎥 Прямо сейчас на Twitch (авто)"):
    st.markdown(
        """
<div class="embed-box">
  <div id="twitch-embed"></div>
</div>
<script>
  (function() {
    const parent = window.location.hostname;
    const html = `
      <iframe
        src="https://player.twitch.tv/?channel=melevik&parent=${parent}"
        height="420" width="100%" frameborder="0" scrolling="no" allowfullscreen="true">
      </iframe>`;
    const box = document.getElementById('twitch-embed');
    if (box) box.innerHTML = html;
  })();
</script>
<p class="hint">Если «оффлайн» — заглядывай позже, стримы регулярно!</p>
        """,
        unsafe_allow_html=True,
    )

# -------------------------------------- YOUTUBE EMBED ----------------------------------------
def resolve_youtube_channel_id(handle_url: str) -> str | None:
    """Пробуем вытащить channel_id по @handle без API-ключа."""
    try:
        html = requests.get(handle_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).text
        m = re.search(r'"channelId":"(UC[0-9A-Za-z_-]{22})"', html)
        return m.group(1) if m else None
    except Exception:
        return None

def get_latest_non_shorts_video_id(channel_handle_url: str) -> str | None:
    """Берём последнее НЕ-Shorts видео через RSS; если нет feedparser — вернём None."""
    channel_id = resolve_youtube_channel_id(channel_handle_url)
    if not channel_id:
        return None
    if not HAS_FEEDPARSER:
        return None
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            # Грубый фильтр шортов по названию/ссылке
            if "short" in title.lower() or "/shorts/" in link.lower():
                continue
            # Достаём ID
            m = re.search(r"v=([0-9A-Za-z_-]{11})", link)
            if m:
                return m.group(1)
        return None
    except Exception:
        return None

with st.expander("📺 Новое видео на YouTube (не Shorts)"):
    yt_handle = "https://youtube.com/@melevik-avlaron"
    vid_id = get_latest_non_shorts_video_id(yt_handle)
    if vid_id:
        st.markdown(
            f"""
<div class="embed-box">
  <iframe width="100%" height="420"
    src="https://www.youtube.com/embed/{vid_id}"
    title="Последнее видео"
    frameborder="0"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
    allowfullscreen></iframe>
</div>
<p class="hint">Если ролик не загрузился — открой канал: <a href="{yt_handle}" target="_blank">YouTube / @melevik-avlaron</a></p>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
<p class="hint">Не удалось получить последнее видео автоматически. Перейди на канал:</p>
<div class="embed-box" style="padding:16px;">
  <a class="btn-social btn-yt" href="{yt_handle}" target="_blank">Открыть канал YouTube</a>
</div>
            """,
            unsafe_allow_html=True,
        )
