import pandas as pd
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="CS2 Конфигуратор", page_icon="🎮", layout="centered")

# ============================
# 🔗 Откуда брать базу
# ============================
# 👉 Поставь сюда свою RAW-ссылку на builds.csv из GitHub (например:
# https://raw.githubusercontent.com/<user>/<repo>/main/builds.csv)
RAW_CSV_URL = "https://raw.githubusercontent.com/<user>/<repo>/main/builds.csv"

# ============================
# 📂 Загрузка базы (всегда актуальная)
# ============================
@st.cache_data(ttl=60)  # кеш максимум на 60 секунд
def load_data():
    # 1) пробуем загрузить по URL (самая свежая версия из GitHub)
    try:
        df = pd.read_csv(RAW_CSV_URL)
        source = "remote"
    except Exception:
        # 2) если не вышло — читаем локальный файл из репозитория
        df = pd.read_csv("builds.csv")
        source = "local"

    # Унификация названий столбцов
    def ensure_col(df, canon, variants):
        for v in variants:
            if v in df.columns:
                df[canon] = df[v]
                break
        if canon not in df.columns:
            df[canon] = ""
        return df

    df = ensure_col(df, "CPU", ["CPU", "Cpu", "Processor"])
    df = ensure_col(df, "GPU", ["GPU", "Gpu", "Graphics"])
    df = ensure_col(df, "RAM", ["RAM", "Memory"])
    df = ensure_col(df, "Game Settings", ["Game Settings", "Settings", "GameSettings"])
    df = ensure_col(df, "Launch Options", ["Launch Options", "Launch", "Params", "LaunchOptions"])
    df = ensure_col(df, "Control Panel", ["Control Panel", "Driver Settings", "Driver"])
    df = ensure_col(df, "Windows Optimization", ["Windows Optimization", "Windows Opt", "Windows"])
    df = ensure_col(df, "FPS Estimate", ["FPS Estimate", "FPS", "FPS Range"])
    df = ensure_col(df, "Source", ["Source"])

    # RAM → единый вид
    if "RAM" in df.columns:
        df["RAM"] = (
            df["RAM"].astype(str)
            .str.replace("GB", " ГБ", regex=False)
            .str.replace("  ", " ", regex=False)
            .str.strip()
        )

    return df, source, datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================
# 🔧 Очистка параметров запуска
# ============================
def clean_launch_options(s: str) -> str:
    if not isinstance(s, str):
        return ""
    tokens = s.split()
    banned = {"-novid", "-nojoy"}  # убираем неактуальные для CS2
    tokens = [t for t in tokens if t not in banned]
    return " ".join(tokens).strip()


# ============================
# 🎮 Интерфейс
# ============================
st.title("⚙️ CS2 Конфигуратор")
st.caption("Подбери готовые настройки для своей сборки: игра, панель драйвера, параметры запуска и оптимизация Windows.")

# Кнопка обновления базы (мгновенно очищает кеш и перезапускает приложение)
col_refresh, col_info = st.columns([1, 3])
with col_refresh:
    if st.button("🔄 Обновить базу"):
        st.cache_data.clear()
        st.experimental_rerun()

df, data_source, loaded_at = load_data()
with col_info:
    st.markdown(
        f"<div style='font-size:12px;opacity:0.8'>Источник: <b>{'GitHub RAW' if data_source=='remote' else 'Локальный файл'}</b> • Обновлено: {loaded_at}</div>",
        unsafe_allow_html=True
    )

# Фильтры
cpu = st.selectbox("🖥 Процессор:", sorted(df["CPU"].dropna().unique()))
gpu = st.selectbox("🎮 Видеокарта:", sorted(df["GPU"].dropna().unique()))
ram = st.selectbox("💾 Оперативная память:", sorted(df["RAM"].dropna().unique()))

# Поиск
if st.button("🔍 Найти настройки"):
    result = df[(df["CPU"] == cpu) & (df["GPU"] == gpu) & (df["RAM"] == ram)]
    st.markdown("---")

    if result.empty:
        st.error("❌ Подходящей конфигурации не найдено.")
    else:
        row = result.iloc[0].to_dict()
        launch_clean = clean_launch_options(row.get("Launch Options", ""))

        # Карточка результата
        st.markdown(
            f"""
<div style="padding:16px;border:1px solid #30363d;border-radius:12px;background:#0e1117;">
  <div style="font-size:18px;margin-bottom:8px;"><b>✅ Рекомендованные настройки</b></div>

  <div><b>🖥 Процессор:</b> {row.get('CPU','')}</div>
  <div><b>🎮 Видеокарта:</b> {row.get('GPU','')}</div>
  <div><b>💾 Оперативная память:</b> {row.get('RAM','')}</div>

  <hr style="border:0;border-top:1px solid #30363d;margin:12px 0;">

  <div><b>🎮 Настройки игры:</b><br>{row.get('Game Settings','')}</div>

  <div style="margin-top:8px;"><b>🚀 Параметры запуска (очищенные):</b><br><code>{launch_clean}</code></div>

  <div style="margin-top:8px;"><b>🎛 Панель драйвера (NVIDIA/AMD):</b><br>{row.get('Control Panel','')}</div>

  <div style="margin-top:8px;"><b>🪟 Оптимизация Windows (по желанию):</b><br>{row.get('Windows Optimization','')}</div>

  <div style="margin-top:8px;"><b>📊 Ожидаемый FPS:</b> {row.get('FPS Estimate','—')}</div>
  <div><b>🔗 Источник:</b> {row.get('Source','')}</div>
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

# ============================
# 🌍 Соцсети (плашки)
# ============================
st.markdown("---")
st.subheader("🌍 Мои соцсети")
soc_cols = st.columns(3)
with soc_cols[0]:
    st.markdown(
        "<a href='https://www.tiktok.com/@melevik?_t=ZS-8zQkTQnA4Pf&_r=1' target='_blank' style='text-decoration:none;'>"
        "<div style='text-align:center;padding:10px;border:1px solid #30363d;border-radius:10px;'>🎵 TikTok</div>"
        "</a>",
        unsafe_allow_html=True
    )
with soc_cols[1]:
    st.markdown(
        "<a href='https://youtube.com/@melevik-avlaron?si=kRXrCD7GUrVnk478' target='_blank' style='text-decoration:none;'>"
        "<div style='text-align:center;padding:10px;border:1px solid #30363d;border-radius:10px;'>▶️ YouTube</div>"
        "</a>",
        unsafe_allow_html=True
    )
with soc_cols[2]:
    st.markdown(
        "<a href='https://m.twitch.tv/melevik/home' target='_blank' style='text-decoration:none;'>"
        "<div style='text-align:center;padding:10px;border:1px solid #30363d;border-radius:10px;'>🎮 Twitch</div>"
        "</a>",
        unsafe_allow_html=True
    )

# ============================
# 💖 Донат
# ============================
st.markdown("---")
st.subheader("💖 Поддержи проект")
st.markdown(
    """
👉 [💸 DonatPay](https://www.donationalerts.com/r/melevik)  

**Каждый, кто поддержит проект рублём — попадёт в следующий ролик 🎥**  
""",
    unsafe_allow_html=True
)
st.caption("Твоя поддержка ускоряет обновления базы и делает проект лучше 🚀")




