import pandas as pd
import streamlit as st

st.set_page_config(page_title="CS2 Конфигуратор", page_icon="🎮")

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

    # Стандартизируем RAM (на всякий случай)
    if "RAM" in df.columns:
        df["RAM"] = df["RAM"].astype(str).str.replace("GB", " GB", regex=False).str.replace("  ", " ", regex=False).str.strip()

    return df

df = load_data()

def clean_launch_options(s: str) -> str:
    if not isinstance(s, str):
        return ""
    tokens = s.split()
    # Убираем неактуальные флаги для CS2
    banned = {"-novid", "-nojoy"}
    tokens = [t for t in tokens if t not in banned]
    # Склеиваем обратно
    cleaned = " ".join(tokens)
    # Чуть подчистим двойные пробелы
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned.strip()

st.title("⚙️ Конфигуратор CS2")
st.caption("Подбери готовые настройки по своей сборке (игра, панель драйвера, параметры запуска, Windows-оптимизации).")

# Фильтры
cpu = st.selectbox("🖥 CPU:", sorted(df["CPU"].dropna().unique()))
gpu = st.selectbox("🎮 GPU:", sorted(df["GPU"].dropna().unique()))
ram = st.selectbox("💾 RAM:", sorted(df["RAM"].dropna().unique()))

# Поиск
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
**🖥 CPU:** {row.get('CPU','')}
**🎮 GPU:** {row.get('GPU','')}
**💾 RAM:** {row.get('RAM','')}

**🎮 Настройки игры:**  
{row.get('Game Settings','')}

**🚀 Параметры запуска (очищено):**  
`{launch_clean}`

**🎛 Панель драйвера (NVIDIA/AMD):**  
{row.get('Control Panel','')}

**🪟 Оптимизация Windows (по желанию):**  
{row.get('Windows Optimization','')}

**📊 Ожидаемый FPS:** {row.get('FPS Estimate','—')}
**🔗 Источник:** {row.get('Source','')}
"""
        )

        # Кнопка скачать профиль как .txt
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

st.markdown("---")
st.subheader("💖 Поддержи проект")
st.markdown("👉 [💸 DonatPay](https://www.donationalerts.com/r/melevik)", unsafe_allow_html=True)
st.caption("Чем больше поддержка — тем чаще обновляем и расширяем базу.")
