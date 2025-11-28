from flask import Flask, request, jsonify, render_template
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

app = Flask(__name__)

# ================================
#   AUTENTICAÇÃO GOOGLE SHEETS
# ================================
google_credentials_json = os.getenv("GOOGLE_CREDENTIALS")

if not google_credentials_json:
    raise Exception("ERRO: Variável GOOGLE_CREDENTIALS não encontrada no Render!")

creds_dict = json.loads(google_credentials_json)

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

SHEET_ID = "10HFxgC2k_6VkFyUoTiPMg6h0aBUhUaESYg5knbapktM"
sheet = client.open_by_key(SHEET_ID).sheet1


# ================================
#   PÁGINA PRINCIPAL (FORMULÁRIO)
# ================================
@app.route("/", methods=["GET"])
def formulario():
    horarios = [
        "08:00", "08:30", "09:00", "09:30",
        "10:00", "10:30", "11:00", "11:30",
        "12:00", "13:00", "14:00", "15:00",
        "16:00", "17:00", "18:00", "19:00",
        "20:00", "21:00", "22:00"
    ]
    return render_template("index.html", horarios=horarios)


# ======================================
#   ROTA PARA RECEBER ENVIO DO FORMULÁRIO
# ======================================
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

        mensagem = "Reserva enviada com sucesso!"
        horarios = [
            "08:00", "08:30", "09:00", "09:30",
            "10:00", "10:30", "11:00", "11:30",
            "12:00", "13:00", "14:00", "15:00",
            "16:00", "17:00", "18:00", "19:00",
            "20:00", "21:00", "22:00"
        ]

        return render_template("index.html", mensagem=mensagem, horarios=horarios)

    except Exception as e:
        return f"ERRO ao enviar reserva: {str(e)}", 500


# ================================
#     TESTE DA API
# ================================
@app.route("/api", methods=["GET"])
def api_teste():
    return jsonify({"status": "online", "mensagem": "API funcionando"})


# ================================
#   EXECUÇÃO LOCAL / RENDER
# ================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
