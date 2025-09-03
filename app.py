import pandas as pd
import streamlit as st

# ⚙️ Параметры страницы
st.set_page_config(page_title="CS2 Конфигуратор", page_icon="🎮", layout="centered")

# 🎨 Глобальный CSS (соцкнопки + анимированный донат)
st.markdown("""
<style>
/* Общие мелочи */
hr {border:0; height:1px; background:linear-gradient(90deg,transparent,#333,transparent);}

/* Соц-плашки */
.btn-row {display:flex; gap:12px; flex-wrap:wrap; margin:6px 0 18px 0;}
a.social-btn {
  display:inline-block; padding:10px 14px; border-radius:12px; text-decoration:none;
  color:#fff; font-weight:700; border:0; box-shadow:0 4px 12px rgba(0,0,0,.2);
}
a.social-btn:hover {filter:brightness(1.05)}
.social-youtube {background:#ff0000;}
.social-twitch  {background:#6441a5;}
.social-tiktok  {background:linear-gradient(90deg,#25F4EE,#FE2C55);}
.social-donate  {background:#0ea5e9;}

/* 🔥 DONATE: анимированный блок */
.cta-box {
  position: relative;
  padding: 22px 18px;
  border-radius: 16px;
  color: #fff;
  text-align: center;
  font-weight: 800;
  box-shadow: 0 10px 22px rgba(0,0,0,.35);
  margin: 18px 0 8px 0;

  /* бесконечный перелив градиента */
  background: linear-gradient(270deg, #ff4b1f, #ff9068, #ff4b1f);
  background-size: 300% 300%;
  animation: ctaGradient 9s ease infinite;
}
@keyframes ctaGradient {
  0%   {background-position: 0% 50%;}
  50%  {background-position: 100% 50%;}
  100% {background-position: 0% 50%;}
}

/* пульс вокруг блока */
.cta-box::after{
  content:'';
  position:absolute; inset:-4px;
  border-radius: 18px;
  background: radial-gradient(ellipse at center, rgba(255,255,255,.12), rgba(255,255,255,0));
  filter: blur(6px);
  animation: breathe 3.5s ease-in-out infinite;
  z-index:0;
}
@keyframes breathe {
  0%,100%{opacity:.35}
  50%{opacity:.7}
}

/* Текст и кнопка поверх */
.cta-inner{position:relative; z-index:2;}
.cta-title{font-size:22px; line-height:1.25; margin:0 0 10px 0;}
.cta-sub{font-size:14px; font-weight:700; opacity:.95; margin-bottom:14px;}

/* Кнопка доната с анимацией пульса */
a.cta-btn {
  display:inline-block;
  background:#fff;
  color:#ff4b1f;
  font-weight:900;
  font-size:18px;
  padding:10px 22px;
  border-radius:12px;
  text-decoration:none;
  box-shadow:0 6px 16px rgba(0,0,0,.35);
  transition: transform .15s ease, box-shadow .15s ease;
  animation: btnPulse 1.6s ease-in-out infinite;
}
a.cta-btn:hover {transform: translateY(-1px); box-shadow:0 10px 18px rgba(0,0,0,.4);}
@keyframes btnPulse{
  0%,100% {transform: scale(1.0)}
  50%     {transform: scale(1.04)}
}

/* Мигающая капля внимания в заголовке */
.blink {animation: blink 1s step-start infinite;}
@keyframes blink {50%{opacity:.45}}
</style>
""", unsafe_allow_html=True)

# 📂 Загрузка базы (используем builds.csv)
@st.cache_data
def load_data():
    df = pd.read_csv("builds.csv")

    # Приведение столбцов к канону
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

# 🚫 Чистим -novid/-nojoy (мы это строго соблюдаем по твоему ТЗ)
def clean_launch_options(s: str) -> str:
    if not isinstance(s, str):
        return ""
    tokens = s.split()
    banned = {"-novid", "-nojoy"}  # убираем неактуальные для CS2
    tokens = [t for t in tokens if t not in banned]
    cleaned = " ".join(tokens)
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned.strip()

# 🧭 Заголовок
st.title("⚙️ Конфигуратор CS2")
st.caption("Подбери готовые настройки под свою сборку: графика, панель драйвера, параметры запуска и оптимизации Windows.")

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
    st.markdown("<hr/>", unsafe_allow_html=True)

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

        # 📥 Скачать профиль как .txt
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

# 🔄 Обновление базы (по твоей просьбе — всегда актуальная)
col_refresh, col_spacer = st.columns([1,3])
with col_refresh:
    if st.button("🔄 Обновить базу"):
        st.cache_data.clear()
        st.rerun()

# 🌍 Соцсети — КНОПКИ
st.markdown("<hr/>", unsafe_allow_html=True)
st.subheader("🌍 Соцсети")
st.markdown(
    """
<div class="btn-row">
  <a class="social-btn social-tiktok" href="https://www.tiktok.com/@melevik?_t=ZS-8zQkTQnA4Pf&_r=1" target="_blank">🎵 TikTok</a>
  <a class="social-btn social-youtube" href="https://youtube.com/@melevik-avlaron?si=kRXrCD7GUrVnk478" target="_blank">▶️ YouTube</a>
  <a class="social-btn social-twitch" href="https://m.twitch.tv/melevik/home" target="_blank">🎮 Twitch</a>
</div>
""",
    unsafe_allow_html=True
)

# 💖 Донат — ЯРКИЙ, АНИМИРОВАННЫЙ CTA
st.markdown("<hr/>", unsafe_allow_html=True)
st.subheader("💖 Поддержи проект")

st.markdown(
    """
<div class="cta-box">
  <div class="cta-inner">
    <div class="cta-title">🔥 <span class="blink">Внимание!</span> Каждый, кто поддержит проект рублём — попадёт в <u>следующий ролик</u>!</div>
    <div class="cta-sub">Твоя поддержка ускоряет обновления базы и добавление новых сборок 🙌</div>
    <a class="cta-btn" href="https://www.donationalerts.com/r/melevik" target="_blank">💸 Поддержать на DonatPay</a>
  </div>
</div>
""",
    unsafe_allow_html=True
)
