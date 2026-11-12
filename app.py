import numpy as np
import pandas as pd
import streamlit as st
from core.detonation import kamlet_jacobs, tnt_equivalent
from core.blast import sadovsky_dp_kpa
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import matplotlib.pyplot as plt

# Настройка страницы
st.set_page_config(page_title="deto-calc", page_icon="💥", layout="wide")
st.title("💥 Дето-Калькулятор: экспресс-оценка параметров взрыва")

# Загружаем базу данных
df = pd.read_csv("data/explosives.csv")
name = st.selectbox("Выберите взрывчатое вещество", df["name"])
row = df[df["name"] == name].iloc[0]

rho = st.slider("Плотность заряда, г/см³", 0.8, float(row["rho_max"]), float(row["rho_max"]))
mass = st.number_input("Масса заряда, кг", 0.1, 1000.0, 5.0)

D, P = kamlet_jacobs(rho, row["Q_cal_g"], row["N"], row["M"])
q = tnt_equivalent(mass, row["Q_cal_g"])

st.metric("Скорость детонации", f"{D:.2f} км/с", f"эксп.: {row['D_exp_km_s']} км/с")
st.metric("Давление Чепмена–Жуге", f"{P:.0f} кбар")
st.metric("Тротиловый эквивалент", f"{q:.1f} кг")
st.divider()

R = st.slider("Расстояние от центра взрыва, м", 1.0, 200.0, 20.0)
st.metric("Избыточное давление (ΔP) на расстоянии", f"{sadovsky_dp_kpa(R, q):.1f} кПа")

# Строим график в интерфейсе (ограничиваем максимальное значение по Y, чтобы график был красивым)
Rs = np.linspace(1, 200, 200)
dps = [sadovsky_dp_kpa(r, q) for r in Rs]
chart_data = pd.DataFrame({"Расстояние, м": Rs, "ΔP, кПа": dps})
st.line_chart(chart_data, x="Расстояние, м", y="ΔP, кПа")

if st.button("Экспорт отчёта в PDF"):
    # Ищем шрифт в папке с проектом (он будет работать и на сервере)
    try:
        pdfmetrics.registerFont(TTFont('Roboto', 'Roboto-Regular.ttf'))
        font_name = 'Roboto'
    except:
        font_name = 'Helvetica'

    # Строим график
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(Rs, dps, color='red', linewidth=2)
    ax.set_title("Зависимость избыточного давления от расстояния", fontname=font_name, fontsize=12)
    ax.set_xlabel("Расстояние, м", fontname=font_name, fontsize=10)
    ax.set_ylabel("Избыточное давление, кПа", fontname=font_name, fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)

    # Ограничиваем график, чтобы не было огромного пика при 100 кг (ставим лимит до 100 кПа)
    plt.ylim(0, max(100, min(1500, sadovsky_dp_kpa(1, q))))

    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    img_buf.seek(0)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont(font_name, 12)

    c.drawString(50, 800, f"ВВ: {name}, масса: {mass} кг, Плотность заряда: {rho} г/см³")
    c.drawString(50, 780, f"Скорость детонации: {D:.2f} км/с")
    c.drawString(50, 760, f"Давление Чепмена-Жуге: {P:.0f} кбар")
    c.drawString(50, 740, f"Тротиловый эквивалент: {q:.1f} кг")
    c.drawString(50, 720, f"Избыточное давление на расстоянии {R:.0f} м: {sadovsky_dp_kpa(R, q):.1f} кПа")

    c.drawImage(ImageReader(img_buf), 50, 350, width=500, height=250)

    c.save()
    st.download_button("Скачать PDF", buf.getvalue(), "report.pdf")