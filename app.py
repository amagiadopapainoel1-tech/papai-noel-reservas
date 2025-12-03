import os
from flask import Flask, render_template, request, redirect, jsonify
from datetime import datetime, timedelta
import sqlite3
import smtplib
from email.message import EmailMessage

# ==========================
# CONFIG DO FLASK
# ==========================
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "segredo123")

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
            data TEXT,
            horario TEXT,
            responsavel TEXT,
            numero_criancas INTEGER,
            email TEXT,
            telefone TEXT,
            valor_total REAL,
            status_pagamento TEXT,
            observacoes TEXT,
            endereco TEXT,
            bairro TEXT,
            cidade TEXT
        )
    """)
    conn.commit()
    conn.close()

criar_tabela()

# ==========================
# GERAR HORÁRIOS
# ==========================
def gerar_horarios(data):
    if data == "2024-12-24":
        inicio = datetime(2024, 12, 24, 14, 0)
        fim = datetime(2024, 12, 24, 23, 59)
    elif data == "2024-12-25":
        inicio = datetime(2024, 12, 25, 0, 0)
        fim = datetime(2024, 12, 25, 11, 0)
    else:
        return []

    horarios = []
    atual = inicio
    while atual <= fim:
        horarios.append(atual.strftime("%H:%M"))
        atual += timedelta(minutes=10)

    return horarios


def horarios_ocupados(data):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT horario FROM agendamentos WHERE data = ?", (data,))
    dados = cursor.fetchall()
    conn.close()
    return {linha[0] for linha in dados}


# ==========================
# ROTA AJAX – HORÁRIOS
# ==========================
@app.route("/horarios_indisponiveis", methods=["POST"])
def horarios_indisponiveis():
    data = request.form.get("data")
    if not data:
        return jsonify({"erro": "data não enviada"})

    todos = gerar_horarios(data)
    ocupados = horarios_ocupados(data)

    return jsonify({
        "horarios_disponiveis": todos,
        "ocupados": list(ocupados)
    })

# ==========================
# ENVIO DE EMAIL
# ==========================
def enviar_email(destinatario, responsavel, data, horario, valor_total):
    msg = EmailMessage()
    msg["Subject"] = "Confirmação de Reserva - Papai Noel 🎅"
    msg["From"] = f"{NOME_REMETENTE} <{EMAIL_REMETENTE}>"
    msg["To"] = destinatario

    corpo = f"""
Olá {responsavel}!

Sua reserva com o Papai Noel foi confirmada! 🎅✨

📅 Data: {data}  
⏰ Horário: {horario}  
👧👦 Crianças atendidas  
💰 Valor total: R$ {valor_total:.2f}

Finalize o pagamento via PIX para garantir sua visita 🎄
    """

    msg.set_content(corpo)

    # anexos
    for caminho in [QR_CODE_PATH, NOEL_FOTO_PATH]:
        if os.path.exists(caminho):
            with open(caminho, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="image",
                    subtype="jpeg" if caminho.endswith(".jpg") else "png",
                    filename=os.path.basename(caminho)
                )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_REMETENTE, EMAIL_PASSWORD)
        smtp.send_message(msg)

# ==========================
# ROTAS PRINCIPAIS
# ==========================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/enviar", methods=["POST"])
def enviar():
    data = request.form["data"]
    horario = request.form["horario"]
    responsavel = request.form["responsavel"]
    numero_criancas = int(request.form["numero_criancas"])
    email = request.form["email"]
    telefone = request.form.get("telefone", "")
    observacoes = request.form.get("observacoes", "")
    endereco = request.form.get("endereco", "")
    bairro = request.form.get("bairro", "")
    cidade = request.form.get("cidade", "")
    status_pagamento = "Pendente"

    valor_total = numero_criancas * 50

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO agendamentos
        (data, horario, responsavel, numero_criancas, email, telefone, valor_total,
         status_pagamento, observacoes, endereco, bairro, cidade)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data, horario, responsavel, numero_criancas, email, telefone,
        valor_total, status_pagamento, observacoes, endereco, bairro, cidade
    ))

    conn.commit()
    conn.close()

    # envia o e-mail
    enviar_email(email, responsavel, data, horario, valor_total)

    return redirect("/confirmado")


@app.route("/confirmado")
def confirmado():
    return "<h2>Reserva confirmada! Verifique seu e-mail 🎅✨</h2>"

# ==========================
# INICIAR SERVIDOR
# ==========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

