# app.py — CS2 Конфигуратор (RU) — соцкнопки, Single/Dual RAM, тёмная карточка, кнопка обновления

import pandas as pd
import streamlit as st

# --------------------------- НАСТРОЙКИ СТРАНИЦЫ ---------------------------
st.set_page_config(
    page_title="CS2 Конфигуратор",
    page_icon="🎮",
    layout="centered"
)

# --------------------------- CSS СТИЛИ ---------------------------
st.markdown("""
<style>
html, body, [class*="css"]  { font-family: "Inter", system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }

/* соц.кнопки — компактные, с SVG */
.social-wrap { display: flex; gap: 10px; flex-wrap: wrap; margin: 6px 0 12px 0; }
.social-btn {
  text-decoration: none; padding: 8px 12px; border-radius: 10px; font-weight: 700; font-size: 14px;
  display: inline-flex; align-items: center; gap: 8px; color: #fff !important;
  transition: transform .08s ease, box-shadow .12s ease, opacity .2s ease;
}
.social-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(0,0,0,.25); opacity: .95; }
.social-svg { width: 16px; height: 16px; display: inline-block; }
.tiktok  { background: #000; }
.youtube { background: #ff0033; }
.twitch  { background: #9146FF; }

/* донат-плашка (как было) */
.donate-card {
  position: relative;
  border-radius: 14px;
  padding: 16px 16px;
  background: linear-gradient(180deg, #111, #171717);
  border: 1px solid #2a2a2a;
  color: #fff;
  margin: 8px 0 2px 0;
  box-shadow: 0 6px 22px rgba(0,0,0,0.25);
  overflow: hidden;
}
.donate-card h3 { margin: 0 0 6px 0; font-size: 18px; }
.donate-card p { margin: 0 0 10px 0; opacity: .92; }
.pulse-ring {
  position: absolute; inset: -2px; border-radius: 16px; pointer-events: none;
  animation: softPulse 2.2s ease-in-out infinite; border: 2px solid rgba(255, 214, 64, 0.22);
}
@keyframes softPulse { 0%{box-shadow:0 0 0 0 rgba(255,214,64,0.18);}70%{box-shadow:0 0 0 12px rgba(255,214,64,0.06);}100%{box-shadow:0 0 0 0 rgba(255,214,64,0);} }
.donate-link {
  display: inline-block; text-decoration: none; padding: 8px 12px; border-radius: 8px;
  font-weight: 700; background: #ffd740; color: #222 !important;
  transition: transform .08s ease, box-shadow .08s ease;
}
.donate-link:hover { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(255,215,64,.35); }

/* карточка результата — тёмная */
.result-card {
  border-radius: 12px; border: 1px solid #2a2a2a; padding: 14px;
  background: #0f0f12; color: #e8e8ea;
}
.result-card b { color: #ffffff; }
.code-box {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
  background: #0b1220; color: #dbe5ff; padding: 10px 12px; border-radius: 8px; margin: 6px 0 10px 0;
  white-space: pre-wrap; word-break: break-word; border: 1px solid #1e293b;
}
.small-muted { color: #9aa0a6; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# --------------------------- ЗАГРУЗКА ДАННЫХ ---------------------------
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv("builds.csv")

    def ensure_col(frame: pd.DataFrame, canon: str, variants: list[str]) -> pd.DataFrame:
        for v in variants:
            if v in frame.columns:
                frame[canon] = frame[v]
                break
        if canon not in frame.columns:
            frame[canon] = ""
        return frame

    df = ensure_col(df, "CPU", ["CPU", "Processor"])
    df = ensure_col(df, "GPU", ["GPU", "Graphics"])
    df = ensure_col(df, "RAM", ["RAM", "Memory"])
    df = ensure_col(df, "RAM Channel", ["RAM Channel", "RAMChannel", "Memory Channel", "Channel"])
    df = ensure_col(df, "Game Settings", ["Game Settings", "Settings", "GameSettings"])
    df = ensure_col(df, "Launch Options", ["Launch Options", "Launch", "Params", "LaunchOptions"])
    df = ensure_col(df, "Control Panel", ["Control Panel", "ControlPanel", "Driver Settings", "Driver"])
    df = ensure_col(df, "Windows Optimization", ["Windows Optimization", "Windows Optimizations", "Windows", "Windows Opt", "Windows Tweaks"])
    df = ensure_col(df, "FPS Estimate", ["FPS Estimate", "FPS", "FPS Range", "Estimate"])
    df = ensure_col(df, "Source", ["Source"])

    # Нормализация RAM
    df["RAM"] = df["RAM"].astype(str).str.replace("GB", " GB", regex=False).str.replace("  ", " ", regex=False).str.strip()

    # Нормализация канальности
    ch = df["RAM Channel"].astype(str).str.strip().str.lower()
    ch = ch.replace({"single":"Single", "одноканал":"Single", "1":"Single",
                     "dual":"Dual", "двухканал":"Dual", "2":"Dual"})
    ch = ch.where(~ch.isin(["single","dual"]), ch)  # уже норм
    # Приводим к Title («Single», «Dual»), пустые — «—»
    ch = ch.replace({"single":"Single", "dual":"Dual"})
    ch = ch.where(ch.isin(["Single", "Dual"]), "—")
    df["RAM Channel"] = ch

    return df

df = load_data()

# --------------------------- УТИЛИТЫ ---------------------------
def clean_launch_options(s: str) -> str:
    if not isinstance(s, str):
        return ""
    tokens = s.split()
    banned = {"-novid", "-nojoy"}
    tokens = [t for t in tokens if t not in banned]
    cleaned = " ".join(tokens)
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned.strip()

def is_amd_gpu(name: str) -> bool:
    if not isinstance(name, str):
        return False
    n = name.lower()
    return any(k in n for k in ["amd", "radeon", " rx", " r9", " r7", " r5"])

def show_amd_global_warning():
    st.warning(
        "### Важно для владельцев AMD (Radeon)\n"
        "Критичные переключатели **включаем только в профиле CS2**, не глобально:\n"
        "- **Anti-Lag / Anti-Lag+ / Anti-Lag 2** — не включайте глобально. Только поигрово.\n"
        "- **Chill (Global)** — может занижать FPS и дёргать фреймтайм.\n"
        "- **FRTC (Global)** — глобальный лимит FPS повышает задержку, конфликтует с `fps_max`.\n"
        "- **V-Sync = Always On (Global)** — увеличивает задержку.\n"
        "- **Enhanced Sync (Global)** — возможны фликеры/разрывы.\n"
        "- **RSR/VSR (Global)** — не опасно, но может блюрить; включайте осознанно.\n"
        "- **Tessellation/AF Override/MLAA (Global)** — держите **Use application settings** и управляйте в игре.\n\n"
        "➡️ Путь: **AMD Adrenalin → Gaming → Games → CS2** — создайте профиль и настраивайте всё там.",
        icon="⚠️"
    )

def g(row: dict, key: str, fallback: str = "") -> str:
    v = row.get(key, fallback)
    return "" if pd.isna(v) else str(v)

# --------------------------- ШАПКА ---------------------------
st.title("⚙️ Конфигуратор CS2")
st.caption("Подбери готовые настройки по своей сборке: параметры игры, панель драйвера, параметры запуска и оптимизации Windows.")

# Социальные кнопки (с SVG)
st.subheader("📣 Подписывайся, чтобы следить за актуальными обновлениями и контентом автора")
st.markdown(
    """
<div class="social-wrap">
  <a class="social-btn tiktok" href="https://www.tiktok.com/@melevik?_t=ZS-8zQkTQnA4Pf&_r=1" target="_blank">
    <svg class="social-svg" viewBox="0 0 24 24" fill="white"><path d="M16 8.04c1.32.98 2.94 1.57 4.7 1.57V6.3a6.88 6.88 0 0 1-4.7-1.97V4h-3.7v11.26a2.49 2.49 0 1 1-2.49-2.49c.19 0 .38.02.56.06V9.04A6.19 6.19 0 0 0 6.3 8.6a6.19 6.19 0 1 0 10.7 4.45V8.04z"/></svg>
    TikTok
  </a>
  <a class="social-btn youtube" href="https://youtube.com/@melevik-avlaron?si=kRXrCD7GUrVnk478" target="_blank">
    <svg class="social-svg" viewBox="0 0 24 24" fill="white"><path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.6 3.5 12 3.5 12 3.5s-7.6 0-9.4.6A3 3 0 0 0 .5 6.2 31.3 31.3 0 0 0 0 12a31.3 31.3 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.8.6 9.4.6 9.4.6s7.6 0 9.4-.6a3 3 0 0 0 2.1-2.1c.3-1.9.5-3.8.5-5.8s-.2-3.9-.5-5.8zM9.6 15.5V8.5L15.8 12l-6.2 3.5z"/></svg>
    YouTube
  </a>
  <a class="social-btn twitch" href="https://m.twitch.tv/melevik/home" target="_blank">
    <svg class="social-svg" viewBox="0 0 24 24" fill="white"><path d="M4 3l-2 4v12h5v3h3l3-3h4l5-5V3H4zm16 9l-3 3h-5l-3 3v-3H6V5h14v7zM14 7h2v5h-2V7zm-5 0h2v5H9V7z"/></svg>
    Twitch
  </a>
</div>
""",
    unsafe_allow_html=True
)

st.markdown("---")

# --------------------------- ФИЛЬТРЫ ---------------------------
col1, col2 = st.columns(2)
with col1:
    cpu = st.selectbox("🖥 Процессор (CPU):", sorted(df["CPU"].dropna().unique()))
with col2:
    gpu = st.selectbox("🎮 Видеокарта (GPU):", sorted(df["GPU"].dropna().unique()))

ram = st.selectbox("💾 Оперативная память (RAM):", sorted(df["RAM"].dropna().unique()))

# Канальность ОЗУ — всегда показываем селектор с понятными метками
ram_ch_human = st.selectbox("🧠 Канальность ОЗУ:", ["Неважно", "Одноканал", "Двухканал"])
# Преобразование в значения базы
ram_ch_map = {"Одноканал": "Single", "Двухканал": "Dual"}

# Кнопка обновления базы
if st.button("🔁 Обновить базу"):
    load_data.clear()
    st.rerun()

# --------------------------- ПОИСК ---------------------------
if st.button("🔍 Найти настройки"):
    q = (df["CPU"] == cpu) & (df["GPU"] == gpu) & (df["RAM"] == ram)
    if ram_ch_human in ram_ch_map:
        q = q & (df["RAM Channel"] == ram_ch_map[ram_ch_human])

    result = df[q]

    st.markdown("---")

    if result.empty:
        st.error("❌ Подходящая конфигурация не найдена в базе.")
    else:
        row = result.iloc[0].to_dict()

        # AMD предупреждение
        if is_amd_gpu(g(row, "GPU")):
            show_amd_global_warning()

        # Очистка параметров запуска
        launch_clean = clean_launch_options(g(row, "Launch Options"))

        # Человекочитаемая канальность в выводе
        ram_channel_val = g(row, "RAM Channel")
        ram_channel_human = "Двухканал" if ram_channel_val == "Dual" else ("Одноканал" if ram_channel_val == "Single" else "")

        # Карточка результата (тёмная)
        st.subheader("✅ Рекомендованные настройки")
        st.markdown(
            f"""
<div class="result-card">
<b>🖥 Процессор:</b> {g(row, "CPU")}<br/>
<b>🎮 Видеокарта:</b> {g(row, "GPU")}<br/>
<b>💾 ОЗУ:</b> {g(row, "RAM")}{("  ·  "+ram_channel_human) if ram_channel_human else ""}

<b>🎮 Настройки игры:</b><br/>
{g(row, "Game Settings")}

<b>🚀 Параметры запуска (очищенные):</b>
<div class="code-box">{launch_clean if launch_clean else "—"}</div>

<b>🎛 Панель драйвера (NVIDIA/AMD):</b><br/>
{g(row, "Control Panel")}

<b>🪟 Оптимизация Windows (по желанию):</b><br/>
{g(row, "Windows Optimization")}

<b>📊 Ожидаемый FPS:</b> {g(row, "FPS Estimate", "—")}<br/>
<span class="small-muted"><b>🔗 Источник:</b> {g(row, "Source", "—")}</span>
</div>
""",
            unsafe_allow_html=True
        )

        # Профиль для скачивания
        profile_txt = (
            f"CPU: {g(row,'CPU')}\n"
            f"GPU: {g(row,'GPU')}\n"
            f"RAM: {g(row,'RAM')} {('('+ram_channel_human+')') if ram_channel_human else ''}\n\n"
            f"[Game Settings]\n{g(row,'Game Settings')}\n\n"
            f"[Launch Options]\n{launch_clean}\n\n"
            f"[Control Panel]\n{g(row,'Control Panel')}\n\n"
            f"[Windows Optimization]\n{g(row,'Windows Optimization')}\n\n"
            f"FPS Estimate: {g(row,'FPS Estimate','—')}\n"
            f"Source: {g(row,'Source','—')}\n"
        )
        st.download_button("💾 Скачать профиль (.txt)", data=profile_txt, file_name="cs2_profile.txt", type="primary")

st.markdown("---")

# --------------------------- ДОНАТ-ПЛАШКА (без изменений) ---------------------------
st.markdown(
    """
<div class="donate-card">
  <div class="pulse-ring"></div>
  <h3>💛 Поддержи проект</h3>
  <p>Каждый, кто поддержит рублём — попадёт в <b>следующий ролик</b>. Спасибо за помощь сообществу!</p>
  <a class="donate-link" href="https://www.donationalerts.com/r/melevik" target="_blank">Поддержать на DonatPay</a>
</div>
""",
    unsafe_allow_html=True
)
st.caption("Чем больше поддержка — тем чаще обновляем и расширяем базу сборок и настроек.")

