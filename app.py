import re
import pandas as pd
import streamlit as st

# ---------- базовая настройка страницы ----------
st.set_page_config(page_title="CS2 Конфигуратор", page_icon="🎮", layout="wide")

# ---------- стили (соц-кнопки, донат, черный блок результатов) ----------
st.markdown("""
<style>
/* контейнер результата на чёрном фоне */
.result-box {
  background: #0f1116;
  border: 1px solid #222;
  border-radius: 10px;
  padding: 16px 18px;
  color: #e8e8e8;
  line-height: 1.55;
  font-size: 15px;
}

/* ряд соц-кнопок */
.social-row { display:flex; gap:10px; flex-wrap:wrap; margin:8px 0 2px 0; }
.btn {
  display:inline-block; padding:10px 14px; border-radius:8px; text-decoration:none;
  color:#fff; font-weight:600; font-size:14px;
}
.btn-yt { background:#FF0000; }
.btn-tt { background:#000000; border:1px solid #333; }
.btn-tw { background:#9146FF; }

/* донат-плашка с мягкой пульсацией жёлтого */
.donate-box {
  position: relative;
  background: linear-gradient(135deg, #2a2200, #1a1600);
  border: 1px solid #4d3b00;
  border-radius: 12px;
  padding: 14px 16px;
  color: #ffd666;
  margin-top: 10px;
  overflow: hidden;
}
.donate-pulse {
  position: absolute;
  inset: -40%;
  background: radial-gradient(circle, rgba(255, 223, 0, 0.16) 0%, rgba(0,0,0,0) 60%);
  animation: pulse 2.8s ease-in-out infinite;
  pointer-events: none;
}
@keyframes pulse {
  0% { transform: scale(0.9); opacity: 0.35; }
  50% { transform: scale(1.05); opacity: 0.55; }
  100% { transform: scale(0.9); opacity: 0.35; }
}

/* предупреждения */
.warn {
  background:#1b1b1b; border:1px solid #3a3a3a; color:#ffec99;
  padding:10px 12px; border-radius:8px; margin:8px 0;
}
</style>
""", unsafe_allow_html=True)

# ---------- загрузка базы и нормализация ----------
@st.cache_data
def load_builds():
    df = pd.read_csv("builds.csv")
    # канонизируем основные колонки (если имена отличаются)
    def ensure_col(df, canon, variants):
        for v in variants:
            if v in df.columns:
                df[canon] = df[v]
                break
        if canon not in df.columns:
            df[canon] = ""
        return df

    df = ensure_col(df, "CPU", ["CPU","cpu","Процессор"])
    df = ensure_col(df, "GPU", ["GPU","gpu","Видеокарта"])
    df = ensure_col(df, "RAM", ["RAM","ram","ОЗУ"])

    df = ensure_col(df, "Game Settings", ["Game Settings","Settings","Графика"])
    df = ensure_col(df, "Launch Options", ["Launch Options","Params","Параметры запуска"])
    df = ensure_col(df, "Control Panel", ["Control Panel","Driver Settings","Панель драйвера"])
    df = ensure_col(df, "Windows Optimization", ["Windows Optimization","Windows","Оптимизация Windows"])
    df = ensure_col(df, "FPS Estimate", ["FPS Estimate","FPS","Ожидаемый FPS"])
    df = ensure_col(df, "Source", ["Source","Источник"])

    # унифицируем RAM → '16 GB'
    df["RAM"] = (df["RAM"].astype(str)
                 .str.replace("\u200b","", regex=False)
                 .str.replace("\u00a0"," ", regex=False)  # NBSP
                 .str.lower()
                 .str.replace("гб","gb")
                 .str.replace(" ", "")
                 .str.replace("gb"," GB")
                 )
    # извлекаем число (например, '16 GB' → '16 GB', '16' → '16 GB')
    def normalize_ram_display(s):
        m = re.search(r'(\d+)', str(s))
        if not m: return "8 GB"
        return f"{m.group(1)} GB"

    df["RAM"] = df["RAM"].apply(normalize_ram_display)

    # нормализатор строк для ключей
    def norm(s: str) -> str:
        s = str(s)
        s = s.replace("\u200b","").replace("\u00a0"," ")
        s = s.lower()
        s = s.replace("®","").replace("(tm)","").replace("™","")
        # приведение брендов и суффиксов
        s = s.replace("geforce", "").replace("nvidia", "")
        s = s.replace("radeon", "").replace("amd", "")
        s = s.replace("intel", "").replace("core", "")
        s = s.replace("super", "super").replace("ti", "ti")
        s = s.replace("гб","gb")
        # убрать лишние символы
        s = re.sub(r'[^a-z0-9]+', '', s)
        return s

    # ключи
    df["key_cpu"] = df["CPU"].apply(norm)
    df["key_gpu"] = df["GPU"].apply(norm)
    df["key_ram"] = df["RAM"].apply(norm)
    return df

