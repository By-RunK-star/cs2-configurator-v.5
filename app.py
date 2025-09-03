import pandas as pd
import streamlit as st

# ⚙️ Настройки страницы
st.set_page_config(page_title="CS2 Конфигуратор", page_icon="🎮")

# 📂 Загрузка базы
@st.cache_data
def load_data():
    df = pd.read_csv("builds.csv")

    # Нормализуем названия столбцов → приводим к канону
    def ensure_col(df, canon, variants):
        for v in variants:
            if v in df.columns:
                df[canon] = df[v]
                break
        if canon not in df.columns:
            df[canon] = ""  # пусто, если не нашли
        return df

    df = ensure_col(df, "Game Settings", ["Game Settings", "Settings", "GameSettings"])
    df = ensure_col(df, "Launch Options", ["Launch Options", "Launch", "Params", "LaunchOptions"])
    df = ensure_col(df, "Control Panel", ["Control Panel", "ControlPanel", "Driver Settings", "Driver"])
    df = ensure_col(df, "Windows Optimization", ["Windows Optimization", "Windows Optimizations", "Windows", "Windows Opt"])
    df = ensure_col(df, "FPS Estimate", ["FPS Estimate", "FPS", "FPS Range", "Estimate"])
    df = ensure_col(df, "Source", ["Source"])

    # Стандартизируем RAM
    if "RAM" in df.columns:
        df["RAM"] = (
            df["RAM"]
            .astype(str)
            .str.replace("GB", " ГБ", regex=False)
            .str.replace("  ", " ", regex=False)
            .str.strip()
        )

    return df


df = load_data()

# 🚀 Очистка параметров запуска
def clean_launch_options(s: str) -> str:
    if not isinstance(s, str):
        return ""
    tokens = s.split()
    banned = {"-novid", "-nojoy"}  # неактуальные флаги
    tokens = [t for t in tokens if t not in banned]
    cleaned = " ".join(tokens)
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned.strip()


# 🖥 Заголовок
st.title("⚙️ Конфигуратор CS2")
st.caption("Подбери готовые настройки под свою сборку (игра, драйвер, параметры запуска, Windows-оптимизации).")

# 🔍 Фильтры
cpu = st.selectbox("🖥 Процессор:", sorted(df["CPU"].dropna().unique()))
gpu = st.selectbox("🎮 Видеокарта:", sorted(df["GPU"].dropna().unique()))
ram = st.selectbox("💾 Оперативная память:", sorted(df["RAM"].dropna().unique()))

# 🔎 Поиск
if st.button("🔍 Найти настройки"):
    result = df[(df["CPU"] == cpu) & (df["GPU"] == gpu) & (df["RAM"] == ram)]

    st.markdown("---")

    if result.empty:
        st.error("❌ Подходящей конфигурации не найдено в базе.")
    else:
        row = result.iloc[0].to_dict()
        launch_raw = row.get("Launch Options", "")
        launch_clean = clean_launch_options(launch_raw)

        st.subheader("✅ Рекомендованные настройки")
        st.markdown(
            f"""
**🖥 Процессор:** {row.get('CPU','')}
**🎮 Видеокарта:** {row.get('GPU','')}
**💾 Оперативная память:** {row.get('RAM','')}

**🎮 Настройки игры:**  
{row.get('Game Settings','')}

**🚀 Параметры запуска (очищенные):**  
`{launch_clean}`

**🎛 Панель драйвера (NVIDIA/AMD):**  
{row.get('Control Panel','')}

**🪟 Оптимизация Windows (по желанию):**  
{row.get('Windows Optimization','')}

**📊 Ожидаемый FPS:** {row.get('FPS Estimate','—')}
**🔗 Источник:** {row.get('Source','')}
"""
        )

        # 📥 Скачать профиль как txt
        profile_txt = (
            f"CPU: {row.get('CPU','')}\n"
            f"GPU: {row.get('GPU','')}\n"
            f"RAM: {row.get('RAM','')}\n\n"
            f"[Настройки игры]\n{row.get('Game Settings','')}\n\n"
            f"[Параметры запуска]\n{launch_clean}\n\n"
            f"[Панель драйвера]\n{row.get('Control Panel','')}\n\n"
            f"[Оптимизация Windows]\n{row.get('Windows Optimization','')}\n\n"
            f"FPS: {row.get('FPS Estimate','—')}\n"
            f"Источник: {row.get('Source','')}\n"
        )
        st.download_button("💾 Скачать профиль (.txt)", data=profile_txt, file_name="cs2_profile.txt")

# 🔄 Кнопка обновления базы
col_refresh, col_info = st.columns([1, 3])
with col_refresh:
    if st.button("🔄 Обновить базу"):
        st.cache_data.clear()
        st.rerun()

# --- Соцсети ---
st.markdown("---")
st.subheader("🌍 Соцсети")
st.markdown(
    """
    [🎮 Twitch](https://m.twitch.tv/melevik/home)  
    [▶️ YouTube](https://youtube.com/@melevik-avlaron?si=kRXrCD7GUrVnk478)  
    [🎵 TikTok](https://www.tiktok.com/@melevik?_t=ZS-8zQkTQnA4Pf&_r=1)  
    """,
    unsafe_allow_html=True,
)

# --- Донат ---
st.markdown("---")
st.subheader("💖 Поддержи проект")
st.markdown("👉 [💸 DonatPay](https://www.donationalerts.com/r/melevik)", unsafe_allow_html=True)
st.caption("Каждый, кто поддержит проект рублём — попадёт в следующий ролик 🙌")




