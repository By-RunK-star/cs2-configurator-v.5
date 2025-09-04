import streamlit as st
import pandas as pd

# Загружаем базу конфигураций
@st.cache_data
def load_data():
    return pd.read_csv("builds.csv")

builds = load_data()

st.set_page_config(page_title="⚙️ CS2 Конфигуратор", layout="wide")

# Заголовок
st.title("⚙️ CS2 Конфигуратор (онлайн)")
st.markdown("Подбери готовые настройки: игра, панель драйвера, параметры запуска и оптимизации Windows. "
            "Поиск устойчив к регистру/пробелам и вариантам написания.")

# Выбор компонентов
cpu = st.selectbox("🖥 Процессор", sorted(builds["cpu"].unique()))
gpu = st.selectbox("🎮 Видеокарта", sorted(builds["gpu"].unique()))
ram = st.selectbox("💾 ОЗУ", sorted(builds["ram"].unique()))

# Фильтрация по выбранным параметрам
result = builds[(builds["cpu"] == cpu) & (builds["gpu"] == gpu) & (builds["ram"] == ram)]

# Блок поддержки проекта
st.markdown(
    """
    <div style="text-align:center; margin:20px 0;">
        <div style="animation:pulse 2s infinite; display:inline-block;
                    background:linear-gradient(90deg, #FFD700, #FFEE32);
                    padding:12px 22px; border-radius:8px; font-size:18px; font-weight:bold; color:black;">
            💛 Каждый, кто поддержит рублём — попадёт в следующий ролик (в титры благодарности)!
        </div>
        <style>
            @keyframes pulse {
                0% { box-shadow: 0 0 0 0 rgba(255,215,0,0.7); }
                70% { box-shadow: 0 0 20px 15px rgba(255,215,0,0); }
                100% { box-shadow: 0 0 0 0 rgba(255,215,0,0); }
            }
        </style>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("👉 Поддержать на [DonatPay](https://donatpay.ru) / [DonationAlerts](https://www.donationalerts.com)")

# Соцсети — кнопки в цвете площадок
st.markdown(
    """
    <div style="display:flex; justify-content:center; gap:15px; margin:20px 0;">
        <a href="https://www.tiktok.com/@melevik" target="_blank"
           style="background:#000; color:white; padding:10px 18px; border-radius:6px; font-weight:bold; text-decoration:none;">
           🎵 TikTok
        </a>
        <a href="https://youtube.com/@melevik-avlaron" target="_blank"
           style="background:#FF0000; color:white; padding:10px 18px; border-radius:6px; font-weight:bold; text-decoration:none;">
           ▶️ YouTube
        </a>
        <a href="https://m.twitch.tv/melevik/home" target="_blank"
           style="background:#9146FF; color:white; padding:10px 18px; border-radius:6px; font-weight:bold; text-decoration:none;">
           🎥 Twitch
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)

# Twitch — окно стрима
st.markdown("### 🎥 Twitch — прямая трансляция (если идёт)")
st.components.v1.iframe("https://player.twitch.tv/?channel=melevik&parent=streamlit.app", height=400)

# YouTube — последнее видео
st.markdown("### 📺 YouTube — последнее видео (не шортс)")
st.components.v1.iframe("https://www.youtube.com/embed?listType=user_uploads&list=melevik-avlaron", height=400)

# Результат поиска
if not result.empty:
    row = result.iloc[0]

    st.markdown("## ✅ Рекомендованные настройки")
    st.markdown(f"**🖥 Процессор:** {row['cpu']}")
    st.markdown(f"**🎮 Видеокарта:** {row['gpu']}")
    st.markdown(f"**💾 ОЗУ:** {row['ram']}")

    st.markdown("### 🎮 Настройки игры")
    st.markdown(
        "- Разрешение: **1280×960 (4:3)** или **1600×900**\n"
        "- Тени: **Низко**\n"
        "- Текстуры: **Средне** (если VRAM ≥ 6 ГБ), иначе **Низко**\n"
        "- Эффекты/Шейдеры: **Низко**\n"
        "- Фильтрация текстур: **4x / 8x**\n"
        "- MSAA: **Выкл**\n"
        "- NVIDIA Reflex: **Вкл**\n"
        "- FSR: **Выкл** (или **Качество**, если нужен доп. FPS)"
    )

    st.markdown("### 🚀 Параметры запуска (очищенные)")
    st.code("+fps_max 0 -high", language="bash")

    st.markdown("### 🎛 Профиль драйвера (NVIDIA/AMD)")
    st.markdown(
        "**NVIDIA Control Panel:**\n"
        "- V-Sync: **Выкл**\n"
        "- Low Latency Mode: **Вкл**\n"
        "- Power Management Mode: **Prefer maximum performance**\n"
        "- Texture Filtering → Quality: **High performance**\n"
        "- Anisotropic optimization: **On**\n"
        "- Max Frame Rate: **Off**\n\n"
        "*(AMD: Anti-Lag/Boost включайте **только в профиле CS2**, не глобально.)*"
    )

    st.markdown("### 🪟 Оптимизация Windows (по желанию)")
    st.markdown(
        "- **Game Mode**: Вкл\n"
        "- **Xbox Game Bar**: Выкл\n"
        "- **HAGS**: Выкл *(если нестабильно — тестируй)*\n"
        "- `cs2.exe` → приоритет: **High**\n"
        "- Отключить **полноэкранные оптимизации**\n"
        "- План электропитания: **Высокая производительность**"
    )

    st.markdown(f"**📊 Ожидаемый FPS:** {row['fps']}")
    st.markdown(f"**🔗 Источник:** {row['source']}")

else:
    st.error("❌ Подходящей конфигурации не найдено. Попробуй изменить параметры.")
