import pandas as pd
import streamlit as st

st.set_page_config(page_title="CS2 Конфигуратор", page_icon="🎮")

@st.cache_data
def load_data():
    df = pd.read_csv("builds_full.csv")

    # Унификация названий столбцов
    def ensure_col(df, canon, variants):
        for v in variants:
            if v in df.columns:
                df[canon] = df[v]
                break
        if canon not in df.columns:
            df[canon] = ""  # пусто, если не нашли
        return df

    df = ensure_col(df, "Настройки игры", ["Game Settings", "Settings", "GameSettings"])
    df = ensure_col(df, "Параметры запуска", ["Launch Options", "Launch", "Params", "LaunchOptions"])
    df = ensure_col(df, "Панель драйвера", ["Control Panel", "ControlPanel", "Driver Settings", "Driver"])
    df = ensure_col(df, "Оптимизация Windows", ["Windows Optimization", "Windows Optimizations", "Windows", "Windows Opt"])
    df = ensure_col(df, "Ожидаемый FPS", ["FPS Estimate", "FPS", "FPS Range", "Estimate"])
    df = ensure_col(df, "Источник", ["Source"])

    # Стандартизируем RAM
    if "RAM" in df.columns:
        df["RAM"] = df["RAM"].astype(str).str.replace("GB", " ГБ", regex=False).str.replace("  ", " ", regex=False).str.strip()

    return df

df = load_data()

def clean_launch_options(s: str) -> str:
    if not isinstance(s, str):
        return ""
    tokens = s.split()
    # Убираем неактуальные флаги
    banned = {"-novid", "-nojoy"}
    tokens = [t for t in tokens if t not in banned]
    cleaned = " ".join(tokens)
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned.strip()

st.title("⚙️ Конфигуратор CS2")
st.caption("Подберите готовые настройки для вашей сборки ПК: игра, панель драйвера, параметры запуска и оптимизации Windows.")

# Фильтры
cpu = st.selectbox("🖥 Процессор (CPU):", sorted(df["CPU"].dropna().unique()))
gpu = st.selectbox("🎮 Видеокарта (GPU):", sorted(df["GPU"].dropna().unique()))
ram = st.selectbox("💾 Оперативная память (RAM):", sorted(df["RAM"].dropna().unique()))

# Поиск
if st.button("🔍 Найти настройки"):
    result = df[(df["CPU"] == cpu) & (df["GPU"] == gpu) & (df["RAM"] == ram)]

    st.markdown("---")

    if result.empty:
        st.error("❌ Подходящей конфигурации не найдено в базе.")
    else:
        row = result.iloc[0].to_dict()
        launch_raw = row.get("Параметры запуска", "")
        launch_clean = clean_launch_options(launch_raw)

        st.subheader("✅ Рекомендованные настройки")
        st.markdown(
            f"""
**🖥 Процессор:** {row.get('CPU','')}
**🎮 Видеокарта:** {row.get('GPU','')}
**💾 Оперативная память:** {row.get('RAM','')}

**🎮 Настройки игры:**  
{row.get('Настройки игры','')}

**🚀 Параметры запуска (очищенные):**  
`{launch_clean}`

**🎛 Панель драйвера (NVIDIA/AMD):**  
{row.get('Панель драйвера','')}

**🪟 Оптимизация Windows (по желанию):**  
{row.get('Оптимизация Windows','')}

**📊 Ожидаемый FPS:** {row.get('Ожидаемый FPS','—')}
**🔗 Источник:** {row.get('Источник','')}
"""
        )

        # Кнопка скачать профиль
        profile_txt = (
            f"CPU: {row.get('CPU','')}\n"
            f"GPU: {row.get('GPU','')}\n"
            f"RAM: {row.get('RAM','')}\n\n"
            f"[Настройки игры]\n{row.get('Настройки игры','')}\n\n"
            f"[Параметры запуска]\n{launch_clean}\n\n"
            f"[Панель драйвера]\n{row.get('Панель драйвера','')}\n\n"
            f"[Оптимизация Windows]\n{row.get('Оптимизация Windows','')}\n\n"
            f"Ожидаемый FPS: {row.get('Ожидаемый FPS','—')}\n"
            f"Источник: {row.get('Источник','')}\n"
        )
        st.download_button("💾 Скачать профиль (.txt)", data=profile_txt, file_name="cs2_profile.txt")

st.markdown("---")
st.subheader("💖 Поддержи проект")
st.markdown("👉 [💸 DonatPay](https://www.donationalerts.com/r/melevik)", unsafe_allow_html=True)
st.caption("Чем больше поддержка — тем быстрее обновляется и расширяется база.")

