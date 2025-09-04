import re
import io
import pandas as pd
import streamlit as st

# ============= НАСТРОЙКИ И СТИЛИ =============
st.set_page_config(page_title="CS2 Конфигуратор", page_icon="🎮", layout="centered")

st.markdown("""
<style>
/* Соц-кнопки */
.badge-row { display:flex; gap:10px; flex-wrap:wrap; margin-top:6px; }
.badge {
  text-decoration:none; padding:8px 12px; border-radius:10px;
  font-weight:700; border:1px solid rgba(255,255,255,0.18);
  display:inline-flex; align-items:center; gap:8px;
}
.badge:hover { filter:brightness(1.08); }
.badge-yt { background:#FF0000; color:#fff; }
.badge-tt { background:#111; color:#fff; }
.badge-tw { background:#9146FF; color:#fff; }

/* Мягкая пульсация донат-блока */
.donate-box {
  border:1px solid rgba(255,255,255,0.14);
  border-radius:12px; padding:14px;
  background:rgba(255,255,255,0.04);
  margin:14px 0;
  animation:pulse 2.8s ease-in-out infinite;
}
@keyframes pulse {
  0%   { box-shadow:0 0 0 0 rgba(255,215,0,0.0); }
  50%  { box-shadow:0 0 20px 2px rgba(255,215,0,0.16); }
  100% { box-shadow:0 0 0 0 rgba(255,215,0,0.0); }
}

/* Аккуратные блоки-коды */
.code-wrap {
  border:1px solid rgba(255,255,255,0.12);
  border-radius:8px; padding:10px 12px;
  background:rgba(255,255,255,0.03);
  white-space:pre-wrap;
}

/* Маленькие подсказки */
.small-note { opacity:0.85; font-size:0.92rem; }

/* Иконки-метки слева от заголовков */
.hicon { opacity:0.9; margin-right:6px; }
</style>
""", unsafe_allow_html=True)

# ============= ЗАГРУЗКА ДАННЫХ =============
@st.cache_data
def load_data():
    df = pd.read_csv("builds.csv")

    # Канонизируем столбцы, чтобы не падало, если имена слегка отличаются
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

    # Нормализуем RAM (8 GB / 16 GB …)
    df["RAM"] = df["RAM"].astype(str)\
        .str.replace("GB", " GB", regex=False)\
        .str.replace("  "," ", regex=False).str.strip()
    return df

df = load_data()

# ============= ХЕЛПЕРЫ =============
BANNED_FLAGS = {"-novid", "-nojoy"}  # убираем из запуска

def clean_launch_options(s: str) -> str:
    if not isinstance(s, str):
        return ""
    toks = s.split()
    toks = [t for t in toks if t not in BANNED_FLAGS]
    cleaned = " ".join(toks).strip()
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned

def reduce_fps_text(fps_text: str, ratio: float = 0.85) -> str:
    """
    Понижаем FPS, если одноканал. Поддерживает "250–300", "~280", "280".
    Если распарсить нельзя — возвращаем исходный текст.
    """
    s = str(fps_text)
    nums = list(map(int, re.findall(r"\d+", s)))
    if not nums:
        return s
    if "–" in s or "-" in s:
        # диапазон
        if len(nums) >= 2:
            a, b = nums[0], nums[1]
            a2 = max(1, int(a * ratio))
            b2 = max(1, int(b * ratio))
            return f"{a2}–{b2}"
    # одиночное значение
    n2 = max(1, int(nums[0] * ratio))
    return f"~{n2}"

def add_single_channel_tips(text: str) -> str:
    """
    Добавляем короткий совет для 1 канала.
    """
    tip = "\n\n• Одноканал: ожидай -10–25% FPS. Для стабильности: снизить MSAA/фильтрацию, убрать тени на «Низко», ограничить FPS (~90–95% от среднего)."
    t = (text or "").strip()
    return (t + tip) if t else tip

def looks_dangerous_nvidia(cp_text: str) -> bool:
    """
    Если в рекомендациях панели встречается «макс. производительность» — подсветим предупреждение.
    """
    s = (cp_text or "").lower()
    return ("макс" in s and "производ" in s) or ("prefer maximum" in s and "performance" in s)

