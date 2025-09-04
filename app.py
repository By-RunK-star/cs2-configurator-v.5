import pandas as pd
import streamlit as st

# =========================
# БАЗОВАЯ КОНФИГУРАЦИЯ
# =========================
st.set_page_config(page_title="CS2 Конфигуратор", page_icon="🎮", layout="wide")

# =========================
# СТИЛИ (тёмная карточка + донат-баннер с жёлтым переливом)
# =========================
st.markdown("""
<style>
/* Карточка результата (тёмная) */
.result-card {
  background: #0e1117;
  border: 1px solid #222632;
  border-radius: 12px;
  padding: 18px 20px;
  color: #e6e6e6;
  line-height: 1.5;
  box-shadow: 0 0 0 1px #141823 inset;
}

/* Донат-баннер: мягкий переливающийся жёлтый */
.donate-wrap {
  position: relative;
  margin: 12px 0 4px 0;
}
.donate-banner {
  background: linear-gradient(90deg, #FFDD33, #FFC300, #FFD84D, #FFB703, #FFDD33);
  background-size: 300% 300%;
  animation: gradientFlow 6s ease infinite;
  border-radius: 12px;
  padding: 14px 16px;
  color: #1a1a1a;
  font-weight: 600;
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 6px 18px rgba(255, 199, 0, 0.15);
}
.donate-left {
  display: flex; flex-direction: column; gap: 6px;
}
.donate-title {
  font-size: 16px; margin: 0; padding: 0; letter-spacing: 0.2px;
}
.donate-sub {
  font-weight: 500; opacity: 0.85; margin: 0;
}

/* Неброская пульсация значка монетки */
@keyframes softPulse {
  0% { transform: scale(1); filter: drop-shadow(0 0 0 rgba(255, 183, 3, 0)); }
  50% { transform: scale(1.05); filter: drop-shadow(0 0 10px rgba(255, 183, 3, .45)); }
  100% { transform: scale(1); filter: drop-shadow(0 0 0 rgba(255, 183, 3, 0)); }
}
.coin {
  font-size: 22px; animation: softPulse 2.8s ease-in-out infinite;
}

/* Плавный перелив */
@keyframes gradientFlow {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

/* Кнопка-ссылка внутри баннера */
.donate-btn {
  background: rgba(0,0,0,0.1);
  color: #1a1a1a;
  text-decoration: none;
  padding: 8px 14px;
  border-radius: 10px;
  font-weight: 700;
  border: 1px solid rgba(0,0,0,0.08);
}
.donate-btn:hover {
  background: rgba(0,0,0,0.18);
}

/* Соц-иконки */
.soc-row {
  display:flex; gap:12px; align-items:center; flex-wrap:wrap;
}
.soc-btn {
  display:inline-flex; align-items:center; gap:8px;
  border:1px solid #2a2f3a; border-radius:10px;
  padding:8px 12px; text-decoration:none; color:#e6e6e6;
  background:#11151b;
}
.soc-btn:hover { background:#171c24; border-color:#394253; }
.soc-ico { font-size:18px; }
</style>
""", unsafe_allow_html=True)

# =========================
# ЗАГРУЗКА БАЗЫ
# =========================
@st.cache_data
def load_data():
    df = pd.read_csv("builds.csv")

    # Нормализуем столбцы до канона
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

    # Стандартизируем RAM
    if "RAM" in df.columns:
        df["RAM"] = (df["RAM"].astype(str)
            .str.replace("GB", " GB", regex=False)
            .str.replace("  ", " ", regex=False)
            .str.strip())

    return df

df = load_data()

# Чистим параметры запуска от устаревших ключей
def clean_launch_options(s: str) -> str:
    if not isinstance(s, str):
        return ""
    tokens = s.split()
    banned = {"-novid", "-nojoy"}  # в CS2 не применяются
    tokens = [t for t in tokens if t not in banned]
    cleaned = " ".join(tokens)
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned.strip()

# =========================
# UI: ШАПКА + ФИЛЬТРЫ
# =========================
st.title("⚙️ Конфигуратор CS2")
st.caption("Подбери готовые настройки по своей сборке (игра, панель драйвера, параметры запуска, Windows-оптимизации).")

