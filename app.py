import streamlit as st
import pandas as pd

# Заголовок
st.set_page_config(page_title="CS2 Configurator", layout="centered", page_icon="🎮")

st.title("🎮 CS2 Configurator")
st.markdown("Найди оптимальные настройки под своё железо")

# Загружаем базу
@st.cache_data
def load_builds():
    return pd.read_csv("builds.csv")

builds = load_builds()

# ----------------------- Ввод пользователя -----------------------
cpu = st.selectbox("Выбери процессор", sorted(builds["cpu"].unique()))
gpu = st.selectbox("Выбери видеокарту", sorted(builds["gpu"].unique()))
ram_user = st.number_input("Укажи объём RAM (ГБ)", min_value=4, max_value=64, value=16, step=4)

# ----------------------- Поиск конфигурации -----------------------
matches = builds[(builds["cpu"] == cpu) & (builds["gpu"] == gpu)]

if not matches.empty:
    # Проверяем RAM по диапазону
    row = None
    for _, r in matches.iterrows():
        if r["ram_min"] <= ram_user <= r["ram_max"]:
            row = r
            break
    if row is None:
        row = matches.iloc[0]
        st.warning("⚠️ Указанный объём RAM больше/меньше, чем в базе. Результат может отличаться.")

    st.subheader("✅ Рекомендованные настройки")
    st.markdown(
        f"""
        <div style="background-color:#000000; color:white; padding:15px; border-radius:10px;">
        🖥 Процессор: {row['cpu']}  
        🎮 Видеокарта: {row['gpu']}  
        💾 Оперативная память: {ram_user} ГБ  

        🎮 Настройки игры: {row['settings']}  
        🖥 Разрешение: {row['resolution']}  
        📊 Ожидаемый FPS: {row['fps']}
        </div>
        """,
        unsafe_allow_html=True
    )

else:
    st.error("❌ Конфигурация не найдена. Обнови базу или проверь ввод.")

# ----------------------- Предупреждения -----------------------
st.markdown("### ⚠️ Важно")
st.info("Одноканальная память = FPS ниже. Двухканальная память = FPS выше.")
st.warning("AMD: в глобальных настройках драйвера не включайте лишние оптимизации — это может снизить FPS.")
st.warning("Intel: отключите энергосбережение CPU в Windows (часто снижает производительность).")

# ----------------------- Поддержка проекта -----------------------
st.markdown(
    """
    <div style="background:#222; padding:20px; border-radius:10px; text-align:center;">
      <a href="https://www.donationalerts.com/r/melevik" target="_blank"
         style="
           background: linear-gradient(90deg, #FFD700, #FFA500, #FFD700);
           background-size: 200% 200%;
           color:black;
           padding:12px 20px;
           border-radius:8px;
           text-decoration:none;
           font-weight:bold;
           display:inline-block;
           animation:pulse 2s infinite;
         ">
         💛 Поддержи проект — каждый донатер попадёт в следующий ролик
      </a>
    </div>
    <style>
    @keyframes pulse {
      0% { box-shadow: 0 0 5px #FFD700; }
      50% { box-shadow: 0 0 20px #FFA500; }
      100% { box-shadow: 0 0 5px #FFD700; }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------- Соцсети -----------------------
st.markdown("#### Подписывайся, чтобы следить за актуальными обновлениями и контентом автора")
st.markdown(
    """
    <div class="socials">
      <a class="btn-social btn-yt"   href="https://youtube.com/@melevik-avlaron" target="_blank">YouTube</a>
      <a class="btn-social btn-tktk" href="https://www.tiktok.com/@melevik?_t=ZS-8zQkTQnA4Pf&_r=1" target="_blank">TikTok</a>
      <a class="btn-social btn-tw"   href="https://m.twitch.tv/melevik/home" target="_blank">Twitch</a>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    .socials { display:flex; gap:10px; flex-wrap:wrap; }
    .btn-social { padding:10px 15px; border-radius:6px; color:white; text-decoration:none; font-weight:bold; }
    .btn-yt { background:#FF0000; }
    .btn-tktk { background:#000000; border:1px solid #222; }
    .btn-tw { background:#9146FF; }
    </style>
    """,
    unsafe_allow_html=True
)
