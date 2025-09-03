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
if st.button("Показать настройки"):
    result = df[
        (df["CPU"] == cpu) &
        (df["GPU"] == gpu) &
        (df["RAM"] == ram)
 st.markdown("---")  # разделительная линия
st.subheader("💖 Поддержи проект рублем - что бы обновление выходило быстрее")

st.markdown(
    """
    Если тебе помог конфигуратор — поддержи разработку:
    
    👉 [❤️ Boosty](https://boosty.to/твоя_ссылка)  
    👉 [☕ Patreon](https://patreon.com/твоя_ссылка)  
    👉 [💸 DonatPay](https://donatepay.ru/твоя_ссылка)  
    """,
    unsafe_allow_html=True
)
    ]
    if not result.empty:
        st.subheader("✅ Рекомендованные настройки")
        st.write(result.to_dict(orient="records")[0])
    else:
        st.error("❌ Подходящей конфигурации не найдено.")


