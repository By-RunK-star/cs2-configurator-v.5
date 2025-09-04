import pandas as pd
import streamlit as st

# -------------------------- БАЗОВЫЕ НАСТРОЙКИ СТРАНИЦЫ --------------------------
st.set_page_config(
    page_title="CS2 Конфигуратор",
    page_icon="🎮",
    layout="centered"
)

# -------------------------- СТИЛИ (CSS) --------------------------
st.markdown("""
<style>
/* Тёмная карточка для рекомендаций */
.reco-card {
    background: #0f0f0f;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    padding: 18px 16px;
    color: #e8e8e8;
    font-size: 0.95rem;
}

/* Заголовки секций внутри карточки */
.reco-card h4{
    margin: 0.25rem 0 0.4rem 0;
    font-size: 1.02rem;
}

/* Блок соц-кнопок (брендовые цвета) */
.social-row {
    display: flex; gap: 10px; flex-wrap: wrap; margin: 8px 0 0 0;
}
.social-btn {
    display: inline-flex; align-items: center; justify-content: center;
    padding: 8px 12px; border-radius: 8px; text-decoration: none; font-weight: 600;
    color: #fff !important; border: none;
}
.social-btn:hover { opacity: .9; }

/* Цвета площадок */
.btn-tiktok { background:#000000; }
.btn-youtube { background:#FF0000; }
.btn-twitch { background:#9146FF; }

/* Донат-баннер (мягкая жёлтая пульсация) */
.donate-banner {
    border-radius: 10px;
    padding: 14px 16px;
    background: #1a1a1a;
    color: #ffd84d;
    font-weight: 700;
    border: 1px solid #4d3b00;
    box-shadow: 0 0 0px rgba(255, 215, 0, 0.0);
    animation: pulseGlow 2.4s ease-in-out infinite;
}
@keyframes pulseGlow {
    0%   { box-shadow: 0 0 0px rgba(255, 215, 0, 0.0);   }
    50%  { box-shadow: 0 0 18px rgba(255, 215, 0, 0.25); }
    100% { box-shadow: 0 0 0px rgba(255, 215, 0, 0.0);   }
}

/* Тонкий разделитель */
.hr { height:1px; background:#2a2a2a; margin: 12px 0; }

/* Предупреждения */
.warn {
    border-left: 4px solid #f0ad4e;
    background: #1b1a17;
    color: #f5e8c7;
    padding: 10px 12px;
    border-radius: 6px;
    font-size: 0.92rem;
}
.info {
    border-left: 4px solid #5bc0de;
    background: #141a1f;
    color: #d6ecff;
    padding: 10px 12px;
    border-radius: 6px;
    font-size: 0.92rem;
}
</style>
""", unsafe_allow_html=True)

# -------------------------- ЗАГРУЗКА БАЗЫ --------------------------
@st.cache_data(show_spinner=False)
def load_data():
    # читаем сначала сжатые, затем обычный CSV
    df = None
    for path in ["builds_site_ready.csv.gz", "builds.csv.gz", "builds.csv"]:
        try:
            if path.endswith(".gz"):
                df = pd.read_csv(path, compression="infer")
            else:
                df = pd.read_csv(path)
            break
        except Exception:
            df = None
    if df is None:
        st.error("Не удалось найти базу builds. Залейте файл builds_site_ready.csv.gz или builds.csv в корень репозитория.")
        st.stop()

    # нормализация имён колонок (на всякий)
    def ensure_col(df, canon, variants):
        for v in variants:
            if v in df.columns:
                df[canon] = df[v]
                break
        if canon not in df.columns:
            df[canon] = ""
        return df

    df.columns = [c.strip() for c in df.columns]
    df = ensure_col(df, "CPU", ["CPU","Cpu","cpu"])
    df = ensure_col(df, "GPU", ["GPU","Gpu","gpu"])
    df = ensure_col(df, "RAM", ["RAM","Ram","ram"])
    df = ensure_col(df, "Game Settings", ["Game Settings","Settings","GameSettings"])
    df = ensure_col(df, "Launch Options", ["Launch Options","Launch","Params","LaunchOptions"])
    df = ensure_col(df, "Control Panel", ["Control Panel","ControlPanel","Driver Settings","Driver"])
    df = ensure_col(df, "Windows Optimization", ["Windows Optimization","Windows Optimizations","Windows","Windows Opt"])
    df = ensure_col(df, "FPS Estimate", ["FPS Estimate","FPS","FPS Range","Estimate"])
    df = ensure_col(df, "Source", ["Source","origin"])

    # стандартизация RAM
    df["RAM"] = df["RAM"].astype(str)
    df["RAM"] = (df["RAM"]
                 .str.replace("ГБ"," GB", regex=False)
                 .str.replace("GB"," GB", regex=False)
                 .str.replace("  "," ", regex=False)
                 .str.strip())

    # чистим неактуальные флаги CS2 в параметрах запуска
    def clean_launch(s):
        if not isinstance(s, str):
            return ""
        banned = {"-novid", "-nojoy"}
        toks = [t for t in s.split() if t not in banned]
        out = " ".join(toks).strip()
        while "  " in out:
            out = out.replace("  "," ")
        return out
    df["Launch Options"] = df["Launch Options"].apply(clean_launch)

    # убираем явные дубли
    df = df.drop_duplicates(subset=["CPU","GPU","RAM","Game Settings","Launch Options","Control Panel","Windows Optimization"], keep="first").reset_index(drop=True)
    return df

