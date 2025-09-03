import pandas as pd
import streamlit as st

# Загружаем базу сборок
@st.cache_data
def load_data():
    return pd.read_csv("builds.csv")

df = load_data()

# Интерфейс
st.title("⚙️ Конфигуратор CS2")
st.write("Выбери свой ПК и получи готовые настройки для CS2!")

cpu = st.selectbox("🖥 CPU:", sorted(df["CPU"].unique()))
gpu = st.selectbox("🎮 GPU:", sorted(df["GPU"].unique()))
ram = st.selectbox("💾 RAM:", sorted(df["RAM"].unique()))

# Кнопка поиска
if st.button("🔍 Найти настройки"):
    result = df[
        (df["CPU"] == cpu) &
        (df["GPU"] == gpu) &
        (df["RAM"] == ram)
    ]

    st.markdown("---")  # разделитель

    if not result.empty:
        row = result.to_dict(orient="records")[0]

        st.subheader("✅ Рекомендованные настройки")

        st.markdown(f"""
        🖥 **CPU:** {row['CPU']}  
        🎮 **GPU:** {row['GPU']}  
        💾 **RAM:** {row['RAM']}  

        ⚙️ **Настройки игры:**  
        {row['Game Settings']}  

        🚀 **Параметры запуска:**  
        `{row['Launch Options']}`  

        🎛 **Панель управления (NVIDIA/AMD):**  
        {row['Control Panel']}  

        🪟 **Оптимизация Windows (по желанию):**  
        {row['Windows Optimization']}  

        🔗 **Источник:** {row['Source']}
        """)
    else:
        st.error("❌ Подходящей конфигурации не найдено.")

# Кнопка доната
st.markdown("---")
st.subheader("💖 Поддержи проект, чтобы обновления выходили быстрее")
st.markdown(
    """
    👉 [💸 DonatPay](https://www.donationalerts.com/r/melevik)  
    """,
    unsafe_allow_html=True
)