@st.cache_data
def augment_with_ram_channel(_df: pd.DataFrame) -> pd.DataFrame:
    """
    Делаем расширенную базу с колонкой RAM Channel и дублируем строки: Dual / Single.
    В Single снижаем FPS, добавляем подсказку.
    """
    rows = []
    for _, r in _df.iterrows():
        base = dict(r)

        # Dual
        dual = dict(base)
        dual["RAM Channel"] = "Dual"
        rows.append(dual)

        # Single — FPS ниже + советы в game settings/windows
        single = dict(base)
        single["RAM Channel"] = "Single"

        # FPS
        single["FPS Estimate"] = reduce_fps_text(single.get("FPS Estimate", ""), 0.85)

        # Game settings & Windows optimization дополним советами
        single["Game Settings"] = add_single_channel_tips(single.get("Game Settings", ""))
        win_opt = single.get("Windows Optimization", "")
        win_tip = "• Добавь вторую планку ОЗУ → двухканал почти всегда даёт ощутимый прирост в CS2."
        single["Windows Optimization"] = (win_opt + ("\n\n" if win_opt else "") + win_tip)

        rows.append(single)

    out = pd.DataFrame(rows)
    # Порядок столбцов — понятный
    cols = ["CPU","GPU","RAM","RAM Channel",
            "Game Settings","Launch Options","Control Panel","Windows Optimization",
            "FPS Estimate","Source"]
    return out[[c for c in cols if c in out.columns] + [c for c in out.columns if c not in cols]]

# ============= UI =============
st.title("CS2 Конфигуратор")
st.caption("Подбери готовые настройки под свою сборку: игра, панель драйвера, параметры запуска и оптимизации Windows.")

