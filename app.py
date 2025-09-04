
**🎛 Панель драйвера (NVIDIA/AMD):**  
{row.get('Control Panel','—')}

**🪟 Оптимизация Windows (по желанию):**  
{row.get('Windows Optimization','—')}

**📊 Ожидаемый FPS:** {row.get('FPS Estimate','—')}  
**🔗 Источник:** {row.get('Source','—')}
""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

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
        st.download_button("💾 Скачать профиль (.txt)", data=profile_txt, file_name="cs2_profile.txt")

        # Ремайндер про каналы памяти (без фильтров — просто полезная плашка)
        st.info("💡 Подсказка: переход с **1×** модуля ОЗУ на **2×** (двухканал) часто даёт заметный прирост FPS в CS2.")

        # =========================
        # ⚠️ ОПАСНЫЕ ГЛОБАЛЬНЫЕ ТУМБЛЕРЫ (AMD/NVIDIA)
        # =========================
        with st.expander("⚠️ Важно: не включайте агрессивные драйверные опции глобально"):
            st.markdown("""
**AMD (Radeon Software):**  
- **Anti-Lag / Anti-Lag+**, **Chill**, **Boost**, **Enhanced Sync**, **Radeon Super Resolution** — включайте в **профиле CS2**, не глобально.  
- Глобальные включения могут дать нестабильные частоты, фризы, микролаги или высокий idle-жор.

**NVIDIA (Панель управления):**  
- **Предпочтительный режим электропитания — «Максимальная производительность»** — только в **профиле CS2**, не глобально (иначе карта будет держать частоты на рабочем столе).  
- **Low Latency Mode (Низкая задержка)** — используйте в профиле игры, тестируйте **On**/**Ultra**; глобально не требуется.

✅ В целом: все «жёсткие» драйверные твики держите **на уровне профиля игры**, а не системы.
""")

# =========================
# 🔗 СОЦИАЛКИ (ОСТАВЬТЕ СВОЙ БЛОК КАК ЕСТЬ)
# =========================
# Примечание: по вашей просьбе НЕ меняю разметку и иконки соцсетей.
# Оставьте свой существующий блок соц-иконок в том месте, где он у вас уже стоит.

# =========================
# 💖 ПОДДЕРЖКА ПРОЕКТА (КАК БЫЛО, + мягкая пульсация)
# =========================
st.markdown("---")
st.subheader("💖 Поддержи проект")
st.markdown("👉 [💸 DonatPay](https://www.donationalerts.com/r/melevik)", unsafe_allow_html=True)
st.caption("Каждый, кто поддержит рублём — попадёт в титры следующего ролика ✨")
