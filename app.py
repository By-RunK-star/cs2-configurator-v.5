# -*- coding: utf-8 -*-
import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="CS2 Конфигуратор", page_icon="🎮", layout="centered")

# ------------------------------
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ------------------------------

def canon_ram(s: str) -> str:
    s = str(s or "").lower().replace("гб", "gb")
    m = re.search(r'(\d+)', s)
    num = m.group(1) if m else ""
    return f"{num}gb" if num else s.replace(" ", "")

def canon_cpu(s: str) -> str:
    """
    Приводим ввод к семейному ключу, как в builds.csv:
    i3-10100F -> i3 10th gen
    i5-12400F -> i5 12th gen
    Ryzen 5 5600 -> ryzen 5 5000
    """
    x = (s or "").lower()
    x = re.sub(r'\(.*?\)|™|®', '', x)
    x = x.replace("processor", "").replace("core", "")
    x = x.replace("intel", "").replace("amd", "").strip()
    x = re.sub(r'\s+', ' ', x)

    # Intel Core i3/i5/i7/i9
    m = re.search(r'(i[3579])[\s\-]*([0-9]{3,5})?', x)
    if m:
        fam = m.group(1).lower()
        digits = m.group(2)
        gen = None
        # "10th/11th/12th gen" в тексте
        m2 = re.search(r'([0-9]{1,2})\s*(st|nd|rd|th)?\s*gen', x)
        if m2:
            gen = int(m2.group(1))
        # по цифрам модели
        if gen is None and digits:
            if len(digits) >= 5:      # 10100, 12400, 14600 => 10/12/14 gen
                gen = int(digits[:2])
            elif len(digits) == 4:    # 8700, 9400 => 8/9 gen
                gen = int(digits[0])
            elif len(digits) == 3:    # 710 => 7 gen (на крайний случай)
                gen = int(digits[0])

        if gen:
            return f"{fam} {gen}th gen"
        # вдруг уже было "i5 12th gen"
        if "gen" in x:
            keep = [w for w in x.split() if w in ["i3", "i5", "i7", "i9", "10th", "11th", "12th", "13th", "14th", "gen"]]
            if keep:
                return " ".join(keep)
        return fam  # fallback

    # AMD Ryzen
    m = re.search(r'ryzen\s*([3579])\s*-?\s*([0-9]{3,4})?', x)
    if m:
        fam = m.group(1)  # "5" из "Ryzen 5"
        digits = m.group(2)
        gen = None
        if digits:
            # 5600, 3600, 2600...
            gen = int(digits[0]) * 1000
        if gen:
            label = {1: "1000", 2: "2000", 3: "3000", 4: "4000", 5: "5000", 7: "7000"}.get(int(str(gen)[0]), str(gen))
            return f"ryzen {fam} {label}"
        # вдруг уже вида "ryzen 5 5000"
        m2 = re.search(r'ryzen\s*[3579]\s*[1275]000', x)
        if m2:
            return re.sub(r'\s+', ' ', m2.group(0))
        return f"ryzen {fam}"

    return re.sub(r'\s+', ' ', x).strip()

def canon_gpu(s: str) -> str:
    """
    Приводим GPU к ключу:
    "GeForce RTX 3060 Ti 8GB" -> "rtx 3060 ti"
    "Radeon RX 580" -> "rx 580"
    """
    x = (s or "").lower()
    x = x.replace("nvidia", "").replace("geforce", "").replace("amd", "").replace("radeon", "")
    x = re.sub(r'\s+', ' ', x).strip()

    variant = ""
    if "super" in x:
        variant = " super"
    elif re.search(r'\bti\b', x) or "ti" in x.replace(" ", ""):
        variant = " ti"
    elif re.search(r'\bxt\b', x):
        variant = " xt"

    fam = ""
    if "rtx" in x:
        fam = "rtx"
    elif "gtx" in x:
        fam = "gtx"
    elif "rx" in x:
        fam = "rx"

    m = re.search(r'(\d{3,4})', x)
    num = m.group(1) if m else ""

    if fam and num:
        return f"{fam} {int(num)}{variant}"

    return x