# Соц-ссылки (актуальные бейджи)
st.markdown("**Мои каналы:**")
st.markdown("""
<div class="badge-row">
  <a class="badge badge-tt" href="https://www.tiktok.com/@melevik?_t=ZS-8zQkTQnA4Pf&_r=1" target="_blank">TikTok</a>
  <a class="badge badge-yt" href="https://youtube.com/@melevik-avlaron?si=kRXrCD7GUrVnk478" target="_blank">YouTube</a>
  <a class="badge badge-tw" href="https://m.twitch.tv/melevik/home" target="_blank">Twitch</a>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Фильтры + выбор канальности ОЗУ
c1, c2, c3, c4 = st.columns([1,1,1,1])
with c1:
    cpu = st.selectbox("🖥️ Процессор", sorted(df["CPU"].dropna().unique()))
with c2:
    gpu = st.selectbox("🎮 Видеокарта", sorted(df["GPU"].dropna().unique()))
with c3:
    ram = st.selectbox("💾 ОЗУ", sorted(df["RAM"].dropna().unique()))
with c4:
    ram_channel = st.radio("🧩 Канал ОЗУ", ["Dual", "Single"], index=0, horizontal=True)

st.markdown('<div class="small-note">💡 Двухканал (две планки) часто даёт лучший прирост FPS в CS2. Одноканал — минус 10–25% в типичных сценах.</div>', unsafe_allow_html=True)

# Поиск
if st.button("🔍 Найти настройки"):
    result = df[(df["CPU"] == cpu) & (df["GPU"] == gpu) & (df["RAM"] == ram)]
    st.markdown("---")

    if result.empty:
        st.error("❌ Подходящей конфигурации не найдено. Попробуй другой объём ОЗУ или соседнюю серию CPU/GPU.")
    else:
        row = result.iloc[0].to_dict()
        # Очищаем запуск
        launch = clean_launch_options(row.get("Launch Options",""))
        # Применяем эффекты для выбранного канала
        game_settings = row.get("Game Settings","")
        windows_opt = row.get("Windows Optimization","")
        fps_text = row.get("FPS Estimate","—")

        if ram_channel == "Single":
            game_settings = add_single_channel_tips(game_settings)
            fps_text = reduce_fps_text(fps_text, 0.85)
            win_tip = "• Добавь вторую планку ОЗУ (двухканал) — это почти всегда самый заметный апгрейд для CS2."
            windows_opt = (windows_opt + ("\n\n" if windows_opt else "") + win_tip)

        # Заголовок
        st.subheader("✅ Рекомендованные настройки")
        st.markdown(f"**🖥️ Процессор:** {row.get('CPU','')}  \n"
                    f"**🎮 Видеокарта:** {row.get('GPU','')}  \n"
                    f"**💾 ОЗУ:** {row.get('RAM','')}  \n"
                    f"**🧩 Канал ОЗУ:** {ram_channel}")

        # Блоки-результаты
        st.markdown("#### <span class='hicon'>🎮</span> Настройки игры", unsafe_allow_html=True)
        st.markdown(f"<div class='code-wrap'>{game_settings.strip() or '—'}</div>", unsafe_allow_html=True)

        st.markdown("#### <span class='hicon'>🚀</span> Параметры запуска (очищенные)", unsafe_allow_html=True)
        st.code(launch or "—")

        st.markdown("#### <span class='hicon'>🎛️</span> Панель драйвера (NVIDIA / AMD)", unsafe_allow_html=True)
        cp_text = (row.get("Control Panel","") or "").strip()
        st.markdown(f"<div class='code-wrap'>{cp_text or '—'}</div>", unsafe_allow_html=True)

        # Предупреждение про «Макс. производительность» (только для профиля игры)
        if looks_dangerous_nvidia(cp_text):
            st.info("Совет: «Предпочтителен режим максимальной производительности» включай **только в профиле CS2 (cs2.exe)**, не глобально — иначе карта будет держать высокие частоты даже на рабочем столе.")

        st.markdown("#### <span class='hicon'>🪟</span> Оптимизация Windows (по желанию)", unsafe_allow_html=True)
        st.markdown(f"<div class='code-wrap'>{windows_opt.strip() or '—'}</div>", unsafe_allow_html=True)

        # FPS + источник
        st.markdown(f"**📊 Ожидаемый FPS:** {fps_text if str(fps_text).strip() else '—'}")
        st.caption(f"Источник профиля: {row.get('Source','—')}")

        # Скачать профиль в .txt
        profile_txt = (
            f"CPU: {row.get('CPU','')}\n"
            f"GPU: {row.get('GPU','')}\n"
            f"RAM: {row.get('RAM','')}\n"
            f"RAM Channel: {ram_channel}\n\n"
            f"[Game Settings]\n{game_settings.strip()}\n\n"
            f"[Launch Options]\n{launch}\n\n"
            f"[Control Panel]\n{cp_text}\n\n"
            f"[Windows Optimization]\n{windows_opt.strip()}\n\n"
            f"FPS Estimate: {fps_text}\n"
            f"Source: {row.get('Source','')}\n"
        )
        st.download_button("💾 Скачать профиль (.txt)", data=profile_txt, file_name="cs2_profile.txt")

        # Мини-FAQ
        with st.expander("💬 Мини-FAQ по задержкам, FPS и полезным тумблерам"):
            st.markdown("""
- **V-Sync** — выключить (даёт задержку). Если нужен ограничитель — ставь `fps_max` (~90–95% от рефреша монитора).
- **NVIDIA Reflex** — полезен для уменьшения input lag. В CPU-упоре прирост FPS не ждём; тестируй `Вкл` и `Вкл+усиление`.
- **Окно/Полный экран** — чаще стабильнее **Полный экран** (без оверлеев).
- **Оверлеи** (Steam, Discord, GeForce, браузер, кейс-сайты) — могут давать фризы при ALT-TAB/открытии TAB. Отключи для теста.
- **Ограничение FPS** — если при TAB/меню есть фриз, поставь `fps_max` ниже твоего «среднего» FPS на ~5–10%.
- **Планки ОЗУ** — двухканал (2×8, 2×16) почти всегда быстрее, чем одна планка того же объёма.
""")

# Кнопка скачать расширенную базу (с RAM Channel)
st.markdown("---")
st.markdown("**Нужна база с колонкой `RAM Channel`?** Сгенерируй и скачай для своего репозитория.")
if st.button("📦 Сформировать builds_with_ram_channel.csv"):
    df_aug = augment_with_ram_channel(df)
    csv_bytes = df_aug.to_csv(index=False).encode("utf-8-sig")
    st.download_button("💾 Скачать builds_with_ram_channel.csv",
                       data=csv_bytes, file_name="builds_with_ram_channel.csv", mime="text/csv")

# Донат-блок (ненавязчивый)
st.markdown("---")
st.markdown("""
<div class="donate-box">
  <b>Поддержи проект</b><br>
  Каждый, кто поддержит рублём — попадёт в следующий ролик (экран благодарностей).<br>
  <span class="small-note">Так мы сможем чаще обновлять базу и добавлять новые сборки.</span><br><br>
  👉 <a class="badge badge-yt" href="https://www.donationalerts.com/r/melevik" target="_blank">Поддержать</a>
</div>
""", unsafe_allow_html=True)