df = load_data()

# -------------------------- ЗАГОЛОВОК --------------------------
st.title("⚙️ Конфигуратор CS2")
st.caption("Подбери готовые настройки по своей сборке: графика, параметры запуска, панель драйвера и оптимизации Windows.")

# Предупреждение: 1-канал vs 2-канал
st.markdown("""
<div class="info">
<b>Память:</b> в одноканальном режиме FPS обычно ниже, в двухканальном — выше. 
Если у вас 1 планка ОЗУ — добавьте вторую для стабильности и прироста в CPU-упоре.
</div>
""", unsafe_allow_html=True)

# Предупреждения по глобальным тумблерам
st.markdown("""
<div class="warn" style="margin-top:10px;">
<b>Важно:</b> в драйверах <b>NVIDIA/AMD/Intel</b> меняйте <u>только профиль для CS2</u>, а не глобальные настройки.
Глобальные «макс. производительность / низкая задержка / анти-лаг / форс-VSync» могут:
<ul style="margin:6px 0 0 18px;">
  <li>держать видеокарту на повышенных частотах даже на рабочем столе;</li>
  <li>ломать адаптивную синхронизацию и добавлять статтер;</li>
  <li>(AMD) <b>Anti-Lag+</b> включайте только для CS2; <b>Boost/Chill</b> — с осторожностью;</li>
  <li>(Intel iGPU) проверяйте план энергопитания и не форсируйте VSync глобально.</li>
</ul>
</div>
""", unsafe_allow_html=True)

# -------------------------- ФИЛЬТРЫ --------------------------
col1, col2, col3 = st.columns(3)
with col1:
    cpu = st.selectbox("🖥 Процессор (CPU)", sorted(df["CPU"].dropna().unique()))
with col2:
    gpu = st.selectbox("🎮 Видеокарта (GPU)", sorted(df["GPU"].dropna().unique()))
with col3:
    ram = st.selectbox("💾 ОЗУ (RAM)", sorted(df["RAM"].dropna().unique()))

