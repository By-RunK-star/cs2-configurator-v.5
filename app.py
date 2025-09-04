import os
import re
import pandas as pd
import streamlit as st

# ---------- базовые настройки страницы ----------
st.set_page_config(page_title="CS2 Конфигуратор", page_icon="🎮", layout="wide")

# ---------- стили (аккуратные, без лишней вычурности) ----------
st.markdown("""
<style>
/* Карточка рекомендаций на тёмном фоне */
.reco-card {
  background: #0E1117;
  border: 1px solid #30363d;
  border-radius: 10px;
  padding: 18px 18px 6px 18px;
  margin-top: 8px;
  color: #E6EDF3;
}

/* Пульсирующий жёлтый блок доната (ненавязчиво) */
.donate-pulse {
  background: linear-gradient(90deg, #FFDD55, #FFC300, #FFDD55);
  background-size: 200% 200%;
  animation: pulseGlow 3s ease-in-out infinite;
  border: 1px solid #856404;
  border-radius: 10px;
  padding: 14px 16px;
  color: #111;
  font-weight: 600;
}
@keyframes pulseGlow {
  0%   { background-position: 0% 50%;   box-shadow: 0 0 0px rgba(255,195,0,0.25); }
  50%  { background-position: 100% 50%; box-shadow: 0 0 14px rgba(255,195,0,0.35); }
  100% { background-position: 0% 50%;   box-shadow: 0 0 0px rgba(255,195,0,0.25); }
}

/* Соц. кнопки в цветах площадок */
.social-row { display:flex; gap:10px; flex-wrap:wrap; margin-top:8px; }
.btn-social {
  border-radius: 8px; padding: 10px 14px; text-decoration:none; font-weight:700;
  display:inline-flex; align-items:center; gap:8px; color:#fff;
}
.btn-yt    { background:#FF0000; }
.btn-twitch{ background:#9146FF; }
.btn-tt    { background:#111; border:1px solid #222; }
.btn-tt span { background: linear-gradient(90deg,#69C9D0,#EE1D52); -webkit-background-clip:text; color: transparent; }

/* Небольшой серый дисклеймер/предупреждение */
.warn {
  background:#161B22; border:1px solid #30363d; color:#C9D1D9;
  border-radius:10px; padding:12px 14px; margin-top:8px;
}
.warn b { color:#FFD166; }
</style>
""", unsafe_allow_html=True)

# ---------- служебные функции ----------

def try_read_base():
    """Пробуем прочитать базу по приоритету: gz → csv → full.csv"""
    candidates = [
        "builds_site_ready.csv.gz",
        "builds.csv",
        "builds_full.csv",
    ]
    last_err = None
    for path in candidates:
        if os.path.exists(path):
            try:
                return pd.read_csv(path, compression="infer")
            except Exception as e:
                last_err = e
    # если дошли сюда — ничего не прочиталось
    if last_err:
        raise last_err
    raise FileNotFoundError("Не найден ни один файл базы: builds_site_ready.csv.gz / builds.csv / builds_full.csv")

def canonicalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Приводим разные варианты колонок к канону.
    Канон: cpu, gpu, ram, game_settings, launch_options, control_panel, windows_optimization, fps_estimate, source
    + display_cpu/gpu/ram для красивого вывода.
    """
    # карта вариантов -> канон
    variants = {
        "cpu": ["cpu", "CPU", "Cpu", "Процессор", "processor", "Processor", "CPU Model", "CPU_Name"],
        "gpu": ["gpu", "GPU", "Gpu", "Видеокарта", "graphics", "Graphics", "GPU Model", "GPU_Name"],
        "ram": ["ram", "RAM", "Ram", "ОЗУ", "Оперативная память", "memory", "Memory", "RAM (GB)"],
        "game_settings": ["Game Settings", "Settings", "GameSettings", "Игра", "Настройки игры"],
        "launch_options": ["Launch Options", "Launch", "Params", "LaunchOptions", "Параметры запуска"],
        "control_panel": ["Control Panel", "ControlPanel", "Driver Settings", "Driver", "Панель", "Панель драйвера"],
        "windows_optimization": ["Windows Optimization", "Windows Optimizations", "Windows", "Windows Opt", "Оптимизация Windows"],
        "fps_estimate": ["FPS Estimate", "FPS", "FPS Range", "Estimate", "Ожидаемый FPS"],
        "source": ["Source", "Источник"]
    }

    out = pd.DataFrame()
    # переносим "как есть" — пригодятся для красивого отображения
    for col in df.columns:
        out[col] = df[col]

    # создаём канонические
    def first_match(cols):
        for c in cols:
            if c in df.columns:
                return df[c]
        return None

    for canon, names in variants.items():
        m = first_match(names)
        if m is None:
            out[canon] = ""
        else:
            out[canon] = m.astype(str)

    # нормализуем RAM: 16 -> "16 GB", "16GB" -> "16 GB"
    def norm_ram(x: str) -> str:
        s = str(x).strip()
        m = re.search(r"(\d+)", s)
        if not m:
            return s
        num = m.group(1)
        return f"{int(num)} GB"
    out["ram"] = out["ram"].apply(norm_ram)

    # сохраним display_* (оригинал, но очищенный для красоты)
    out["display_cpu"] = out["cpu"].astype(str).str.strip()
    out["display_gpu"] = out["gpu"].astype(str).str.strip()
    out["display_ram"] = out["ram"].astype(str).str.strip()

    # Нормализованные ключи для поиска (без пробелов, в нижнем регистре)
    def key_norm(s: str) -> str:
        return re.sub(r"\s+", "", str(s).lower())

    out["cpu_key"] = out["cpu"].apply(key_norm)
    out["gpu_key"] = out["gpu"].apply(key_norm)
    out["ram_key"] = out["ram"].apply(key_norm)

    # удалим очевидные пустые CPU/GPU/RAM
    out = out[(out["display_cpu"] != "") & (out["display_gpu"] != "") & (out["display_ram"] != "")]
    out = out.drop_duplicates(subset=["cpu_key", "gpu_key", "ram_key"]).reset_index(drop=True)
    return out

@st.cache_data
def load_data():
    df = try_read_base()
    return canonicalize_columns(df)

def clean_launch_options(s: str) -> str:
    """Удаляем неактуальные флаги для CS2 и лишние пробелы"""
    if not isinstance(s, str):
        return ""
    tokens = s.split()
    banned = {"-novid", "-nojoy"}  # договорились исключать
    tokens = [t for t in tokens if t not in banned]
    cleaned = " ".join(tokens)
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned.strip()

def ram_sort_key(val: str):
    m = re.search(r"(\d+)", str(val))
    return int(m.group(1)) if m else 0

# ---------- загрузка базы ----------
try:
    df = load_data()
except Exception as e:
    st.error(f"Не удалось загрузить базу: {e}")
    st.stop()

# ---------- заголовок ----------
st.title("⚙️ CS2 Конфигуратор (онлайн)")
st.caption("Подбери готовые настройки: игра, панель драйвера, параметры запуска и базовые оптимизации Windows. "
           "Поиск устойчив к регистру/пробелам и вариантам написания.")

# ---------- панель управления (слева) ----------
col_left, col_right = st.columns([1, 2.2])

with col_left:
    # селекты из «красивых» колонок
    cpu_choice = st.selectbox("🖥 Процессор", sorted(df["display_cpu"].unique()))
    gpu_choice = st.selectbox("🎮 Видеокарта", sorted(df["display_gpu"].unique()))
    ram_choice = st.selectbox("💾 ОЗУ", sorted(df["display_ram"].unique(), key=ram_sort_key))

    # кнопка поиска
    find = st.button("🔍 Найти настройки", use_container_width=True)

    # кнопка перезагрузки базы (без падения)
    if st.button("🔄 Перезагрузить базу", use_container_width=True):
        st.cache_data.clear()
        st.success("База перезагружена. Изменения подтянутся при следующем поиске/перезапуске.")

with col_right:
    st.markdown("""
<div class="donate-pulse">
  💛 Каждый, кто поддержит рублём — попадёт в следующий ролик (в титры благодарности)!
  <br>👉 <a href="https://www.donationalerts.com/r/melevik" target="_blank" style="color:#111; text-decoration:underline;">Поддержать на DonatPay / DonationAlerts</a>
</div>
""", unsafe_allow_html=True)

    # Соц. блок — цвета площадок, как просили
    st.markdown("""
<div class="social-row">
  <a class="btn-social btn-tt" href="https://www.tiktok.com/@melevik?_t=ZS-8zQkTQnA4Pf&_r=1" target="_blank">
    <span>TikTok</span>
  </a>
  <a class="btn-social btn-yt" href="https://youtube.com/@melevik-avlaron?si=kRXrCD7GUrVnk478" target="_blank">
    YouTube
  </a>
  <a class="btn-social btn-twitch" href="https://m.twitch.tv/melevik/home" target="_blank">
    Twitch
  </a>
</div>
""", unsafe_allow_html=True)

# ---------- аккордеоны с Twitch/YouTube ----------
with st.expander("🎥 Twitch — прямая трансляция (если идёт)"):
    st.markdown(
        """
<iframe
  src="https://player.twitch.tv/?channel=melevik&parent=share.streamlit.io&parent=streamlit.app"
  height="378" width="620" allowfullscreen="true" frameborder="0">
</iframe>
<p style="color:#8b949e;font-size:12px">
Если окно пустое — стрим сейчас офлайн.
</p>
""",
        unsafe_allow_html=True
    )

with st.expander("📺 YouTube — последнее видео (не шортс)"):
    # универсальная встройка (можно поменять ID на нужный ролик/плейлист)
    st.markdown(
        """
