# app.py — CS2 Конфигуратор (RU)
# Всё на русском, с донат-плашкой, соц.кнопками и предупреждением для AMD.

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
/* аккуратная типографика */
html, body, [class*="css"]  { font-family: "Inter", system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }

/* секция соц.кнопок */
.social-wrap {
  display: flex; gap: 10px; flex-wrap: wrap; margin-top: 8px; margin-bottom: 6px;
}
.social-btn {
  text-decoration: none; padding: 8px 12px; border-radius: 8px; font-weight: 600; font-size: 14px;
  display: inline-flex; align-items: center; gap: 8px; transition: transform .1s ease, box-shadow .1s ease;
  color: white !important;
}
.social-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(0,0,0,.15); }
.tiktok { background: #000000; }
.youtube { background: #FF0000; }
.twitch { background: #9146FF; }

/* донат-плашка — мягкая, с лёгкой пульсацией */
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
  position: absolute; inset: -2px;
  border-radius: 16px;
  pointer-events: none;
  animation: softPulse 2.2s ease-in-out infinite;
  border: 2px solid rgba(255, 214, 64, 0.22);
}
@keyframes softPulse {
  0%   { box-shadow: 0 0 0 0 rgba(255,214,64,0.18); }
  70%  { box-shadow: 0 0 0 12px rgba(255,214,64,0.06); }
  100% { box-shadow: 0 0 0 0 rgba(255,214,64,0.00); }
}
.donate-link {
  display: inline-block; text-decoration: none; padding: 8px 12px; border-radius: 8px;
  font-weight: 700; background: #ffd740; color: #222 !important;
  transition: transform .08s ease, box-shadow .08s ease;
}
.donate-link:hover { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(255,215,64,.35); }

/* аккуратная карточка результата */
.result-card {
  border-radius: 12px; border: 1px solid #e9e9e9; padding: 14px;
  background: #fff;
}
.code-box {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
  background: #0f172a; color: #e2e8f0; padding: 10px 12px; border-radius: 8px; margin: 6px 0 10px 0;
  white-space: pre-wrap; word-break: break-word;
}
.small-muted { color: #667085; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# --------------------------- ЗАГРУЗКА ДАННЫХ ---------------------------
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv("builds.csv")

    # Функция выравнивания столбцов к «каноническим» именам
    def ensure_col(frame: pd.DataFrame, canon: str, variants: list[str]) -> pd.DataFrame:
        for v in variants:
            if v in frame.columns:
                frame[canon] = frame[v]
                break
        if canon not in frame.columns:
            frame[canon] = ""
        return frame

    # Выравниваем ключевые поля
    df = ensure_col(df, "CPU", ["CPU", "Processor"])
    df = ensure_col(df, "GPU", ["GPU", "Graphics"])
    df = ensure_col(df, "RAM", ["RAM", "Memory"])
    df = ensure_col(df, "RAM Channel", ["RAM Channel", "RAMChannel", "Memory Channel"])
    df = ensure_col(df, "Game Settings", ["Game Settings", "Settings", "GameSettings"])
    df = ensure_col(df, "Launch Options", ["Launch Options", "Launch", "Params", "LaunchOptions"])
    df = ensure_col(df, "Control Panel", ["Control Panel", "ControlPanel", "Driver Settings", "Driver"])
    df = ensure_col(df, "Windows Optimization", ["Windows Optimization", "Windows Optimizations", "Windows", "Windows Opt", "Windows Tweaks"])
    df = ensure_col(df, "FPS Estimate", ["FPS Estimate", "FPS", "FPS Range", "Estimate"])
    df = ensure_col(df, "Source", ["Source"])

    # Нормализуем RAM (чтобы «16GB» → «16 GB»)
    df["RAM"] = df["RAM"].astype(str).str.replace("GB", " GB", regex=False).str.replace("  ", " ", regex=False).str.strip()

    # Нормализуем RAM Channel
    df["RAM Channel"] = df["RAM Channel"].astype(str).str.strip()
    df.loc[df["RAM Channel"].str.len() == 0, "RAM Channel"] = "—"

    return df

df = load_data()

# --------------------------- УТИЛИТЫ ---------------------------
def clean_launch_options(s: str) -> str:
    """Удаляем неактуальные флаги для CS2: -novid, -nojoy; чистим пробелы."""
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
    return any(k in n for k in ["amd", "radeon", " rx", " rx ", " r9", " r7", " r5"])

def show_amd_global_warning():
    st.warning(
        "### Важно для владельцев AMD (Radeon)\n"
        "Критичные переключатели **включаем только в профиле CS2**, не глобально:\n"
        "- **Anti-Lag / Anti-Lag+ / Anti-Lag 2** — не включайте глобально. Только поигрово.\n"
        "- **Chill (Global)** — может занижать FPS и дёргать фреймтайм.\n"
        "- **FRTC (Global)** — глобальный лимит FPS повышает задержку, конфликтует с `fps_max`.\n"
        "- **V-Sync = Always On (Global)** — увеличивает задержку.\n"
        "- **Enhanced Sync (Global)** — возможны фликеры/разрывы.\n"
        "- **RSR/VSR (Global)** — не опасно, но бывает блюрит и влияет на захват; включайте осознанно.\n"
        "- **Tessellation Override / AF Override / MLAA (Global)** — используйте **Use application settings** и управляйте в игре.\n\n"
        "➡️ Путь: **AMD Adrenalin → Gaming → Games → CS2** → создайте профиль и настраивайте всё там.",
        icon="⚠️"
    )

# безопасное получение поля
def g(row: dict, key: str, fallback: str = "") -> str:
    v = row.get(key, fallback)
    return "" if pd.isna(v) else str(v)

# --------------------------- ШАПКА ---------------------------
st.title("⚙️ Конфигуратор CS2")
st.caption("Подбери готовые настройки по своей сборке: параметры игры, панель драйвера, параметры запуска и оптимизации Windows.")

# Социальные кнопки
st.subheader("📣 Подписывайся, чтобы следить за актуальными обновлениями и контентом автора")
st.markdown(
    """
<div class="social-wrap">
  <a class="social-btn tiktok"   href="https://www.tiktok.com/@melevik?_t=ZS-8zQkTQnA4Pf&_r=1" target="_blank">🎵 TikTok</a>
  <a class="social-btn youtube"  href="https://youtube.com/@melevik-avlaron?si=kRXrCD7GUrVnk478" target="_blank">▶️ YouTube</a>
  <a class="social-btn twitch"   href="https://m.twitch.tv/melevik/home" target="_blank">🟣 Twitch</a>
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

# Профиль канальности RAM — показываем только если колонка есть и в ней есть значения
ram_channel_selector = None
if "RAM Channel" in df.columns and (df["RAM Channel"] != "—").any():
    ram_channel_selector = st.selectbox("🧠 Канальность оперативной памяти:", ["Неважно", "Single", "Dual"])
else:
    ram_channel_selector = "Неважно"

# --------------------------- ПОИСК ---------------------------
if st.button("🔍 Найти настройки"):
    q = (df["CPU"] == cpu) & (df["GPU"] == gpu) & (df["RAM"] == ram)
    if ram_channel_selector in ["Single", "Dual"] and "RAM Channel" in df.columns:
        q = q & (df["RAM Channel"].str.lower() == ram_channel_selector.lower())

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

        # Карточка результата
        st.subheader("✅ Рекомендованные настройки")
        st.markdown(
            f"""
<div class="result-card">
<b>🖥 Процессор:</b> {g(row, "CPU")}  
<b>🎮 Видеокарта:</b> {g(row, "GPU")}  
<b>💾 ОЗУ:</b> {g(row, "RAM")}{"  ·  "+g(row, "RAM Channel") if g(row, "RAM Channel") not in ("", "—") else ""}

<b>🎮 Настройки игры:</b><br/>
{g(row, "Game Settings")}

<b>🚀 Параметры запуска (очищенные):</b>
<div class="code-box">{launch_clean if launch_clean else "—"}</div>

<b>🎛 Панель драйвера (NVIDIA/AMD):</b><br/>
{g(row, "Control Panel")}

<b>🪟 Оптимизация Windows (по желанию):</b><br/>
{g(row, "Windows Optimization")}

<b>📊 Ожидаемый FPS:</b> {g(row, "FPS Estimate", "—")}  
<span class="small-muted"><b>🔗 Источник:</b> {g(row, "Source", "—")}</span>
</div>
""",
            unsafe_allow_html=True
        )

        # Удобный текст-профиль + скачивание
        profile_txt = (
            f"CPU: {g(row,'CPU')}\n"
            f"GPU: {g(row,'GPU')}\n"
            f"RAM: {g(row,'RAM')} {('('+g(row,'RAM Channel')+')') if g(row,'RAM Channel') not in ('','—') else ''}\n\n"
            f"[Game Settings]\n{g(row,'Game Settings')}\n\n"
            f"[Launch Options]\n{launch_clean}\n\n"
            f"[Control Panel]\n{g(row,'Control Panel')}\n\n"
            f"[Windows Optimization]\n{g(row,'Windows Optimization')}\n\n"
            f"FPS Estimate: {g(row,'FPS Estimate','—')}\n"
            f"Source: {g(row,'Source','—')}\n"
        )
        st.download_button("💾 Скачать профиль (.txt)", data=profile_txt, file_name="cs2_profile.txt", type="primary")

st.markdown("---")

# --------------------------- ДОНАТ-ПЛАШКА ---------------------------
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

