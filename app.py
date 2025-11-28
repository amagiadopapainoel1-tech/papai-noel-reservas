from flask import Flask, render_template, request
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

app = Flask(__name__)

# ============================================
#   1 — GOOGLE CREDENTIALS (Render)
# ============================================
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

# ============================================
#   2 — SUA PLANILHA
# ============================================
SHEET_ID = "10HFxgC2k_6VkFyUoTiPMg6h0aBUhUaESYg5knbapktM"
sheet = client.open_by_key(SHEET_ID).sheet1

# Horários disponíveis
HORARIOS = [
    "08:00", "09:00", "10:00", "11:00",
    "12:00", "13:00", "14:00", "15:00",
    "16:00", "17:00", "18:00", "19:00",
    "20:00", "21:00"
]

# ============================================
#   3 — ROTA PRINCIPAL (formulário)
# ============================================
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", horarios=HORARIOS)

# ============================================
#   4 — ROTA PARA RECEBER O FORMULÁRIO
# ============================================
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

        # Envia para a planilha
        sheet.append_row([
            data, horario, responsavel, numero_criancas, email, telefone,
            valor_total, status_pagamento, observacoes, endereco, bairro, cidade
        ])

        return render_template("index.html",
                               horarios=HORARIOS,
                               mensagem="Reserva registrada com sucesso!")
    except Exception as e:
        return render_template("index.html",
                               horarios=HORARIOS,
                               mensagem=f"Erro ao enviar: {str(e)}")

# ============================================
#   5 — EXECUÇÃO LOCAL
# ============================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
