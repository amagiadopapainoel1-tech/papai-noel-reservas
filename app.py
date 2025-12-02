from flask import Flask, render_template, request, redirect, send_file
import sqlite3
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
import os
import json
from openpyxl import Workbook, load_workbook
from dotenv import load_dotenv

# ------------------------------------------------
# 🔧 CONFIGURA AMBIENTE (.env ou Variáveis Render)
# ------------------------------------------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# ------------------------------------------------
# 📧 CONFIGURAÇÕES DO EMAIL
# ------------------------------------------------
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
NOME_REMETENTE = "Central de Distribuição de Presentes do Papai Noel"

# anexos
QR_CODE_PATH = "static/KrCode pix Paulo.jpg"
NOEL_FOTO_PATH = "static/noel.png"

# ------------------------------------------------
# 🔰 CONFIG GOOGLE (caso use planilhas Google)
# ------------------------------------------------
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

if GOOGLE_CREDENTIALS:
    GOOGLE_CREDENTIALS = json.loads(GOOGLE_CREDENTIALS)

# ------------------------------------------------
# 🗄️ CRIA TABELA LOCAL
# ------------------------------------------------
def criar_tabela():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            idade TEXT,
            data TEXT,
            horario_escolhido TEXT,
            horario_real TEXT,
            endereco TEXT,
            email TEXT,
            telefone TEXT,
            presente TEXT,
            valor REAL,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

criar_tabela()

# ------------------------------------------------
# ⏰ GERAR HORÁRIOS DE 2 EM 2 MINUTOS
# ------------------------------------------------
def gerar_horarios_reais():
    inicio = datetime(2025, 12, 24, 14, 0)
    fim = datetime(2025, 12, 25, 11, 0)
    horarios = []
    atual = inicio
    while atual <= fim:
        horarios.append(atual.strftime("%d/%m/%Y %H:%M"))
        atual += timedelta(minutes=2)
    return horarios

HORARIOS_REAIS = gerar_horarios_reais()

# ------------------------------------------------
# ⛔ VERIFICAR HORÁRIOS JÁ OCUPADOS
# ------------------------------------------------
def horarios_ocupados():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT horario_real FROM agendamentos")
    dados = cursor.fetchall()
    conn.close()
    return {linha[0] for linha in dados}

# ------------------------------------------------
# 🔍 SELECIONAR O HORÁRIO REAL DISPONÍVEL
# ------------------------------------------------
def encontrar_horario_real(horario_desejado):
    ocupados = horarios_ocupados()
    h = datetime.strptime(horario_desejado, "%H:%M")
    base = datetime(2025, 12, 24, h.hour, h.minute)

    for hr in HORARIOS_REAIS:
        dt_hr = datetime.strptime(hr, "%d/%m/%Y %H:%M")
        if dt_hr >= base and hr not in ocupados:
            return hr
    return None

# ------------------------------------------------
# ✉️ ENVIAR EMAIL
# ------------------------------------------------
def enviar_email(destinatario, nome, horario_real, valor):
    msg = EmailMessage()
    msg["Subject"] = "Confirmação de Agendamento - Papai Noel 🎅"
    msg["From"] = f"{NOME_REMETENTE} <{EMAIL_REMETENTE}>"
    msg["To"] = destinatario

    corpo = f"""
Olá {nome}!

🎅 Seu agendamento foi confirmado!

📅 **Horário:** {horario_real}  
💰 **Valor da entrega:** R$ {valor:.2f}

Formas de pagamento no anexo.

A Magia do Natal começa agora! ✨
"""

    msg.set_content(corpo)

    # anexos
    if os.path.exists(QR_CODE_PATH):
        with open(QR_CODE_PATH, "rb") as f:
            msg.add_attachment(f.read(),
                maintype="image", subtype="jpeg",
                filename="qrcode_pix.jpg")

    if os.path.exists(NOEL_FOTO_PATH):
        with open(NOEL_FOTO_PATH, "rb") as f:
            msg.add_attachment(f.read(),
                maintype="image", subtype="png",
                filename="papai_noel.png")

    # envia
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_REMETENTE, EMAIL_PASSWORD)
        smtp.send_message(msg)

# ------------------------------------------------
# 🏠 ROTA PRINCIPAL
# ------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

# ------------------------------------------------
# 📝 ROTA DO FORMULÁRIO
# ------------------------------------------------
@app.route("/agendar", methods=["POST"])
def agendar():
    nome = request.form["nome"]
    idade = request.form["idade"]
    data = request.form["data"]
    horario_escolhido = request.form["horario"]
    endereco = request.form["endereco"]
    email = request.form["email"]
    telefone = request.form["telefone"]
    presente = request.form["presente"]
    valor = float(request.form["valor"])

    horario_real = encontrar_horario_real(horario_escolhido)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO agendamentos (
            nome, idade, data, horario_escolhido, horario_real,
            endereco, email, telefone, presente, valor, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (nome, idade, data, horario_escolhido, horario_real,
          endereco, email, telefone, presente, valor, "PENDENTE"))
    conn.commit()
    conn.close()

    enviar_email(email, nome, horario_real, valor)

    return render_template("confirmacao.html", nome=nome, horario=horario_real)

# ------------------------------------------------
# ▶️ RODAR LOCAL
# ------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