colA, colB, colC, colR = st.columns([1.1, 1.1, 0.8, 0.6])
with colA:
    cpu = st.selectbox("🖥 Процессор (CPU)", sorted(df["CPU"].dropna().unique()))
with colB:
    gpu = st.selectbox("🎮 Видеокарта (GPU)", sorted(df["GPU"].dropna().unique()))
with colC:
    ram = st.selectbox("💾 ОЗУ (RAM)", sorted(df["RAM"].dropna().unique()))
with colR:
    if st.button("🔄 Обновить базу"):
        st.rerun()

# Предупреждение о канальности ОЗУ (без фильтра)
st.info("💡 Важно: в **одноканальном** режиме (1 планка) FPS обычно ниже на **10–25%**, чем в **двухканальном** (2×). Если есть возможность — ставь 2 планки одинакового объёма/частоты.")

# =========================
# ПОИСК
# =========================
if st.button("🔍 Найти настройки"):
    result = df[(df["CPU"] == cpu) & (df["GPU"] == gpu) & (df["RAM"] == ram)]
    st.markdown("---")
    if result.empty:
        st.error("❌ Подходящей конфигурации не найдено в базе.")
    else:
        row = result.iloc[0].to_dict()
        launch_clean = clean_launch_options(row.get("Launch Options", ""))

        st.subheader("✅ Рекомендованные настройки")
        st.markdown(
            f"""
<div class="result-card">
<b>🖥 Процессор:</b> {row.get('CPU','')}<br>
<b>🎮 Видеокарта:</b> {row.get('GPU','')}<br>
<b>💾 ОЗУ:</b> {row.get('RAM','')}
<hr style="border: 1px solid #222632;">

<b>🎮 Настройки игры:</b><br>
{row.get('Game Settings','')}

<br><b>🚀 Параметры запуска (очищенные):</b><br>
<code>{launch_clean}</code>

<br><b>🎛 Панель драйвера (NVIDIA/AMD):</b><br>
{row.get('Control Panel','')}

<br><b>🪟 Оптимизация Windows (по желанию):</b><br>
{row.get('Windows Optimization','')}

<br><b>📊 Ожидаемый FPS:</b> {row.get('FPS Estimate','—')} &nbsp;&nbsp;
<span style="opacity:.7">(<b>Источник:</b> {row.get('Source','')})</span>
</div>
""",
            unsafe_allow_html=True
        )

        # Скачать профиль
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

# =========================
# ДОБРОВОЛЬНАЯ ПОДДЕРЖКА
# =========================
st.markdown('<div class="donate-wrap">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="donate-banner">
      <div class="donate-left">
        <div class="donate-title">💛 <span class="coin">🪙</span> Поддержи проект рублём — попади в следующий ролик!</div>
        <div class="donate-sub">Любая сумма помогает мне быстрее обновлять базу и допиливать фишки на сайте.</div>
      </div>
      <a class="donate-btn" href="https://www.donationalerts.com/r/melevik" target="_blank" rel="noopener noreferrer">Поддержать</a>
    </div>
    """,
    unsafe_allow_html=True
)
st.caption("Спасибо каждому за участие — имена донатеров добавляю в титры следующего видео ✨")

# =========================
# СОЦСЕТИ (как было)
# =========================
st.markdown("---")
st.subheader("Подписывайся, чтобы следить за актуальными обновлениями и контентом автора")
st.markdown(
    """
    <div class="soc-row">
      <a class="soc-btn" href="https://www.tiktok.com/@melevik?_t=ZS-8zQkTQnA4Pf&_r=1" target="_blank" rel="noopener noreferrer">
        <span class="soc-ico">🎵</span> TikTok
      </a>
      <a class="soc-btn" href="https://youtube.com/@melevik-avlaron?si=kRXrCD7GUrVnk478" target="_blank" rel="noopener noreferrer">
        <span class="soc-ico">▶️</span> YouTube
      </a>
      <a class="soc-btn" href="https://m.twitch.tv/melevik/home" target="_blank" rel="noopener noreferrer">
        <span class="soc-ico">🟣</span> Twitch
      </a>
    </div>
    """,
    unsafe_allow_html=True
)

st.caption("База подтягивается из файла builds.csv в корне репозитория. Кнопка «Обновить базу» перечитывает файл и перерисовывает интерфейс.")