def ensure_col(df: pd.DataFrame, canon: str, variants: list[str]) -> pd.DataFrame:
    for v in variants:
        if v in df.columns:
            df[canon] = df[v]
            break
    if canon not in df.columns:
        df[canon] = ""
    return df

def make_keys(df: pd.DataFrame) -> pd.DataFrame:
    df["RAM"] = (
        df["RAM"].astype(str)
        .str.replace("ГБ", "GB", regex=False)
        .str.replace("GB", " GB", regex=False)
        .str.replace("  ", " ", regex=False)
        .str.strip()
    )
    df["_cpu_key"] = df["CPU"].map(canon_cpu)
    df["_gpu_key"] = df["GPU"].map(canon_gpu)
    df["_ram_key"] = df["RAM"].map(canon_ram)
    return df

@st.cache_data
def load_data():
    df = pd.read_csv("builds.csv")
    # выравниваем колонки к канону
    df = ensure_col(df, "Game Settings", ["Game Settings", "Settings", "GameSettings"])
    df = ensure_col(df, "Launch Options", ["Launch Options", "Launch", "Params", "LaunchOptions"])
    df = ensure_col(df, "Control Panel", ["Control Panel", "ControlPanel", "Driver Settings", "Driver"])
    df = ensure_col(df, "Windows Optimization", ["Windows Optimization", "Windows Optimizations", "Windows", "Windows Opt"])
    df = ensure_col(df, "FPS Estimate", ["FPS Estimate", "FPS", "FPS Range", "Estimate"])
    df = ensure_col(df, "Source", ["Source"])
    df = make_keys(df)
    return df

builds = load_data()

# ------------------------------
# UI
# ------------------------------
st.title("⚙️ CS2 Конфигуратор (онлайн)")
st.caption("Подбери готовые настройки: игра, панель драйвера, параметры запуска и базовые оптимизации Windows. Поиск устойчив к разным написаниям.")

# Ввод пользователя (оставляю привычный вид)
col1, col2, col3 = st.columns([1,1,1])
with col1:
    cpu_in = st.text_input("🖥 Процессор", placeholder="Intel i5-12400F")
with col2:
    gpu_in = st.text_input("🎮 Видеокарта", placeholder="RTX 3060 Ti")
with col3:
    ram_in = st.text_input("💾 ОЗУ", placeholder="16 GB")

st.markdown("---")

# Блок доната (мягкая жёлтая пульсация)
st.markdown("""
<div style="padding:12px;border-radius:10px;background:linear-gradient(90deg,#FFF3B0,#FFE066,#FFF3B0);
            animation:pulse 2s ease-in-out infinite; text-align:center;">
  <b>Каждый, кто поддержит рублём — попадёт в следующий ролик (титры благодарности)!</b><br>
  👉 <a href="https://www.donationalerts.com/r/melevik" target="_blank">Поддержать на DonatPay / DonationAlerts</a>
</div>
<style>
@keyframes pulse {
  0% { filter: brightness(0.98); }
  50% { filter: brightness(1.06); }
  100% { filter: brightness(0.98); }
}
</style>
""", unsafe_allow_html=True)

# Соцсети в цветах площадок
st.markdown("""
<div style="display:flex; gap:10px; margin-top:10px; flex-wrap:wrap;">
  <a href="https://www.tiktok.com/@melevik?_t=ZS-8zQkTQnA4Pf&_r=1" target="_blank"
     style="background:#000; color:#fff; padding:8px 12px; border-radius:8px; text-decoration:none;">TikTok</a>
  <a href="https://youtube.com/@melevik-avlaron?si=kRXrCD7GUrVnk478" target="_blank"
     style="background:#FF0000; color:#fff; padding:8px 12px; border-radius:8px; text-decoration:none;">YouTube</a>
  <a href="https://m.twitch.tv/melevik/home" target="_blank"
     style="background:#9146FF; color:#fff; padding:8px 12px; border-radius:8px; text-decoration:none;">Twitch</a>
</div>
""", unsafe_allow_html=True)

