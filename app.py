from flask import Flask, request, render_template, jsonify
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

app = Flask(__name__)


# ====== AUTENTICAÇÃO GOOGLE VIA VARIÁVEL DO RENDER ======
google_credentials_json = os.getenv("GOOGLE_CREDENTIALS")

if not google_credentials_json:
    raise Exception("ERRO: A variável de ambiente GOOGLE_CREDENTIALS não está definida no Render!")

creds_dict = json.loads(google_credentials_json)

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)


# ====== PLANILHA ======
SHEET_ID = "10HFxgC2k_6VkFyUoTiPMg6h0aBUhUaESYg5knbapktM"
sheet = client.open_by_key(SHEET_ID).sheet1


# ====== RENDERIZAR FORMULÁRIO NO "/" ======
@app.route("/", methods=["GET"])
def index():
    horarios = [
        "09:00", "09:30", "10:00", "10:30",
        "11:00", "11:30", "12:00", "12:30",
        "13:00", "13:30", "14:00", "14:30",
        "15:00", "15:30", "16:00", "16:30",
        "17:00", "17:30", "18:00", "18:30",
        "19:00", "19:30", "20:00"
    ]
    return render_template("index.html", horarios=horarios, mensagem=None)


# ====== RECEBER FORMULÁRIO DO SITE ======
@app.route("/enviar", methods=["POST"])
def enviar():
    try:
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

        sheet.append_row([
            data, horario, responsavel, numero_criancas,
            email, telefone, valor_total, status_pagamento,
            observacoes, endereco, bairro, cidade
        ])

        horarios = [
            "09:00", "09:30", "10:00", "10:30",
            "11:00", "11:30", "12:00", "12:30",
            "13:00", "13:30", "14:00", "14:30",
            "15:00", "15:30", "16:00", "16:30",
            "17:00", "17:30", "18:00", "18:30",
            "19:00", "19:30", "20:00"
        ]

        return render_template("index.html", horarios=horarios,
                               mensagem="Reserva enviada com sucesso!")

    except Exception as e:
        return f"Erro ao enviar reserva: {str(e)}"


# ====== API PARA O BOT DO WHATSAPP ======
@app.route("/reserva", methods=["POST"])
def receber_reserva():
    data = request.json

    nome = data.get("nome")
    telefone = data.get("telefone")
    data_reserva = data.get("data")
    horario = data.get("horario")
    pacote = data.get("pacote")

    if not nome or not telefone:
        return jsonify({"erro": "Nome e telefone são obrigatórios"}), 400

    sheet.append_row([nome, telefone, data_reserva, horario, pacote])

    return jsonify({"status": "OK", "mensagem": "Reserva registrada com sucesso!"})


# ====== EXECUÇÃO LOCAL ======
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
