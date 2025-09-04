import pandas as pd
import streamlit as st

# ------------------ НАСТРОЙКИ СТРАНИЦЫ ------------------
st.set_page_config(
    page_title="CS2 Конфигуратор",
    page_icon="🎮",
    layout="centered"
)

# ------------------ СТИЛИ (соц-кнопки + мягкая пульсация) ------------------
st.markdown("""
<style>
.badge-row { display:flex; gap:10px; flex-wrap:wrap; margin-top:4px; }
.badge {
  text-decoration:none; padding:8px 12px; border-radius:8px;
  font-weight:600; border:1px solid rgba(255,255,255,0.2);
}
.badge:hover { filter:brightness(1.08); }

.badge-yt { background:#FF0000; color:white; }
.badge-tt { background:#000000; color:white; }
.badge-tw { background:#9146FF; color:white; }

.donate-box {
  border:1px solid rgba(255,255,255,0.15);
  border-radius:12px; padding:14px;
  background:rgba(255,255,255,0.03);
  margin:12px 0;
  animation:pulse 2.5s ease-in-out infinite;
}
@keyframes pulse {
  0%   { box-shadow:0 0 0 0 rgba(255,215,0,0.0); }
  50%  { box-shadow:0 0 24px 2px rgba(255,215,0,0.18); }
  100% { box-shadow:0 0 0 0 rgba(255,215,0,0.0); }
}
.small-note { opacity:0.8; font-size:0.92rem; }
.code-wrap code { white-space:pre-wrap; }
</style>
""", unsafe_allow_html=True)

# ------------------ ЗАГРУЗКА ДАННЫХ ------------------
@st.cache_data
def load_data():
    df = pd.read_csv("builds.csv")
    # Канонизируем столбцы (если кто-то когда-то переименует)
    def ensure_col(df, canon, variants):
        for v in variants:
            if v in df.columns:
                df[canon] = df[v]
                break
        if canon not in df.columns:
            df[canon] = ""
        return df

    df = ensure_col(df, "CPU", ["CPU"])
    df = ensure_col(df, "GPU", ["GPU"])
    df = ensure_col(df, "RAM", ["RAM"])
    df = ensure_col(df, "Game Settings", ["Game Settings","Settings"])
    df = ensure_col(df, "Launch Options", ["Launch Options","Params","Launch"])
    df = ensure_col(df, "Control Panel", ["Control Panel","Driver","Driver Settings"])
    df = ensure_col(df, "Windows Optimization", ["Windows Optimization","Windows"])
    df = ensure_col(df, "FPS Estimate", ["FPS Estimate","FPS","Estimate"])
    df = ensure_col(df, "Source", ["Source"])

    # Нормализуем RAM
    df["RAM"] = df["RAM"].astype(str).str.replace("GB"," GB", regex=False).str.replace("  "," ", regex=False).str.strip()
    return df

df = load_data()

# Чистим запуск от неактуальных флагов (страховка)
def clean_launch_options(s: str) -> str:
    if not isinstance(s, str):
        return ""
    banned = {"-novid", "-nojoy"}
    toks = s.split()
    toks = [t for t in toks if t not in banned]
    cleaned = " ".join(toks).strip()
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned

# ------------------ UI ------------------
st.title("⚙️ Конфигуратор CS2")
st.caption("Подбери готовые настройки под свою сборку: игра, панель драйвера, параметры запуска и Windows-оптимизации.")

