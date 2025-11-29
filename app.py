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


# ==========================================================
# FUNÇÃO PARA GERAR HORÁRIOS DE 2 EM 2 MINUTOS
# ==========================================================
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
        atual += timedelta(minutes=2)

    return horarios


# ==========================================================
# ROTA PRINCIPAL — CARREGA O FORMULÁRIO
# ==========================================================
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", horarios=[], mensagem=None)


# ==========================================================
# ROTA PARA VERIFICAR HORÁRIOS OCUPADOS
# ==========================================================
@app.route("/horarios_indisponiveis", methods=["POST"])
def horarios_indisponiveis():
    data = request.form.get("data")

    if not data:
        return jsonify({"ocupados": []})

    # Lê todas as linhas da planilha
    registros = sheet.get_all_records()

    ocupados = [
        r["horario"]
        for r in registros
        if str(r["data"]).strip() == data
    ]

    return jsonify({"ocupados": ocupados})


# ==========================================================
# RECEBER FORMULÁRIO DO SITE
# ==========================================================
@app.route("/enviar", methods=["POST"])
def enviar():
    data = request.form.get("data")
    horario = request.form.get("horario")
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

    return render_template("index.html", horarios=[], mensagem="Reserva enviada com sucesso!")


# ==========================================================
# EXECUÇÃO LOCAL
# ==========================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

