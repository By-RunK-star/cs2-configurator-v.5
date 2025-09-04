import pandas as pd
import streamlit as st

# -------------------------
# БАЗОВЫЕ НАСТРОЙКИ СТРАНИЦЫ
# -------------------------
st.set_page_config(page_title="CS2 Конфигуратор", page_icon="🎮", layout="centered")

# -------------------------
# СТИЛИ (тёмная карточка, соц-иконки, донат-бокс с мягкой пульсацией)
# -------------------------
st.markdown("""
<style>
/* Общий контейнер */
.main { padding-top: 10px; }

/* Тёмная карточка с настройками */
.cs2-card {
  background: #111;
  color: #eee;
  border: 1px solid #222;
  border-radius: 14px;
  padding: 18px 18px 10px 18px;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.03) inset, 0 8px 24px rgba(0,0,0,0.45);
  font-size: 15px;
  line-height: 1.55;
}
.cs2-card h3 {
  margin: 0 0 10px 0;
  font-size: 18px;
  font-weight: 700;
}

/* Коды и моно */
.cs2-card code, .cs2-card pre {
  background: #0d0d0d;
  color: #cfe3ff;
  border: 1px solid #1f1f1f;
  border-radius: 8px;
  padding: 6px 8px;
  display: block;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
}

/* Социальные ссылки (иконки SVG) */
.social-wrap {
  display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
}
.social-wrap .social-title {
  font-weight: 700; margin-right: 8px;
}
.social-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid #1f1f1f;
  background: #121212;
  color: #eaeaea !important;
  text-decoration: none !important;
  font-weight: 600;
  transition: transform .08s ease, box-shadow .15s ease, background .2s ease;
}
.social-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(0,0,0,0.35); background: #151515; }
.social-btn svg { width: 18px; height: 18px; }

/* Донат бокс — мягкая жёлтая пульсация (без вырвиглаз) */
.donate-box {
  position: relative;
  border-radius: 14px;
  padding: 16px;
  border: 1px solid #2a2a2a;
  background: linear-gradient(180deg, rgba(255,230,120,0.09), rgba(0,0,0,0.04));
  box-shadow: 0 8px 24px rgba(0,0,0,0.35) inset;
  color: #f6f1ce;
  margin-top: 8px;
}
.donate-pulse {
  position: absolute;
  inset: 0;
  border-radius: 14px;
  background: radial-gradient(60% 60% at 50% 10%, rgba(255,240,120,0.20), rgba(0,0,0,0.0));
  animation: pulseGlow 2.8s ease-in-out infinite;
  pointer-events: none;
  filter: blur(1px);
  opacity: 0.9;
}
@keyframes pulseGlow {
  0% { opacity: 0.18; }
  50% { opacity: 0.32; }
  100% { opacity: 0.18; }
}
.donate-title { font-weight: 800; font-size: 16px; margin-bottom: 6px; }
.donate-link a {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 8px 12px; border-radius: 10px; border: 1px solid #3b3b3b;
  background: #14110b; color: #ffe066 !important; text-decoration: none !important; font-weight: 700;
}
.donate-link a:hover { background: #1a160d; }

/* Блок предупреждений */
.warn-box {
  border: 1px dashed #4a3;
  background: rgba(70, 130, 50, 0.08);
  color: #cfe9c3;
  border-radius: 10px;
  padding: 10px 12px;
  margin-top: 8px;
}
.warn-title { font-weight: 700; margin-bottom: 4px; }

/* Блок AMD-важно */
.amd-box {
  border: 1px dashed #a53;
  background: rgba(160, 70, 50, 0.08);
  color: #f0d0c7;
  border-radius: 10px;
  padding: 10px 12px;
  margin-top: 8px;
}
.amd-title { font-weight: 800; margin-bottom: 4px; color: #ffb7a1; }

/* Кнопки в одну линию */
.button-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# ЗАГРУЗКА БАЗЫ
# -------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("builds.csv")

    # Нормализация названий столбцов
    def ensure_col(df_, canon, variants):
        for v in variants:
            if v in df_.columns:
                df_[canon] = df_[v]
                break
        if canon not in df_.columns:
            df_[canon] = ""
        return df_

    df = ensure_col(df, "CPU", ["CPU", "Processor"])
    df = ensure_col(df, "GPU", ["GPU", "Graphics"])
    df = ensure_col(df, "RAM", ["RAM", "Memory"])
    df = ensure_col(df, "Game Settings", ["Game Settings", "Settings", "GameSettings"])
    df = ensure_col(df, "Launch Options", ["Launch Options", "Launch", "Params", "LaunchOptions"])
    df = ensure_col(df, "Control Panel", ["Control Panel", "ControlPanel", "Driver Settings", "Driver"])
    df = ensure_col(df, "Windows Optimization", ["Windows Optimization", "Windows Optimizations", "Windows", "Windows Opt"])
    df = ensure_col(df, "FPS Estimate", ["FPS Estimate", "FPS", "FPS Range", "Estimate"])
    df = ensure_col(df, "Source", ["Source", "Origin"])

    # Приведём RAM к виду "N GB"
    df["RAM"] = df["RAM"].astype(str).str.replace("GB", " GB", regex=False)
    df["RAM"] = df["RAM"].str.replace("  ", " ", regex=False).str.strip()

    return df

df = load_data()

# -------------------------
# ОЧИСТКА ПАРАМЕТРОВ ЗАПУСКА
# -------------------------
def clean_launch_options(s: str) -> str:
    if not isinstance(s, str):
        return ""
    tokens = s.split()
    banned = {"-novid", "-nojoy"}  # для CS2 считаем неактуальными
    tokens = [t for t in tokens if t not in banned]
    cleaned = " ".join(tokens)
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned.strip()

# -------------------------
# ШАПКА
# -------------------------
st.title("CS2 Конфигуратор")
st.caption("Подбери готовые настройки: параметры игры, драйвера, запуска и Windows-оптимизации. Нет лишних флагов, всё по делу.")

# Социальные ссылки (оставляем расположение; аккуратные SVG-иконки)
st.markdown("""
<div class="social-wrap">
  <div class="social-title">Подписывайся, чтобы следить за актуальными обновлениями и контентом автора:</div>

  <a class="social-btn" href="https://www.tiktok.com/@melevik?_t=ZS-8zQkTQnA4Pf&_r=1" target="_blank" rel="noopener">
    <svg viewBox="0 0 24 24" fill="#fff"><path d="M12.6 3.2c.7 2.3 2.6 4.1 4.9 4.6v3c-1.6.1-3.1-.3-4.4-1.2v5.8c0 3.9-3.2 7-7.1 7-1.7 0-3.3-.6-4.5-1.6a7 7 0 0 1 8.8-10.8V3.2h2.3z"/></svg>
    TikTok
  </a>

  <a class="social-btn" href="https://youtube.com/@melevik-avlaron?si=kRXrCD7GUrVnk478" target="_blank" rel="noopener">
    <svg viewBox="0 0 24 24" fill="#fff"><path d="M21.6 7.2c.3 1.1.4 2.3.4 4s-.1 2.9-.4 4c-.3 1-1 1.7-2 2-1.1.3-5.2.4-7.6.4s-6.5-.1-7.6-.4c-1-.3-1.7-1-2-2C2.1 14.1 2 12.9 2 11.2s.1-2.9.4-4c.3-1 1-1.7 2-2C5.5 4 9.6 3.9 12 3.9s6.5.1 7.6.4c1 .3 1.7 1 2 2zM10 9.2v4l4-2-4-2z"/></svg>
    YouTube
  </a>

  <a class="social-btn" href="https://m.twitch.tv/melevik/home" target="_blank" rel="noopener">
    <svg viewBox="0 0 24 24" fill="#fff"><path d="M4 3h17v11.5l-4 4H12l-2.5 2.5H7V18H4V3zm3 2v9h3v2h2l2-2h3l2-2V5H7z"/></svg>
    Twitch
  </a>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -------------------------
# ФИЛЬТРЫ
# -------------------------
col1, col2, col3 = st.columns(3)
with col1:
    cpu = st.selectbox("Процессор (CPU):", sorted(df["CPU"].dropna().unique()))
with col2:
    gpu = st.selectbox("Видеокарта (GPU):", sorted(df["GPU"].dropna().unique()))
with col3:
    ram = st.selectbox("ОЗУ (RAM):", sorted(df["RAM"].dropna().unique()))

# -------------------------
# ПОИСК
# -------------------------
if st.button("Найти настройки"):
    result = df[(df["CPU"] == cpu) & (df["GPU"] == gpu) & (df["RAM"] == ram)]

    st.markdown("---")

    if result.empty:
        st.error("Подходящая конфигурация не найдена в базе. Обнови базу и попробуй снова.")
    else:
        row = result.iloc[0].to_dict()
        launch_clean = clean_launch_options(row.get("Launch Options", ""))

        # Карточка рекомендаций (чёрная)
        st.markdown('<div class="cs2-card">', unsafe_allow_html=True)
        st.markdown(f"""
<h3>Рекомендованные настройки</h3>

<strong>Процессор:</strong> {row.get('CPU', '—')}  
<strong>Видеокарта:</strong> {row.get('GPU', '—')}  
<strong>ОЗУ:</strong> {row.get('RAM', '—')}

<strong>Настройки игры:</strong>  
{row.get('Game Settings', '—')}

<strong>Параметры запуска (очищенные):</strong>
<pre><code>{launch_clean}</code></pre>

<strong>Панель драйвера (NVIDIA/AMD):</strong>  
{row.get('Control Panel', '—')}

<strong>Оптимизация Windows (по желанию):</strong>  
{row.get('Windows Optimization', '—')}

<strong>Ожидаемый FPS:</strong> {row.get('FPS Estimate', '—')}  
<strong>Источник:</strong> {row.get('Source', '—')}
""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Предупреждение про одноканал/двухканал
        st.markdown("""
<div class="warn-box">
  <div class="warn-title">Память: двухканал быстрее.</div>
  Если у тебя установлена ОЗУ в одноканальном режиме (одна планка), FPS будет ниже.
  Для максимально стабильного FPS ставь две одинаковые планки и включай двухканальный режим.
</div>
""", unsafe_allow_html=True)

        # Важно для AMD — не включать опасные глобальные тумблеры
        st.markdown("""
<div class="amd-box">
  <div class="amd-title">Важно для AMD Radeon (глобальные настройки):</div>
  • Не ставь «Максимальная производительность» глобально — создавай профиль только для CS2, иначе видеокарта может держать частоты даже на рабочем столе.<br>
  • Anti-Lag/Anti-Lag+ включай только в профиле CS2. Глобальное включение может давать нестабильность и конфликты с анти-читом.<br>
  • Radeon Chill/Boost — используй осознанно в профиле игры. Глобально может резать частоты и вызывать фризы.
</div>
""", unsafe_allow_html=True)

        # Скачать профиль
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
        st.download_button("Скачать профиль (.txt)", data=profile_txt, file_name="cs2_profile.txt")

st.markdown("---")

# -------------------------
# КНОПКА ОБНОВЛЕНИЯ БАЗЫ (как было, но актуальная команда)
# -------------------------
c1, c2 = st.columns([1, 3])
with c1:
    if st.button("Обновить базу"):
        st.cache_data.clear()
        st.rerun()
with c2:
    st.caption("Если ты обновил файл builds.csv в репозитории — нажми «Обновить базу», чтобы подтянуть актуальные данные.")

# -------------------------
# ПОДДЕРЖИ ПРОЕКТ (с мягкой жёлтой пульсацией, без кнопок «внимание»)
# -------------------------
st.markdown("""
<div class="donate-box">
  <div class="donate-pulse"></div>
  <div class="donate-title">Поддержи проект — и попади в следующий ролик!</div>
  Каждая поддержка ускоряет обновления базы и улучшения конфигуратора. Имена донатеров мы благодарно упоминаем в следующем видео.
  <div class="donate-link" style="margin-top:8px;">
    <a href="https://www.donationalerts.com/r/melevik" target="_blank" rel="noopener">Перейти к поддержке</a>
  </div>
</div>
""", unsafe_allow_html=True)
