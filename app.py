import matplotlib.pyplot as plt
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import numpy as np
import pandas as pd
import streamlit as st
from core.detonation import kamlet_jacobs, tnt_equivalent
from core.blast import sadovsky_dp_kpa

st.title("deto-calc: экспресс-оценка параметров взрыва")

df = pd.read_csv("data/explosives.csv")
name = st.selectbox("ВВ", df["name"])
row = df[df["name"] == name].iloc[0]

rho = st.slider("Плотность заряда, г/см³", 0.8, float(row["rho_max"]), float(row["rho_max"]))
mass = st.number_input("Масса заряда, кг", 0.1, 1000.0, 5.0)

D, P = kamlet_jacobs(rho, row["Q_cal_g"], row["N"], row["M"])
q = tnt_equivalent(mass, row["Q_cal_g"])

st.metric("Скорость детонации", f"{D:.2f} км/с", f"эксп.: {row['D_exp_km_s']} км/с")
st.metric("Давление Чепмена–Жуге", f"{P:.0f} кбар")
st.metric("Тротиловый эквивалент", f"{q:.1f} кг")

R = st.slider("Расстояние от центра, м", 1.0, 200.0, 20.0)
st.metric("ΔP на расстоянии", f"{sadovsky_dp_kpa(R, q):.1f} кПа")

Rs = np.linspace(1, 200, 200)
st.line_chart(pd.DataFrame({"R, м": Rs, "ΔP, кПа": [sadovsky_dp_kpa(r, q) for r in Rs]}), x="R, м", y="ΔP, кПа")

import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

if st.button("Экспорт отчёта в PDF"):
    # 1. Регистрируем шрифт Arial для поддержки кириллицы
    try:
        pdfmetrics.registerFont(TTFont('Arial', 'C:\\Windows\\Fonts\\arial.ttf'))
        font_name = 'Arial'
    except:
        font_name = 'Helvetica'

    # 2. Строим график в matplotlib
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(Rs, [sadovsky_dp_kpa(r, q) for r in Rs], color='red', linewidth=2)
    ax.set_title("Зависимость избыточного давления от расстояния", fontname=font_name, fontsize=12)
    ax.set_xlabel("Расстояние, м", fontname=font_name, fontsize=10)
    ax.set_ylabel("Избыточное давление, кПа", fontname=font_name, fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)

    # Сохраняем график в картинку в памяти
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)  # Закрываем фигуру, чтобы не висела в памяти
    img_buf.seek(0)

    # 3. Создаем PDF
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont(font_name, 12)

    # Выводим текст (левый верхний угол)
    c.drawString(50, 800, f"ВВ: {name}, масса: {mass} кг, Плотность заряда: {rho} г/см³")
    c.drawString(50, 780, f"Скорость детонации: {D:.2f} км/с")
    c.drawString(50, 760, f"Давление Чепмена-Жуге: {P:.0f} кбар")
    c.drawString(50, 740, f"Тротиловый эквивалент: {q:.1f} кг")
    c.drawString(50, 720, f"Избыточное давление на расстоянии {R:.0f} м: {sadovsky_dp_kpa(R, q):.1f} кПа")

    # 4. Вставляем график в PDF (под текстом)
    # Координаты (50, 300) - отступ слева, отступ снизу. Размеры: 500x250.
    c.drawImage(ImageReader(img_buf), 50, 350, width=500, height=250)

    c.save()
    st.download_button("Скачать PDF", buf.getvalue(), "report.pdf")