builds = load_builds()

# ---------- шапка ----------
st.title("⚙️ CS2 Конфигуратор (онлайн)")
st.caption("Подбери готовые настройки: игра, панель драйвера, параметры запуска и базовые оптимизации Windows. Поиск устойчив к регистру/пробелам и вариантам написания.")

# ---------- формы выбора ----------
col1, col2, col3 = st.columns([1,1,1])
with col1:
    cpu_choice = st.selectbox("🖥 Процессор", sorted(builds["CPU"].dropna().unique()))
with col2:
    gpu_choice = st.selectbox("🎮 Видеокарта", sorted(builds["GPU"].dropna().unique()))
with col3:
    ram_choice = st.selectbox("💾 ОЗУ", sorted(builds["RAM"].dropna().unique()))

# ---------- предупреждение про ОЗУ канал ----------
st.markdown('<div class="warn">ℹ️ Напоминание: в одноканальном режиме (1×) FPS ниже, чем в двухканальном (2×). Для ноутбуков это особенно заметно.</div>', unsafe_allow_html=True)

# ---------- соцсети ----------
st.markdown('<div class="social-row">', unsafe_allow_html=True)
st.markdown('<a class="btn btn-tt" href="https://www.tiktok.com/@melevik?_t=ZS-8zQkTQnA4Pf&_r=1" target="_blank">TikTok</a>', unsafe_allow_html=True)
st.markdown('<a class="btn btn-yt" href="https://youtube.com/@melevik-avlaron?si=kRXrCD7GUrVnk478" target="_blank">YouTube</a>', unsafe_allow_html=True)
st.markdown('<a class="btn btn-tw" href="https://m.twitch.tv/melevik/home" target="_blank">Twitch</a>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------- донат (с мягкой пульсацией) ----------
st.markdown("""
<div class="donate-box">
  <div class="donate-pulse"></div>
  <b>Каждый, кто поддержит рублём — попадёт в следующий ролик (титры благодарности)!</b><br>
  <a href="https://www.donationalerts.com/r/melevik" target="_blank" class="btn" style="background:#f1c40f; color:#222; margin-top:8px;">Поддержать на DonatPay / DonationAlerts</a>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ---------- функции подбора ----------
def norm(s: str) -> str:
    s = str(s)
    s = s.replace("\u200b","").replace("\u00a0"," ")
    s = s.lower().replace("®","").replace("(tm)","").replace("™","")
    s = s.replace("geforce","").replace("nvidia","")
    s = s.replace("radeon","").replace("amd","")
    s = s.replace("intel","").replace("core","")
    s = s.replace("гб","gb")
    s = re.sub(r'[^a-z0-9]+', '', s)
    return s

def find_exact(df, cpu, gpu, ram):
    kcpu, kgpu, kram = norm(cpu), norm(gpu), norm(ram)
    hit = df[(df["key_cpu"] == kcpu) & (df["key_gpu"] == kgpu) & (df["key_ram"] == kram)]
    return hit

def find_close(df, cpu, gpu, ram, limit=5):
    # слабая фильтрация по серии CPU/GPU и объему RAM
    kcpu, kgpu, kram = norm(cpu), norm(gpu), norm(ram)
    base = df.copy()
    # приоритизируем по совпадениям
    base["score"] = 0
    base.loc[base["key_cpu"].str.contains(re.escape(kcpu[:6]), na=False), "score"] += 2
    base.loc[base["key_gpu"].str.contains(re.escape(kgpu[:6]), na=False), "score"] += 2
    base.loc[base["key_ram"] == kram, "score"] += 1
    out = base.sort_values(["score"], ascending=False).head(limit)
    return out.drop(columns=["score"])

# ---------- поиск ----------
if st.button("🔍 Найти настройки"):
    exact = find_exact(builds, cpu_choice, gpu_choice, ram_choice)

    # подсветки по вендору
    gpu_str = str(gpu_choice).lower()
    if "rx" in gpu_str or "radeon" in gpu_str or "amd" in gpu_str:
        st.markdown('<div class="warn">⚠️ AMD Radeon: в глобальных настройках не включайте *Radeon Boost/Chill/Enhanced Sync* для всей системы — задавайте профиль только для CS2, чтобы не словить артефакты и нестабильный FPS.</div>', unsafe_allow_html=True)
    if "intel" in gpu_str:
        st.markdown('<div class="warn">ℹ️ Intel iGPU: убедитесь, что CS2 использует дискретную GPU (если есть). В режиме только iGPU держите низкие пресеты и 720p.</div>', unsafe_allow_html=True)

    st.markdown("---")
    if not exact.empty:
        row = exact.iloc[0]

        # очистка неактуальных флагов у запуска (на всякий случай)
        launch_raw = str(row["Launch Options"])
        tokens = launch_raw.split()
        banned = {"-novid", "-nojoy"}  # для CS2 не нужны
        launch_clean = " ".join([t for t in tokens if t not in banned]).strip()

        st.subheader("✅ Рекомендованные настройки")
        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.markdown(f"""
**🖥 Процессор:** {row['CPU']}  
**🎮 Видеокарта:** {row['GPU']}  
**💾 ОЗУ:** {row['RAM']}

**🎮 Настройки игры:**  
{row['Game Settings']}

**🚀 Параметры запуска (очищенные):**  
`{launch_clean}`

**🎛 Панель драйвера (NVIDIA/AMD):**  
{row['Control Panel']}

**🪟 Оптимизация Windows (по желанию):**  
{row['Windows Optimization']}

**📊 Ожидаемый FPS:** {row['FPS Estimate']}  
**🔗 Источник:** {row['Source']}
""")
        st.markdown('</div>', unsafe_allow_html=True)

        # скачать профиль
        profile_txt = (
            f"CPU: {row['CPU']}\nGPU: {row['GPU']}\nRAM: {row['RAM']}\n\n"
            f"[Game Settings]\n{row['Game Settings']}\n\n"
            f"[Launch Options]\n{launch_clean}\n\n"
            f"[Control Panel]\n{row['Control Panel']}\n\n"
            f"[Windows Optimization]\n{row['Windows Optimization']}\n\n"
            f"FPS Estimate: {row['FPS Estimate']}\nSource: {row['Source']}\n"
        )
        st.download_button("💾 Скачать профиль (.txt)", data=profile_txt, file_name="cs2_profile.txt")

    else:
        st.warning("Похоже, точной записи нет. Вот близкие варианты:")
        close = find_close(builds, cpu_choice, gpu_choice, ram_choice, limit=6)
        for _, r in close.iterrows():
            st.markdown('<div class="result-box">', unsafe_allow_html=True)
            st.markdown(f"""
**🖥 Процессор:** {r['CPU']}  
**🎮 Видеокарта:** {r['GPU']}  
**💾 ОЗУ:** {r['RAM']}

**🎮 Настройки игры:** {r['Game Settings']}  
**🚀 Параметры запуска:** `{str(r['Launch Options']).strip()}`  
**🎛 Панель драйвера:** {r['Control Panel']}  
**🪟 Windows:** {r['Windows Optimization']}  
**📊 FPS:** {r['FPS Estimate']} · **Источник:** {r['Source']}
""")
            st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ---------- Twitch (онлайн) ----------
st.subheader("🎥 Twitch — прямая трансляция (если идёт)")
st.components.v1.iframe(
    "https://player.twitch.tv/?channel=melevik&parent=share.streamlit.io&muted=true",
    height=360, scrolling=False
)

# ---------- YouTube (последнее полноценное видео) ----------
st.subheader("📺 YouTube — последнее видео (не шортс)")
st.components.v1.iframe(
    "https://www.youtube.com/embed?listType=user_uploads&list=melevik-avlaron",
    height=360, scrolling=False
)
