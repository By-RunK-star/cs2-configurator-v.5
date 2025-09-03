import pandas as pd
import streamlit as st

# ⚙️ Параметры страницы
st.set_page_config(page_title="CS2 Конфигуратор", page_icon="🎮", layout="centered")

# 🎨 Стили: соц-кнопки + спокойный донат-блок с мягкой пульсацией
st.markdown("""
<style>
hr {border:0; height:1px; background:linear-gradient(90deg,transparent,#333,transparent);}

/* Соц-плашки */
.btn-row {display:flex; gap:12px; flex-wrap:wrap; margin:6px 0 18px 0;}
a.social-btn {
  display:inline-block; padding:10px 14px; border-radius:12px; text-decoration:none;
  color:#fff; font-weight:700; border:0; box-shadow:0 4px 12px rgba(0,0,0,.15);
}
a.social-btn:hover {filter:brightness(1.05)}
.social-youtube {background:#ff0000;}
.social-twitch  {background:#6441a5;}
.social-tiktok  {background:linear-gradient(90deg,#25F4EE,#FE2C55);}

/* Спокойный донат-блок (без «внимания»), мягкая пульсация */
.cta-box{
  padding:18px 16px; border-radius:14px;
  background: linear-gradient(180deg, rgba(148,163,184,.08), rgba(148,163,184,.03));
  border:1px solid rgba(100,116,139,.35);
  color: inherit;
  animation: gentle-pulse 2.8s ease-in-out infinite;
}
.cta-title{font-size:18px; font-weight:800; margin:0 0 8px 0;}
.cta-sub{font-size:14px; font-weight:600; opacity:.9; margin:0 0 12px 0;}
a.cta-btn{
  display:inline-block; text-decoration:none;
  padding:9px 18px; border-radius:10px;
  background:#0ea5e9; color:#fff; font-weight:800; border:0;
  box-shadow:0 6px 14px rgba(14,165,233,.22);
  transition: transform .12s ease, box-shadow .12s ease, filter .12s ease;
}
a.cta-btn:hover{transform:translateY(-1px); filter:brightness(1.03)}

/* Мягкая пульсация контейнера */
@keyframes gentle-pulse {
  0%   { transform: scale(1);   box-shadow: 0 0 0 rgba(14,165,233,0.00); }
  50%  { transform: scale(1.01); box-shadow: 0 10px 26px rgba(14,165,233,0.18); }
  100% { transform: scale(1);   box-shadow: 0 0 0 rgba(14,165,233,0.00); }
}
</style>
""", unsafe_allow_html=True)

# 📂 Загрузка базы (используем builds.csv)
@st.cache_data
def load_data():
    df = pd.read_csv("builds.csv")

    # Приводим названия столбцов к единому виду
    def ensure_col(df, canon, variants):
        for v in variants:
            if v in df.columns:
                df[canon] = df[v]
                break
        if canon not in df.columns:
            df[canon] = ""
        return df

    df = ensure_col(df, "Game Settings", ["Game Settings", "Settings", "GameSettings"])
    df = ensure_col(df, "Launch Options", ["Launch Options", "Launch", "Params", "LaunchOptions"])
    df = ensure_col(df, "Control Panel", ["Control Panel", "ControlPanel", "Driver Settings", "Driver"])
    df = ensure_col(df, "Windows Optimization", ["Windows Optimization", "Windows Optimizations", "Windows", "Windows Opt"])
    df = ensure_col(df, "FPS Estimate", ["FPS Estimate", "FPS", "FPS Range", "Estimate"])
    df = ensure_col(df, "Source", ["Source"])

    # RAM → единый формат
    if "RAM" in df.columns:
        df["RAM"] = (
            df["RAM"].astype(str)
            .str.replace("GB", " ГБ", regex=False)
            .str.replace("  ", " ", regex=False)
            .str.strip()
        )
    return df

df = load_data()

# 🚫 Чистим неактуальные флаги для CS2
def clean_launch_options(s: str) -> str:
    if not isinstance(s, str):
        return ""
    tokens = s.split()
    banned = {"-novid", "-nojoy"}  # убираем неработающие/неактуальные
    tokens = [t for t in tokens if t not in banned]
    cleaned = " ".join(tokens)
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned.strip()

# 🧭 Заголовок
st.title("⚙️ Конфигуратор CS2")
st.caption("Подбери готовые настройки под свою сборку: графика, панель драйвера, параметры запуска и оптимизации Windows.")

# 🔗 Социальные сети
st.markdown(
    """
<div class="btn-row">
  <a class="social-btn social-tiktok" href="https://www.tiktok.com/@melevik?_t=ZS-8zQkTQnA4Pf&_r=1" target="_blank">TikTok</a>
  <a class="social-btn social-youtube" href="https://youtube.com/@melevik-avlaron?si=kRXrCD7GUrVnk478" target="_blank">YouTube</a>
  <a class="social-btn social-twitch"  href="https://m.twitch.tv/melevik/home" target="_blank">Twitch</a>
</div>
""",
    unsafe_allow_html=True
)

# 🔍 Фильтры
left, right = st.columns([2,1])
with left:
    cpu = st.selectbox("🖥 Процессор", sorted(df["CPU"].dropna().unique()))
    gpu = st.selectbox("🎮 Видеокарта", sorted(df["GPU"].dropna().unique()))
with right:
    ram = st.selectbox("💾 ОЗУ", sorted(df["RAM"].dropna().unique()))

# 🔎 Поиск
if st.button("🔍 Найти настройки"):
    result = df[(df["CPU"] == cpu) & (df["GPU"] == gpu) & (df["RAM"] == ram)]

    st.markdown("---")

    if result.empty:
        st.error("❌ Подходящей конфигурации не найдено в базе.")
    else:
        row = result.iloc[0].to_dict()
        launch_clean = clean_launch_options(row.get("Launch Options", ""))

        st.subheader("✅ Рекомендованные настройки")
        st.markdown(
            f"""
**🖥 Процессор:** {row.get('CPU','')}
**🎮 Видеокарта:** {row.get('GPU','')}
**💾 ОЗУ:** {row.get('RAM','')}

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

# 🔄 Перечитать базу (если обновили builds.csv в репо)
if st.button("🔄 Перечитать базу"):
    load_data.clear()
    st.rerun()

st.markdown("---")

# 💖 Донат (спокойный, с мягкой пульсацией контейнера)
st.markdown(
    """
<div class="cta-box">
  <div class="cta-title">Поддержи проект рублём</div>
  <div class="cta-sub">Каждый, кто поддержал, попадёт в следующий ролик (укажу ник в титрах).</div>
  <a class="cta-btn" href="https://www.donationalerts.com/r/melevik" target="_blank">💸 Донат</a>
</div>
""",
    unsafe_allow_html=True
)

st.caption("Чем больше поддержка — тем чаще обновляем и расширяем базу.")
