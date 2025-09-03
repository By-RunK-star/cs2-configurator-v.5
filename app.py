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

cpu = st.selectbox("🖥 Выбери процессор (CPU):", sorted(df["CPU"].unique()))
gpu = st.selectbox("🎮 Выбери видеокарту (GPU):", sorted(df["GPU"].unique()))
ram = st.selectbox("💾 Выбери объём оперативной памяти (RAM):", sorted(df["RAM"].unique()))

# Кнопка поиска
if st.button("Найти настройки"):
    result = df[
        (df["CPU"] == cpu) &
        (df["GPU"] == gpu) &
        (df["RAM"] == ram)
    ]
    if not result.empty:
        row = result.iloc[0]

        # Форматированный вывод на русском
        st.subheader("✅ Рекомендованные настройки")

        st.write(f"🖥 **Процессор (CPU):** {row['CPU']}")
        st.write(f"🎮 **Видеокарта (GPU):** {row['GPU']}")
        st.write(f"💾 **Оперативная память (RAM):** {row['RAM']}")

        st.markdown("### 🎮 Графика в игре:")
        st.write(row["Game Settings"])

        st.markdown("### 🚀 Параметры запуска:")
        st.code(row["Launch Options"], language="bash")

        st.markdown("### 🎛 Настройки драйвера (NVIDIA/AMD):")
        st.write(row["Control Panel"])

        st.markdown("### 🪟 Оптимизация Windows (по желанию):")
        st.write(row["Windows Optimization"])

        st.markdown(f"### 📊 Ожидаемый FPS: **{row['Expected FPS']}**")

        st.markdown(f"🔗 **Источник:** {row['Source']}")

    else:
        st.error("❌ Подходящей конфигурации не найдено.")

# Разделитель и блок доната
st.markdown("---")
st.subheader("💖 Поддержи проект рублем – чтобы обновления выходили быстрее")

st.markdown(
    """
    Если тебе помог конфигуратор — поддержи разработку:  
    👉 [💸 DonatPay](https://www.donationalerts.com/r/melevik)  
    """,
    unsafe_allow_html=True
)