# -------------------------- ПОИСК --------------------------
if st.button("🔍 Найти настройки"):
    subset = df[(df["CPU"] == cpu) & (df["GPU"] == gpu) & (df["RAM"] == ram)]

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    if subset.empty:
        st.error("❌ Подходящей конфигурации не найдено в базе.")
    else:
        row = subset.iloc[0].to_dict()
        # Формируем текст карточки
        game = row.get("Game Settings","").strip()
        launch = row.get("Launch Options","").strip()
        drv = row.get("Control Panel","").strip()
        winopt = row.get("Windows Optimization","").strip()
        fps = row.get("FPS Estimate","—")
        src = row.get("Source","")

        st.markdown(f"""
<div class="reco-card">
    <div><b>🖥 Процессор:</b> {row.get('CPU','')} &nbsp;&nbsp; <b>🎮 Видеокарта:</b> {row.get('GPU','')} &nbsp;&nbsp; <b>💾 ОЗУ:</b> {row.get('RAM','')}</div>
    <div class="hr"></div>
    <h4>🎮 Настройки игры</h4>
    <div>{game if game else "—"}</div>
    <h4>🚀 Параметры запуска (очищенные)</h4>
    <div><code>{launch if launch else "—"}</code></div>
    <h4>🎛 Панель драйвера (NVIDIA/AMD)</h4>
    <div>{drv if drv else "—"}</div>
    <h4>🪟 Оптимизация Windows (по желанию)</h4>
    <div>{winopt if winopt else "—"}</div>
    <div class="hr"></div>
    <div><b>📊 Ожидаемый FPS:</b> {fps} &nbsp;&nbsp; <b>🔗 Источник:</b> {src}</div>
</div>
""", unsafe_allow_html=True)

        # Кнопка скачать профиль .txt
        profile_txt = (
            f"CPU: {row.get('CPU','')}\n"
            f"GPU: {row.get('GPU','')}\n"
            f"RAM: {row.get('RAM','')}\n\n"
            f"[Game Settings]\n{game}\n\n"
            f"[Launch Options]\n{launch}\n\n"
            f"[Control Panel]\n{drv}\n\n"
            f"[Windows Optimization]\n{winopt}\n\n"
            f"FPS Estimate: {fps}\n"
            f"Source: {src}\n"
        )
        st.download_button("💾 Скачать профиль (.txt)", data=profile_txt, file_name="cs2_profile.txt")

# -------------------------- ДОНАТ --------------------------
st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
st.subheader("💖 Поддержи проект")
st.markdown("""
<div class="donate-banner">
Каждый, кто поддержит рублём — попадает в следующий ролик.  
👉 <a href="https://www.donationalerts.com/r/melevik" target="_blank" style="color:#ffe48b; text-decoration: underline;">DonatPay</a>
</div>
""", unsafe_allow_html=True)
st.caption("Чем больше поддержка — тем чаще обновляем и расширяем базу.")

# -------------------------- СОЦИАЛКИ --------------------------
st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
st.subheader("Подписывайся, чтобы следить за актуальными обновлениями и контентом автора")
st.markdown("""
<div class="social-row">
  <a class="social-btn btn-tiktok" href="https://www.tiktok.com/@melevik?_t=ZS-8zQkTQnA4Pf&_r=1" target="_blank">TikTok</a>
  <a class="social-btn btn-youtube" href="https://youtube.com/@melevik-avlaron?si=kRXrCD7GUrVnk478" target="_blank">YouTube</a>
  <a class="social-btn btn-twitch" href="https://m.twitch.tv/melevik/home" target="_blank">Twitch</a>
</div>
""", unsafe_allow_html=True)

# -------------------------- ВСТАВКИ TWITCH/YOUTUBE --------------------------
with st.expander("📺 Онлайн-активность (Twitch/YouTube)", expanded=False):
    st.markdown("""
    <div style="display:flex; flex-wrap:wrap; gap:16px;">
      <div style="flex:1 1 360px; min-width:320px; max-width:560px;">
        <div style="font-weight:600; margin:4px 0 6px 0;">Twitch</div>
        <!-- Покажет эфир, если вы в онлайне; иначе оффлайн-панель канала -->
        <iframe
          src="https://player.twitch.tv/?channel=melevik&parent=share.streamlit.io&muted=true"
          height="315" width="560" frameborder="0" scrolling="no" allowfullscreen>
        </iframe>
      </div>
      <div style="flex:1 1 360px; min-width:320px; max-width:560px;">
        <div style="font-weight:600; margin:4px 0 6px 0;">YouTube (последний ролик)</div>
        <!-- Без API: вставьте сюда ID последнего полноформатного видео -->
        <iframe width="560" height="315"
          src="https://www.youtube.com/embed?listType=user_uploads&list=melevik-avlaron"
          title="YouTube video player" frameborder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowfullscreen>
        </iframe>
        <div style="font-size:12px; opacity:.8; margin-top:4px;">
          Если нужно показывать строго «последний полноформатный ролик (не шорт)» — подключим YouTube API.
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# -------------------------- КНОПКА ОБНОВЛЕНИЯ БАЗЫ --------------------------
st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
if st.button("🔄 Обновить базу (перечитать файл)"):
    # чистим кэш и мягко перезапускаем скрипт
    load_data.clear()
    st.rerun()
