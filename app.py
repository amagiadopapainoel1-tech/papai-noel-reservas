import os
from flask import Flask, render_template, request, redirect, jsonify
from datetime import datetime, timedelta
import sqlite3
import smtplib
from email.message import EmailMessage

# ==========================
# CONFIGURAÇÃO DO FLASK
# ==========================
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# ==========================
# VARIÁVEIS DE AMBIENTE
# ==========================
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

NOME_REMETENTE = "Central de Distribuição de Presentes do Papai Noel 🎅"

QR_CODE_PATH = "static/KrCode pix Paulo.jpg"
NOEL_FOTO_PATH = "static/noel.png"


# ==========================
# BANCO DE DADOS
# ==========================
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

# ==========================
# GERAR HORÁRIOS
# ==========================
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


def horarios_ocupados():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT horario_real FROM agendamentos")
    dados = cursor.fetchall()

    conn.close()
    return {linha[0] for linha in dados}


def encontrar_horario_real(horario_desejado):
    ocupados = horarios_ocupados()

    h = datetime.strptime(horario_desejado, "%H:%M")
    base = datetime(2025, 12, 24, h.hour, h.minute)

    for hr in HORARIOS_REAIS:
        dt_hr = datetime.strptime(hr, "%d/%m/%Y %H:%M")

        if dt_hr >= base and hr not in ocupados:
            return hr

    return None


# ==========================
# ENVIO DE EMAIL
# ==========================
def enviar_email(destinatario, nome, horario_real, valor):
    msg = EmailMessage()
    msg["Subject"] = "Confirmação de Agendamento - Papai Noel 🎅"
    msg["From"] = f"{NOME_REMETENTE} <{EMAIL_REMETENTE}>"
    msg["To"] = destinatario

    corpo = f"""
Olá {nome}!

Sua visita do Papai Noel foi confirmada! 🎅✨

📅 **Horário confirmado:** {horario_real}  
💰 **Valor da entrega:** R$ {valor:.2f}

Finalize o pagamento via PIX para garantir sua reserva!

A magia do Natal agradece sua confiança ❤️🎄
"""

    msg.set_content(corpo)

    # anexos (opcional)
    for caminho in [QR_CODE_PATH, NOEL_FOTO_PATH]:
        if os.path.exists(caminho):
            with open(caminho, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="image",
                    subtype="jpeg" if caminho.endswith(".jpg") else "png",
                    filename=os.path.basename(caminho)
                )

    # envio
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_REMETENTE, EMAIL_PASSWORD)
        smtp.send_message(msg)


# ==========================
# ROTAS
# ==========================
@app.route("/")
def index():
    return render_template("index.html")


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

    if not horario_real:
        return "Não há horário disponível!", 400

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO agendamentos
        (nome, idade, data, horario_escolhido, horario_real, endereco, email, telefone, presente, valor, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (nome, idade, data, horario_escolhido, horario_real, endereco, email, telefone, presente, valor, "Pendente"))

    conn.commit()
    conn.close()

    enviar_email(email, nome, horario_real, valor)

    return redirect("/confirmado")


@app.route("/confirmado")
def confirmado():
    return "Agendamento confirmado! Verifique seu e-mail."


# ==========================
# INICIAR SERVIDOR
# ==========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
