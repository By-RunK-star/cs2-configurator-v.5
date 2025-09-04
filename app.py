import pandas as pd
import streamlit as st
from difflib import get_close_matches

# ──────────────────────────────────────────────────────────────────────────────
# БАЗОВЫЕ НАСТРОЙКИ СТРАНИЦЫ
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="CS2 Конфигуратор", page_icon="🎮", layout="wide")

# Глобальный CSS (карточки, кнопки соцсетей, донат-пульсация и т.д.)
st.markdown("""
<style>
/* Контейнер с чёрным фоном под рекомендации */
.result-card {
  background: #0f1116;
  color: #ffffff;
  border: 1px solid #22252e;
  border-radius: 12px;
  padding: 18px 18px 12px 18px;
  line-height: 1.55;
  font-size: 16px;
}
.result-card h3 {
  margin: 0 0 10px 0;
  color: #ffffff;
}

/* Соцкнопки: цвета площадок, без изменения вашего макета */
.social-row { display: flex; gap: 10px; flex-wrap: wrap; }
.btn-social {
  display: inline-block; padding: 10px 14px; border-radius: 10px;
  text-decoration: none; color: #fff; font-weight: 600;
  box-shadow: 0 4px 10px rgba(0,0,0,.2);
}
.btn-tiktok { background: #010101; }
.btn-youtube { background: #cc0000; }
.btn-twitch { background: #9146ff; }

/* Блок поддержки: мягкая золотая пульсация без агрессивной кнопки */
.support-box {
  position: relative; border-radius: 12px; padding: 14px 16px; color: #1b1b1b;
  background: linear-gradient(135deg, #ffe27a, #ffd84d);
  box-shadow: 0 4px 18px rgba(255, 216, 77, .35);
  animation: pulseGold 2.2s ease-in-out infinite;
}
@keyframes pulseGold {
  0%   { box-shadow: 0 0 0 0 rgba(255, 216, 77, .5); }
  70%  { box-shadow: 0 0 0 14px rgba(255, 216, 77, 0); }
  100% { box-shadow: 0 0 0 0 rgba(255, 216, 77, 0); }
}

/* Предупреждения */
.warn-box {
  background: #161a22; border: 1px solid #2a3140; color: #e6e6e6;
  border-radius: 10px; padding: 12px 14px; font-size: 14px;
}
.warn-title { font-weight: 700; color: #ffd84d; }

/* Тонкие горизонтальные линии */
.hr { height: 1px; background: #1f2230; border: none; margin: 14px 0; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# ЗАГРУЗКА ДАННЫХ
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_builds() -> pd.DataFrame:
    df = pd.read_csv("builds.csv")

    # Приводим названия колонок к ожидаемым (если вдруг есть вариации)
    rename_map = {}
    cols = {c.lower(): c for c in df.columns}

    def col_name(*variants, default=None):
        for v in variants:
            if v.lower() in cols:
                return cols[v.lower()]
        return default

    cpu_col = col_name("CPU", "Cpu", "cpu", default="CPU")
    gpu_col = col_name("GPU", "Gpu", "gpu", default="GPU")
    ram_col = col_name("RAM", "Ram", "ram", default="RAM")
    gs_col  = col_name("Game Settings", "Settings", "GameSettings", default="Game Settings")
    lo_col  = col_name("Launch Options", "Launch", "Params", "LaunchOptions", default="Launch Options")
    cp_col  = col_name("Control Panel", "ControlPanel", "Driver Settings", "Driver", default="Control Panel")
    win_col = col_name("Windows Optimization", "Windows", "Windows Optimizations", "Windows Opt",
                       default="Windows Optimization")
    fps_col = col_name("FPS Estimate", "FPS", "Estimate", "FPS Range", default="FPS Estimate")
    src_col = col_name("Source", "source", default="Source")

    # Гарантируем наличие необходимых столбцов
    for need in [cpu_col, gpu_col, ram_col, gs_col, lo_col, cp_col, win_col, fps_col, src_col]:
        if need not in df.columns:
            df[need] = ""

    # Нормализация RAM к виду "NN GB"
    df[ram_col] = (
        df[ram_col].astype(str)
        .str.replace("ГБ", "GB", regex=False)
        .str.replace("gb", "GB", case=False, regex=True)
        .str.replace(" ", "", regex=False)
        .str.upper()
        .str.replace("GB", " GB", regex=False)
        .str.strip()
    )

    # Переименуем в канонику внутри приложения
    df = df.rename(columns={
        cpu_col: "CPU", gpu_col: "GPU", ram_col: "RAM",
        gs_col: "Game Settings", lo_col: "Launch Options",
        cp_col: "Control Panel", win_col: "Windows Optimization",
        fps_col: "FPS Estimate", src_col: "Source"
    })

    return df

builds = load_builds()

# ──────────────────────────────────────────────────────────────────────────────
# ВСПОМОГАТЕЛЬНОЕ
# ──────────────────────────────────────────────────────────────────────────────
BANNED_FLAGS = {"-novid", "-nojoy"}

def clean_launch_options(s: str) -> str:
    if not isinstance(s, str):
        return ""
    toks = s.split()
    toks = [t for t in toks if t not in BANNED_FLAGS]
    cleaned = " ".join(toks).strip()
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned

def soft_match(df: pd.DataFrame, cpu: str, gpu: str, ram: str) -> pd.DataFrame:
    """Мягкий поиск: точное совпадение, иначе подберём близкие варианты."""
    exact = df[(df["CPU"] == cpu) & (df["GPU"] == gpu) & (df["RAM"] == ram)]
    if not exact.empty:
        return exact

    # Попробуем подобрать ближайшие по строковому сходству
    cpus = df["CPU"].dropna().astype(str).unique().tolist()
    gpus = df["GPU"].dropna().astype(str).unique().tolist()
    rams = df["RAM"].dropna().astype(str).unique().tolist()

    cpu_guess = get_close_matches(cpu, cpus, n=5, cutoff=0.6)
    gpu_guess = get_close_matches(gpu, gpus, n=5, cutoff=0.6)
    ram_guess = get_close_matches(ram, rams, n=5, cutoff=0.6)

    suggest = df[
        df["CPU"].isin(cpu_guess if cpu_guess else [cpu]) &
        df["GPU"].isin(gpu_guess if gpu_guess else [gpu]) &
        df["RAM"].isin(ram_guess if ram_guess else [ram])
    ]
    return suggest.head(10)

def render_result(row: pd.Series):
    launch_clean = clean_launch_options(row.get("Launch Options", ""))

    block = f"""
<div class="result-card">
  <h3>✅ Рекомендованные настройки</h3>
  <p><b>🖥 Процессор:</b> {row.get('CPU','')}</p>
  <p><b>🎮 Видеокарта:</b> {row.get('GPU','')}</p>
  <p><b>💾 ОЗУ:</b> {row.get('RAM','')}</p>

  <div class="hr"></div>

  <p><b>🎮 Настройки игры:</b><br>
  {row.get('Game Settings','')}</p>

  <p><b>🚀 Параметры запуска (очищенные):</b><br>
  <code>{launch_clean}</code></p>

  <p><b>🎛 Панель драйвера (NVIDIA/AMD):</b><br>
  {row.get('Control Panel','')}</p>

  <p><b>🪟 Оптимизация Windows (по желанию):</b><br>
  {row.get('Windows Optimization','')}</p>

  <div class="hr"></div>
  <p><b>📊 Ожидаемый FPS:</b> {row.get('FPS Estimate','—')}<br>
  <b>🔗 Источник:</b> {row.get('Source','')}</p>
</div>
"""
    st.markdown(block, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# ШАПКА + СОЦСЕТИ + ДОБРОЕ ПРЕДУПРЕЖДЕНИЕ ПРО ОЗУ
# ──────────────────────────────────────────────────────────────────────────────
st.title("⚙️ CS2 Конфигуратор (онлайн)")
st.caption("Подбери готовые настройки: игра, панель драйвера, параметры запуска и базовые оптимизации Windows. Поиск устойчив к регистру/пробелам и вариантам написания.")

# Соцсети (НЕ меняем макет — только стили)
st.markdown("""
<div class="social-row">
  <a class="btn-social btn-tiktok" href="https://www.tiktok.com/@melevik" target="_blank">TikTok</a>
  <a class="btn-social btn-youtube" href="https://youtube.com/@melevik-avlaron" target="_blank">YouTube</a>
  <a class="btn-social btn-twitch" href="https://m.twitch.tv/melevik/home" target="_blank">Twitch</a>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

st.markdown("""
<div class="warn-box">
  <div class="warn-title">Памятка по ОЗУ:</div>
  <div>Одноканальная память (1×8/1×16) даёт <b>ниже FPS и выше микрофризы</b>, чем двухканальная (2×8/2×16). Если у вас одна планка — ожидайте меньший FPS, чем в рекомендациях.</div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# ФИЛЬТРЫ ПО БАЗЕ
# ──────────────────────────────────────────────────────────────────────────────
left, right = st.columns([1.4, 1])

with left:
    col1, col2, col3 = st.columns(3)
    with col1:
        cpu_pick = st.selectbox("🖥 Процессор", sorted(builds["CPU"].dropna().unique().tolist()))
    with col2:
        gpu_pick = st.selectbox("🎮 Видеокарта", sorted(builds["GPU"].dropna().unique().tolist()))
    with col3:
        ram_pick = st.selectbox("💾 ОЗУ", sorted(builds["RAM"].dropna().unique().tolist()))

    if st.button("🔍 Найти настройки"):
        found = soft_match(builds, cpu_pick, gpu_pick, ram_pick)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        if found.empty:
            st.error("❌ Подходящей конфигурации не найдено.")
        else:
            # Если точное совпадение — выводим первую. Если «мягкий» матч — покажем все найденные (до 10)
            exact = builds[(builds["CPU"] == cpu_pick) & (builds["GPU"] == gpu_pick) & (builds["RAM"] == ram_pick)]
            if not exact.empty:
                render_result(exact.iloc[0])
            else:
                st.info("Похоже, точной записи нет. Вот близкие варианты:")
                for _, row in found.iterrows():
                    render_result(row)
                    st.markdown("")  # небольшой отступ

with right:
    st.markdown("#### 📡 Стрим и последнее видео")
    # Встраивание Twitch (если офлайн — Twitch покажет офлайн)
    st.components.v1.html(
        """
        <div style="position:relative;padding-top:56.25%;">
          <iframe src="https://player.twitch.tv/?channel=melevik&parent=streamlit.app"
                  height="100%" width="100%" frameborder="0" scrolling="no" allowfullscreen
                  style="position:absolute;top:0;left:0;width:100%;height:100%;">
          </iframe>
        </div>
        """,
        height=300
    )

    st.markdown("")
    # Встраивание YouTube: укажите ID нужного видео (лучше не Shorts).
    # Если у вас уже было рабочее встраивание — оставьте его; этот iframe безопасен по умолчанию.
    st.components.v1.html(
        """
        <div style="position:relative;padding-top:56.25%;">
          <iframe width="100%" height="100%"
                  src="https://www.youtube.com/embed?listType=user_uploads&list=melevik-avlaron"
                  title="YouTube"
                  frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowfullscreen
                  style="position:absolute;top:0;left:0;width:100%;height:100%;">
          </iframe>
        </div>
        """,
        height=300
    )

st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# ПРЕДУПРЕЖДЕНИЯ ПО ДРАЙВЕРАМ (НЕ МЕНЯЛИ СУТЬ — ТОЛЬКО СФОРМАТИРОВАЛ)
# ──────────────────────────────────────────────────────────────────────────────
with st.expander("⚠️ Важно: глобальные тумблеры драйверов (прочитать перед настройкой)"):
    st.markdown("""
<div class="warn-box">
  <div class="warn-title">AMD (Adrenalin):</div>
  <ul>
    <li>Не включайте «Radeon Chill», «Enhanced Sync», «Anti-Lag/Anti-Lag+» и «Radeon Super Resolution» <b>глобально</b>. Делайте профиль <b>только для CS2</b>.</li>
    <li>Морфологическое сглаживание, принудительное шумоподавление и «Surface Format Optimization» тоже держите <b>выкл</b> глобально.</li>
  </ul>
  <div class="warn-title">NVIDIA (Control Panel):</div>
  <ul>
    <li>«Предпочтительный режим производительности» и «Низкая задержка (Low Latency)» — ставьте в <b>профиле CS2</b>, а не глобально.</li>
    <li>V-Sync держите <b>выкл</b> в профиле CS2 (глобально лучше «Использовать настройку 3D-приложения»).</li>
  </ul>
  <div class="warn-title">Intel (Arc/IGPU):</div>
  <ul>
    <li>Параметры энергопитания и низкой задержки настраивайте <b>в профиле CS2</b>, не глобально, иначе это затронет всё.</li>
  </ul>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# БЛОК ПОДДЕРЖКИ (мягкая золотая пульсация) + КНОПКА ОБНОВЛЕНИЯ БАЗЫ
# ──────────────────────────────────────────────────────────────────────────────
left2, right2 = st.columns([1.4, 1])
with left2:
    st.markdown("""
<div class="support-box">
  <b>Каждый, кто поддержит рублём — попадёт в следующий ролик (в титры благодарности)!</b><br>
  👉 <a href="https://www.donationalerts.com/r/melevik" target="_blank" style="color:#1b1b1b;text-decoration:underline;font-weight:800;">Поддержать на DonatPay / DonationAlerts</a>
</div>
""", unsafe_allow_html=True)

with right2:
    if st.button("🔄 Обновить базу"):
        st.cache_data.clear()
        st.rerun()