<iframe width="620" height="349"
src="https://www.youtube.com/embed?listType=user_uploads&list=melevik-avlaron"
title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
allowfullscreen></iframe>
<p style="color:#8b949e;font-size:12px">
YouTube может показывать последние загрузки — замени на нужный плейлист/ID, если требуется конкретный ролик.
</p>
""",
        unsafe_allow_html=True
    )

st.markdown("---")

# ---------- логика поиска ----------
def key_norm(s: str) -> str:
    return re.sub(r"\s+", "", str(s).lower())

if find:
    # нормализуем выбор пользователя и таблицу
    cpu_k = key_norm(cpu_choice)
    gpu_k = key_norm(gpu_choice)
    ram_k = key_norm(ram_choice)

    # базовый точный матч по нормализованным ключам
    res = df[(df["cpu_key"] == cpu_k) & (df["gpu_key"] == gpu_k) & (df["ram_key"] == ram_k)]

    # если пусто — попробуем мягче: CPU/GPU точные, RAM только по числу
    if res.empty:
        ram_num = re.search(r"(\d+)", ram_choice)
        if ram_num:
            rn = int(ram_num.group(1))
            res = df[(df["cpu_key"] == cpu_k) & (df["gpu_key"] == gpu_k) & (df["display_ram"].str.contains(str(rn)))]
    # если всё ещё пусто — оставим пользователю понятное сообщение
    st.markdown("---")
    if res.empty:
        st.error("❌ Подходящей конфигурации не найдено. Проверь, что в базе есть ровно такая связка CPU/GPU/RAM.")
    else:
        row = res.iloc[0].copy()

        # очистим параметры запуска
        launch_raw = row.get("launch_options", "")
        launch_clean = clean_launch_options(launch_raw)

        # карточка рекомендаций
        st.markdown('<div class="reco-card">', unsafe_allow_html=True)
        st.markdown(f"### ✅ Рекомендованные настройки")
        st.markdown(f"**🖥 Процессор:** {row.get('display_cpu','')}")
        st.markdown(f"**🎮 Видеокарта:** {row.get('display_gpu','')}")
        st.markdown(f"**💾 ОЗУ:** {row.get('display_ram','')}")

        # блоки настроек
        st.markdown("**🎮 Настройки игры:**")
        st.write(row.get("game_settings", ""))

        st.markdown("**🚀 Параметры запуска (очищенные):**")
        st.code(launch_clean or "—", language="bash")

        st.markdown("**🎛 Панель драйвера (NVIDIA/AMD):**")
        st.write(row.get("control_panel", ""))

        st.markdown("**🪟 Оптимизация Windows (по желанию):**")
        st.write(row.get("windows_optimization", ""))

        # оценка FPS/источник
        fps_txt = row.get("fps_estimate", "—")
        src_txt = row.get("source", "")
        st.markdown(f"**📊 Ожидаемый FPS:** {fps_txt}")
        st.markdown(f"**🔗 Источник:** {src_txt if src_txt else '—'}")

        # RAM канал — общий дисклеймер (без фильтров)
        st.markdown("""
<div class="warn">
<b>Важно про ОЗУ:</b> в одноканальном режиме FPS обычно ниже и чаще бывают микрофризы. 
Для стабильности и лучшего фреймтайма ставьте память <b>двухканалом</b> (2×8, 2×16 и т. п.).
</div>
""", unsafe_allow_html=True)

        # Предостережения по «опасным» глобальным тумблерам
        st.markdown("""
<div class="warn">
<b>Не включайте глобально в драйвере (делайте профиль <i>только</i> для CS2):</b><br>
• <b>NVIDIA</b>: «Максимальная производительность» — включайте в профиле игры, не в глобальном! Иначе карта может держать частоты даже на рабочем столе. <br>
• <b>AMD</b>: Anti-Lag/Anti-Lag+ и Radeon Boost не включайте глобально — только в профиле CS2, иначе возможны конфликты и нестабильность. <br>
• <b>Intel</b>: Режим питания «Максимальная производительность» включайте в профиле, а не глобально (особенно на ноутбуках).
</div>
""", unsafe_allow_html=True)

        # скачать профиль
        profile_txt = (
            f"CPU: {row.get('display_cpu','')}\n"
            f"GPU: {row.get('display_gpu','')}\n"
            f"RAM: {row.get('display_ram','')}\n\n"
            f"[Game Settings]\n{row.get('game_settings','')}\n\n"
            f"[Launch Options]\n{launch_clean}\n\n"
            f"[Control Panel]\n{row.get('control_panel','')}\n\n"
            f"[Windows Optimization]\n{row.get('windows_optimization','')}\n\n"
            f"FPS Estimate: {fps_txt}\n"
            f"Source: {src_txt}\n"
        )
        st.download_button("💾 Скачать профиль (.txt)", data=profile_txt, file_name="cs2_profile.txt")
        st.markdown("</div>", unsafe_allow_html=True)  # /reco-card

# ---------- футер ----------
st.markdown("---")
st.caption("Обновляем базу регулярно. Если у тебя редкая связка — напиши на YouTube, добавим в следующем апдейте.")
