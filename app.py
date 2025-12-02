from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json

app = Flask(__name__)

# Autenticação Google Sheets
def get_sheet():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
    client = gspread.authorize(creds)

    # Abra sua planilha pelo nome
    sheet = client.open("reservas_papainoel").worksheet("Página1")
    return sheet

# Rota para salvar reserva
@app.route('/salvar', methods=['POST'])
def salvar():
    try:
        data = request.get_json()

        nome = data.get("nome")
        telefone = data.get("telefone")
        horario = data.get("horario")
        criado_em = datetime.now().strftime("%d/%m/%Y %H:%M")

        sheet = get_sheet()
        sheet.append_row([nome, telefone, horario, criado_em])

        return jsonify({"status": "ok", "mensagem": "Reserva salva com sucesso!"})

    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

# Rota para consultar reservas
@app.route('/consultar', methods=['GET'])
def consultar():
    try:
        sheet = get_sheet()
        registros = sheet.get_all_records()

        return jsonify(registros)

    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


@app.route('/', methods=['GET'])
def home():
    return "API do Sistema de Reservas Papai Noel funcionando!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

