import pandas as pd
import streamlit as st

# Загружаем базу
@st.cache_data
def load_data():
    return pd.read_csv("builds.csv")

df = load_data()

# Заголовок
st.title("⚙️ Конфигуратор CS2")
st.write("Выбери свой ПК и получи готовые настройки для CS2!")

# Фильтры
cpu = st.selectbox("Выбери процессор:", sorted(df["CPU"].unique()))
gpu = st.selectbox("Выбери видеокарту:", sorted(df["GPU"].unique()))
ram = st.selectbox("Выбери объём ОЗУ:", sorted(df["RAM"].unique()))

# Кнопка поиска
if st.button("Найти настройки"):
    result = df[
        (df["CPU"] == cpu) &
        (df["GPU"] == gpu) &
        (df["RAM"] == ram)
    ]
    if not result.empty:
        st.subheader("✅ Рекомендованные настройки")

        # Берем первую найденную строку
        row = result.iloc[0]

        # Делаем красивый вывод
        st.markdown(f"""
        **🖥 CPU:** {row['CPU']}  
        **🎮 GPU:** {row['GPU']}  
        **💾 RAM:** {row['RAM']}  

        **⚙️ Настройки игры:** {row['Game Settings']}  
        **🚀 Параметры запуска:** {row['Launch Options']}  
        **🎛 Панель управления:** {row['Control Panel']}  

        🔗 *Источник:* {row['Source']}
        """)
    else:
        st.error("❌ Подходящей конфигурации не найдено.")


# --- Блок поддержки
st.markdown("---")  # разделительная линия
st.subheader("💖 Поддержи проект рублем - чтобы обновления выходили быстрее")

st.markdown(
    """
    Если тебе помог конфигуратор — поддержи разработку:  
    👉 [💸 DonatPay](https://www.donationalerts.com/r/melevik)
    """,
    unsafe_allow_html=True
)



