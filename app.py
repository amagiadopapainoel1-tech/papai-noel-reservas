from flask import Flask, render_template, request, jsonify
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# ====== AUTENTICAÇÃO GOOGLE VIA VARIÁVEL DO RENDER ======
google_credentials_json = os.getenv("GOOGLE_CREDENTIALS")
if not google_credentials_json:
    raise Exception("ERRO: A variável GOOGLE_CREDENTIALS não está definida no Render!")

creds_dict = json.loads(google_credentials_json)

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# === SUA PLANILHA ===
SHEET_ID = "10HFxgC2k_6VkFyUoTiPMg6h0aBUhUaESYg5knbapktM"
sheet = client.open_by_key(SHEET_ID).sheet1


# ===== GERAR HORÁRIOS DE 2 EM 2 MINUTOS =====
def gerar_horarios():
    horarios = []

    # 24/12 – das 14:00 até 23:59
    inicio_24 = datetime(2025, 12, 24, 14, 0)
    fim_24 = datetime(2025, 12, 24, 23, 59)

    atual = inicio_24
    while atual <= fim_24:
        horarios.append(atual.strftime("%H:%M"))
        atual += timedelta(minutes=2)

    # 25/12 – das 00:00 até 11:00
    inicio_25 = datetime(2025, 12, 25, 0, 0)
    fim_25 = datetime(2025, 12, 25, 11, 0)

    atual = inicio_25
    while atual <= fim_25:
        horarios.append(atual.strftime("%H:%M"))
        atual += timedelta(minutes=2)

    return horarios


# LISTA COMPLETA DE HORÁRIOS
TODOS_HORARIOS = gerar_horarios()


# ===== ABRIR FORMULÁRIO =====
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", horarios=TODOS_HORARIOS, mensagem=None)


# ===== RETORNAR HORÁRIOS OCUPADOS PARA O FRONT =====
@app.route("/horarios_indisponiveis", methods=["POST"])
def horarios_indisponiveis():
    data = request.form.get("data")

    if not data:
        return jsonify({"ocupados": []})

    registros = sheet.get_all_records()

    ocupados = []
    for row in registros:
        if str(row["data"]) == data:
            ocupados.append(row["horario"])

    return jsonify({"ocupados": ocupados})


# ===== RECEBER FORMULÁRIO DO SITE =====
@app.route("/enviar", methods=["POST"])
def enviar():

    data = request.form.get("data")
    horario = request.form.get("horario")

    # 🔒 Segurança: bloquear tentativa de agendar horário já ocupado
    registros = sheet.get_all_records()
    for row in registros:
        if str(row["data"]) == data and str(row["horario"]) == horario:
            return render_template(
                "index.html",
                horarios=TODOS_HORARIOS,
                mensagem=f"⚠ O horário {horario} para {data} já foi reservado!"
            )

    # Coleta dos dados restantes
    responsavel = request.form.get("responsavel")
    numero_criancas = request.form.get("numero_criancas")
    email = request.form.get("email")
    telefone = request.form.get("telefone")
    valor_total = request.form.get("valor_total")
    status_pagamento = request.form.get("status_pagamento")
    observacoes = request.form.get("observacoes")
    endereco = request.form.get("endereco")
    bairro = request.form.get("bairro")
    cidade = request.form.get("cidade")

    # gravação na planilha
    sheet.append_row([
        data, horario, responsavel, numero_criancas, email, telefone,
        valor_total, status_pagamento, observacoes, endereco, bairro, cidade
    ])

    mensagem = "🎅 Reserva enviada com sucesso!"

    return render_template("index.html", horarios=TODOS_HORARIOS, mensagem=mensagem)


# ===== EXECUÇÃO LOCAL =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
