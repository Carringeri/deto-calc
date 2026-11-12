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
import matplotlib
import matplotlib.pyplot as plt
import plotly.express as px

# --- НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(page_title="DETO-CALC", page_icon="⚙️", layout="wide", initial_sidebar_state="collapsed")

# --- КАСТОМНЫЕ СТИЛИ (CSS) ---
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1, h2, h3 { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600; color: #1E293B; }
    .stButton>button { width: 100%; border-radius: 4px; height: 3em; background-color: #0F172A; color: white; font-weight: 600; }
    .stButton>button:hover { background-color: #334155; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- ШАПКА САЙТА ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.markdown("<h1 style='color: #0F172A; margin: 0;'>DETO-CALC</h1>", unsafe_allow_html=True)
with col_title:
    st.markdown(
        "<p style='text-align: right; color: #64748B; margin-top: 15px; font-size: 14px;'>Инженерный калькулятор физики взрыва</p>",
        unsafe_allow_html=True)

st.markdown("---")

# --- ЗАГРУЗКА ДАННЫХ ---
df = pd.read_csv("data/explosives.csv")

# --- ВВОД ДАННЫХ ---
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Параметры заряда")
    name = st.selectbox("Взрывчатое вещество", df["name"])
    row = df[df["name"] == name].iloc[0]
    mass = st.number_input("Масса заряда, кг", 0.1, 1000.0, 5.0, step=1.0)

with col2:
    st.markdown("#### Условия среды")
    rho = st.slider("Плотность заряда, г/см³", 0.8, float(row["rho_max"]), float(row["rho_max"]))
    R = st.slider("Расстояние от центра, м", 1.0, 200.0, 20.0, step=1.0)

# --- РАСЧЕТЫ ---
D, P = kamlet_jacobs(rho, row["Q_cal_g"], row["N"], row["M"])
q = tnt_equivalent(mass, row["Q_cal_g"])
dp_at_R = sadovsky_dp_kpa(R, q)

st.markdown("---")

# --- ВЫВОД РЕЗУЛЬТАТОВ ---
st.markdown("#### Результаты расчета")
res_col1, res_col2, res_col3, res_col4 = st.columns(4)


def custom_metric(title, value, unit=""):
    st.markdown(f"""
        <div style="background-color: #F8FAFC; padding: 15px; border-radius: 8px; border: 1px solid #E2E8F0; border-left: 4px solid #0F172A; border-left-width: 4px;">
            <p style="margin: 0; font-size: 12px; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">{title}</p>
            <p style="margin: 5px 0 0 0; font-size: 24px; font-weight: 600; color: #0F172A;">{value} <span style="font-size: 14px; color: #64748B; font-weight: 400;">{unit}</span></p>
        </div>
    """, unsafe_allow_html=True)


with res_col1:
    custom_metric("Скорость детонации", f"{D:.2f}", "км/с")
with res_col2:
    custom_metric("Давление Ч-Ж", f"{P:.0f}", "кбар")
with res_col3:
    custom_metric("Тротиловый эквивалент", f"{q:.1f}", "кг")
with res_col4:
    custom_metric("ΔP на расстоянии", f"{dp_at_R:.1f}", "кПа")

st.markdown("<br>", unsafe_allow_html=True)

# --- ГРАФИК ---
Rs = np.linspace(1, 200, 200)
dps = [sadovsky_dp_kpa(r, q) for r in Rs]
chart_data = pd.DataFrame({"Расстояние, м": Rs, "ΔP, кПа": dps})

fig = px.line(chart_data, x="Расстояние, м", y="ΔP, кПа", log_y=True)
fig.update_layout(
    title=dict(text="Зависимость избыточного давления от расстояния", font=dict(size=16, color="#1E293B")),
    plot_bgcolor="white",
    paper_bgcolor="white",
    xaxis=dict(showgrid=True, gridcolor='#E2E8F0', title="Расстояние, м", linecolor='#CBD5E1'),
    yaxis=dict(showgrid=True, gridcolor='#E2E8F0', title="Избыточное давление, кПа (лог. шкала)", linecolor='#CBD5E1'),
    margin=dict(l=40, r=40, t=50, b=40),
    height=400
)
fig.update_traces(line_color='#0F172A', line_width=2)

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
st.markdown("<br>", unsafe_allow_html=True)

# --- БЛОК ЭКСПОРТА PDF ---
if st.button("Сформировать инженерный отчет (PDF)"):
    try:
        font_path = matplotlib.get_data_path() + '/fonts/ttf/DejaVuSans.ttf'
        pdfmetrics.registerFont(TTFont('DejaVu', font_path))
        font_name = 'DejaVu'
    except:
        font_name = 'Helvetica'

    fig_pdf, ax = plt.subplots(figsize=(8, 4))
    ax.plot(Rs, dps, color='#0F172A', linewidth=2)
    ax.set_title("Зависимость избыточного давления от расстояния", fontname=font_name, fontsize=12)
    ax.set_xlabel("Расстояние, м", fontname=font_name, fontsize=10)
    ax.set_ylabel("Избыточное давление, кПа", fontname=font_name, fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.6)

    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig_pdf)
    img_buf.seek(0)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # --- ШАПКА PDF (СЕРАЯ) ---
    c.setFillColorRGB(0.35, 0.35, 0.35)  # Серый цвет
    c.rect(0, height - 80, width, 80, fill=1, stroke=0)

    c.setFillColorRGB(1, 1, 1)  # Белый текст
    c.setFont(font_name, 22)
    c.drawString(40, height - 50, "Отчет: Экспресс-оценка параметров взрыва")
    c.setFont(font_name, 10)
    c.drawString(40, height - 70, "Сгенерировано программой DETO-CALC")

    # Данные
    c.setFillColorRGB(0, 0, 0)
    c.setFont(font_name, 12)
    c.drawString(40, height - 130, "1. ИСХОДНЫЕ ДАННЫЕ:")
    c.drawString(50, height - 155, f"• Взрывчатое вещество: {name}")
    c.drawString(50, height - 175, f"• Масса заряда: {mass} кг")
    c.drawString(50, height - 195, f"• Плотность заряда: {rho:.2f} г/см³")

    c.drawString(40, height - 240, "2. РЕЗУЛЬТАТЫ РАСЧЕТА:")
    c.drawString(50, height - 265, f"• Скорость детонации: {D:.2f} км/с")
    c.drawString(50, height - 285, f"• Давление Ч-Ж: {P:.0f} кбар")
    c.drawString(50, height - 305, f"• Тротиловый эквивалент: {q:.1f} кг")

    # --- РАМКА ГЛАВНОГО РЕЗУЛЬТАТА (ТЕМНО-СЕРАЯ) ---
    c.setStrokeColorRGB(0.25, 0.25, 0.25)
    c.setLineWidth(2)
    c.rect(40, height - 380, 510, 45, fill=0, stroke=1)
    c.setFont(font_name, 14)
    c.drawString(50, height - 365, f"Избыточное давление на R = {R:.0f} м: {dp_at_R:.1f} кПа")

    # График
    c.setFont(font_name, 12)
    c.drawString(40, height - 430, "3. ГРАФИЧЕСКАЯ ЗАВИСИМОСТЬ:")
    c.drawImage(ImageReader(img_buf), 50, height - 750, width=500, height=280)

    # Подвал
    c.setFont(font_name, 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(40, 30, "Документ сформирован автоматически.")
    c.drawString(40, 15, "DETO-CALC © 2024. Все расчеты носят оценочный характер.")
    c.save()

    st.download_button(label="⬇️ Скачать отчет", data=buf.getvalue(), file_name="deto-calc-report.pdf",
                       mime="application/pdf")