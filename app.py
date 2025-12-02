from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
import os

app = Flask(__name__)

# ---------------------------
# CONFIGURAÇÕES DO EMAIL
# ---------------------------
EMAIL_REMETENTE = "amagiadopapainoel1@gmail.com"
SENHA_EMAIL = os.getenv("EMAIL_PASSWORD")  # ← LIDO DO RENDER
NOME_REMETENTE = "Central de Distribuição de Presentes do Papai Noel"

QR_CODE_PATH = "static/KrCode pix Paulo.jpg"
NOEL_FOTO_PATH = "static/noel.png"


# ---------------------------
# CRIAÇÃO DA TABELA
# ---------------------------
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


# ---------------------------
# GERAR HORÁRIOS REAIS (2 em 2 minutos)
# ---------------------------
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


# ---------------------------
# BUSCAR HORÁRIOS OCUPADOS
# ---------------------------
def horarios_ocupados():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT horario_real FROM agendamentos")
    dados = cursor.fetchall()

    conn.close()
    return {h[0] for h in dados}


# ---------------------------
# ENCONTRAR HORÁRIO REAL DISPONÍVEL
# ---------------------------
def encontrar_horario_real(horario_desejado):
    ocupados = horarios_ocupados()

    h = datetime.strptime(horario_desejado, "%H:%M")
    base = datetime(2025, 12, 24, h.hour, h.minute)

    for hr in HORARIOS_REAIS:
        dt = datetime.strptime(hr, "%d/%m/%Y %H:%M")
        if dt >= base and hr not in ocupados:
            return hr

    return None


# ---------------------------
# ENVIO DO EMAIL
# ---------------------------
def enviar_email(destinatario, nome, horario_real, valor):
    msg = EmailMessage()

    msg["Subject"] = "Confirmação de Agendamento - Papai Noel 🎅"
    msg["From"] = f"{NOME_REMETENTE} <{EMAIL_REMETENTE}>"
    msg["To"] = destinatario

    corpo = f"""
Olá {nome}!

Seu agendamento foi **confirmado** pela Central de Distribuição de Presentes do Papai Noel 🎅

---------------------------------------
📅 **Horário confirmado:** {horario_real}
💰 **Valor da entrega:** R$ {valor:.2f}
---------------------------------------

### 🔻 Formas de Pagamento
Você pode concluir o pagamento usando as opções abaixo:

1️⃣ **PIX copia e cola**  
2️⃣ **PIX QR Code** (anexo)

Agradecemos por ajudar o Papai Noel a levar magia para tantas crianças! 🎁✨
"""

    msg.set_content(corpo)

    # anexar QR Code
    try:
        with open(QR_CODE_PATH, "rb") as f:
            msg.add_attachment(f.read(), maintype="image", subtype="jpeg", filename="qrcode-pagamento.jpg")
    except:
        pass

    # anexar foto do Papai Noel
    try:
        with open(NOEL_FOTO_PATH, "rb") as f:
            msg.add_attachment(f.read(), maintype="image", subtype="png", filename="noel.png")
    except:
        pass

    # Enviar
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_REMETENTE, SENHA_EMAIL)
        smtp.send_message(msg)


# ---------------------------
# ROTA PRINCIPAL (FORMULÁRIO)
# ---------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------
# ROTA DE AGENDAMENTO
# ---------------------------
@app.route("/agendar", methods=["POST"])
def agendar():
    nome = request.form["nome"]
    idade = request.form["idade"]
    endereco = request.form["endereco"]
    email = request.form["email"]
    telefone = request.form["telefone"]
    presente = request.form["presente"]
    valor = float(request.form["valor"])
    horario_desejado = request.form["horario"]

    horario_real = encontrar_horario_real(horario_desejado)

    if not horario_real:
        return "Não foi possível encontrar um horário disponível.", 400

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO agendamentos
        (nome, idade, data, horario_escolhido, horario_real, endereco, email, telefone, presente, valor, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        nome,
        idade,
        "2025",
        horario_desejado,
        horario_real,
        endereco,
        email,
        telefone,
        presente,
        valor,
        "confirmado"
    ))

    conn.commit()
    conn.close()

    enviar_email(email, nome, horario_real, valor)

    return redirect("/sucesso")


# ---------------------------
# ROTA DE SUCESSO
# ---------------------------
@app.route("/sucesso")
def sucesso():
    return render_template("sucesso.html")


# ---------------------------
# INICIAR APP
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