# Соц-ссылки (верх)
st.markdown("**Мои каналы:**")
st.markdown("""
<div class="badge-row">
  <a class="badge badge-tt" href="https://www.tiktok.com/@melevik?_t=ZS-8zQkTQnA4Pf&_r=1" target="_blank">TikTok</a>
  <a class="badge badge-yt" href="https://youtube.com/@melevik-avlaron?si=kRXrCD7GUrVnk478" target="_blank">YouTube</a>
  <a class="badge badge-tw" href="https://m.twitch.tv/melevik/home" target="_blank">Twitch</a>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Фильтры
col1, col2, col3 = st.columns(3)
with col1:
    cpu = st.selectbox("🖥 Процессор (CPU)", sorted(df["CPU"].dropna().unique()))
with col2:
    gpu = st.selectbox("🎮 Видеокарта (GPU)", sorted(df["GPU"].dropna().unique()))
with col3:
    ram = st.selectbox("💾 ОЗУ (RAM)", sorted(df["RAM"].dropna().unique()))

# Подсказка про двухканал
st.markdown(
    '<div class="small-note">💡 Если у тебя одна планка ОЗУ — добавь вторую (двухканал). Это часто даёт самый лучший прирост в CS2.</div>',
    unsafe_allow_html=True
)

# Поиск
if st.button("🔍 Найти настройки"):
    result = df[(df["CPU"] == cpu) & (df["GPU"] == gpu) & (df["RAM"] == ram)]

    st.markdown("---")

    if result.empty:
        st.error("❌ Подходящей конфигурации не найдено в базе. Попробуй другой объём RAM или соседнее семейство CPU/GPU.")
    else:
        row = result.iloc[0].to_dict()
        launch_clean = clean_launch_options(row.get("Launch Options",""))

        st.subheader("✅ Рекомендованные настройки")

        # Краткий заголовок
        st.markdown(f"**🖥 Процессор:** {row.get('CPU','')}  \n"
                    f"**🎮 Видеокарта:** {row.get('GPU','')}  \n"
                    f"**💾 Оперативная память:** {row.get('RAM','')}")

        # Блоки
        st.markdown("### 🎮 Настройки игры")
        st.markdown(f"<div class='code-wrap'><code>{row.get('Game Settings','').strip()}</code></div>", unsafe_allow_html=True)

        st.markdown("### 🚀 Параметры запуска (очищенные)")
        st.code(launch_clean or "—")

        st.markdown("### 🎛 Панель драйвера (NVIDIA/AMD)")
        st.markdown(f"<div class='code-wrap'><code>{row.get('Control Panel','').strip()}</code></div>", unsafe_allow_html=True)

        st.markdown("### 🪟 Оптимизация Windows (по желанию)")
        st.markdown(f"<div class='code-wrap'><code>{row.get('Windows Optimization','').strip()}</code></div>", unsafe_allow_html=True)

        # FPS + источник
        fps = row.get("FPS Estimate","—")
        src = row.get("Source","—")
        st.markdown(f"**📊 Ожидаемый FPS:** {fps if str(fps).strip() else '—'}")
        st.caption(f"Источник профиля: {src}")

        # Скачать профиль
        profile_txt = (
            f"CPU: {row.get('CPU','')}\n"
            f"GPU: {row.get('GPU','')}\n"
            f"RAM: {row.get('RAM','')}\n\n"
            f"[Game Settings]\n{row.get('Game Settings','').strip()}\n\n"
            f"[Launch Options]\n{launch_clean}\n\n"
            f"[Control Panel]\n{row.get('Control Panel','').strip()}\n\n"
            f"[Windows Optimization]\n{row.get('Windows Optimization','').strip()}\n\n"
            f"FPS Estimate: {fps}\n"
            f"Source: {src}\n"
        )
        st.download_button("💾 Скачать профиль (.txt)", data=profile_txt, file_name="cs2_profile.txt")

# Донат-блок (ненавязчивый, с пульсацией)
st.markdown("---")
st.markdown("""
<div class="donate-box">
  <b>Поддержи проект</b><br>
  Каждый, кто поддержит рублём — попадёт в следующий ролик (экран благодарностей).  
  <span class="small-note">Так мы сможем чаще обновлять базу и добавлять новые сборки.</span><br><br>
  👉 <a class="badge badge-yt" href="https://www.donationalerts.com/r/melevik" target="_blank">Перейти к поддержке</a>
</div>
""", unsafe_allow_html=True)