# Встраивание Twitch/YouTube
with st.expander("🎥 Twitch — прямая трансляция (если идёт)"):
    st.components.v1.iframe(
        "https://player.twitch.tv/?channel=melevik&parent=streamlit.app",
        height=380, scrolling=True
    )
with st.expander("📺 YouTube — последнее видео (не шортс)"):
    st.components.v1.iframe(
        "https://www.youtube.com/embed?listType=user_uploads&list=melevik-avlaron",
        height=380, scrolling=True
    )

st.markdown("---")

# Поиск
if st.button("🔍 Найти настройки"):
    cpu_key = canon_cpu(cpu_in)
    gpu_key = canon_gpu(gpu_in)
    ram_key = canon_ram(ram_in)

    # строгий матч по ключам
    exact = builds[(builds["_cpu_key"] == cpu_key) &
                   (builds["_gpu_key"] == gpu_key) &
                   (builds["_ram_key"] == ram_key)]

    if exact.empty:
        # Похожие варианты (та же серия CPU и та же видеокарта или ближайшие)
        family_cpu = " ".join(cpu_key.split()[:2])  # i5 12th, ryzen 5 ...
        near = builds[
            (builds["_cpu_key"].str.contains(family_cpu, na=False)) &
            (builds["_gpu_key"] == gpu_key)
        ]
        # если пусто, попробуем ослабить GPU до семейства без суффиксов
        if near.empty:
            base_gpu = gpu_key.replace(" ti", "").replace(" super", "").replace(" xt", "")
            near = builds[
                (builds["_cpu_key"].str.contains(family_cpu, na=False)) &
                (builds["_gpu_key"].str.startswith(base_gpu))
            ]

        if near.empty:
            st.warning("Похоже, точной записи нет. Вот близкие варианты по серии/видеокарте (5 шт.):")
            st.dataframe(builds[["CPU","GPU","RAM","Game Settings","Launch Options","Control Panel","Windows Optimization","FPS Estimate"]].head(5))
        else:
            st.info("Точной записи нет, но нашлись близкие по серии. Ниже — лучшая из них.")
            row = near.iloc[0].to_dict()
            launch_clean = " ".join([t for t in str(row.get("Launch Options","")).split() if t not in {"-novid","-nojoy"}])
            st.subheader("✅ Рекомендованные настройки")
            st.markdown(f"""
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
""")
    else:
        row = exact.iloc[0].to_dict()
        launch_clean = " ".join([t for t in str(row.get("Launch Options","")).split() if t not in {"-novid","-nojoy"}])
        st.subheader("✅ Рекомендованные настройки")
        st.markdown(f"""
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
""")

    # Напоминание про одноканал/двухканал
    st.info("ℹ️ Внимание: при **одноканальной** ОЗУ FPS обычно ниже, при **двухканальной** — выше. Для стабильности и кадров — ставьте двухканал (2×8, 2×16 и т.д.).")

    # Опасные тумблеры драйверов — аккуратно
    with st.expander("⚠️ Предупреждение по глобальным настройкам драйверов (AMD/NVIDIA/Intel)"):
        st.markdown("""
- **AMD Radeon Software**: не включайте глобально агрессивные оптимизации (Shader Cache принудительно «AMD Optimized», FRTC, Chill) — лучше на профиль игры.  
- **NVIDIA**: Low Latency Mode, Max Perf — ок, но не заставляйте глобально V-Sync/Aniso/FXAA.  
- **Intel ARC/iGPU**: держите обновления драйверов, не включайте глобальные эксперименты.
""")

st.markdown("---")
st.caption("Подписывайся, чтобы следить за актуальными обновлениями и контентом автора.")
