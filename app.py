from flask import Flask, render_template, request
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime, timedelta

app = Flask(__name__)

# -------------------------------
# CONFIGURAÇÕES DO SISTEMA
# -------------------------------
EMAIL_SENDER = "amagiadopapainoel1@gmail.com"
EMAIL_PASSWORD = "taniameuamor"
EMAIL_SMTP = "smtp.gmail.com"
EMAIL_PORT = 587

PLANILHA = "Agenda_Papai_Noel_Atualizada.xlsx"
QR_CODE_PATH = "static/KrCode pix Paulo.jpg"
NOEL_PATH = "static/papai_noel.png"

PIX_COPIA_COLA = (
    "00020126360014br.gov.bcb.pix0114+55419975658825204000053039865802BR5912PAULO_DUARTE"
    "6008Curitiba610981550-bc1qruqmcx20vwhv5dav2hlr4yg9n20kqz0fescezh"
)

INICIO = datetime(2024, 12, 24, 14, 0)
FIM = datetime(2024, 12, 25, 11, 0)
INTERVALO_REAL = timedelta(minutes=2)


# ------------------------------------
# FUNÇÃO: gerar todos os horários reais
# ------------------------------------
def gerar_horarios_reais():
    h = []
    atual = INICIO
    while atual <= FIM:
        h.append(atual)
        atual += INTERVALO_REAL
    return h


horarios_reais = gerar_horarios_reais()


# -------------------------------
# FUNÇÃO: carregar planilha
# -------------------------------
def carregar_agendamentos():
    try:
        df = pd.read_excel(PLANILHA)
        return df
    except:
        return pd.DataFrame(columns=["horario", "nome_crianca", "responsavel", "email", "valor"])


# -------------------------------
# FUNÇÃO: encontrar próximo horário real
# -------------------------------
def encontrar_horario_real(ideal):
    for h in horarios_reais:
        if h >= ideal:
            return h
    return None


# -------------------------------
# FUNÇÃO: enviar e-mail HTML com imagens inline
# -------------------------------
def enviar_email_confirmacao(destinatario, dados, horario_final):
    msg = MIMEMultipart("related")
    msg["Subject"] = "🎅 Confirmação de Agendamento — Central de Distribuição de Presentes do Papai Noel"
    msg["From"] = EMAIL_SENDER
    msg["To"] = destinatario

    # HTML DO EMAIL
    html = f"""
    <html>
    <body style="font-family: Arial; background: #f7f7f7; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 10px;">

            <h2 style="color: red;">🎅 Central de Distribuição de Presentes do Papai Noel</h2>

            <p>Olá, <b>{dados['responsavel']}</b>!</p>

            <p>
                Seu agendamento foi recebido com sucesso!  
                Aqui estão os detalhes confirmados:
            </p>

            <p><b>Criança:</b> {dados['nome_crianca']}</p>
            <p><b>Horário Escolhido:</b> {dados['horario_str']}</p>
            <p><b>Horário Final Real:</b> {horario_final.strftime("%d/%m %H:%M")}</p>
            <p><b>Valor:</b> R$ {dados['valor']}</p>

            <hr>

            <h3 style="color: green;">💰 Instruções de Pagamento</h3>

            <p>Você pode pagar usando o PIX <b>copia e cola</b> abaixo:</p>

            <p style="background: #eee; padding: 10px; word-break: break-all;">
                {PIX_COPIA_COLA}
            </p>

            <p>Ou escanear o QR Code abaixo:</p>

            <img src="cid:qrcode" style="width: 260px; border: 2px solid #ddd; border-radius: 10px;">

            <hr>

            <h3>📩 Após pagamento</h3>
            <p>
                Envie o comprovante para nosso e-mail ou WhatsApp  
                <b>(41) 99756‑5882</b><br>
                Informe o nome da criança e descreva o presente para personalizarmos a entrega.  
                <br><br>
                — <b>Papai Noel Paulo Duarte</b>
            </p>

            <hr>

            <img src="cid:noel" style="width: 180px; margin-top: 20px;">
        </div>
    </body>
    </html>
    """

    msg_html = MIMEText(html, "html")
    msg.attach(msg_html)

    # Anexar QR code inline
    with open(QR_CODE_PATH, "rb") as f:
        img = MIMEImage(f.read())
        img.add_header("Content-ID", "<qrcode>")
        msg.attach(img)

    # Anexar foto do papai noel inline
    with open(NOEL_PATH, "rb") as f:
        img2 = MIMEImage(f.read())
        img2.add_header("Content-ID", "<noel>")
        msg.attach(img2)

    # Enviar
    server = smtplib.SMTP(EMAIL_SMTP, EMAIL_PORT)
    server.starttls()
    server.login(EMAIL_SENDER, EMAIL_PASSWORD)
    server.sendmail(EMAIL_SENDER, destinatario, msg.as_string())
    server.quit()


# -------------------------------
# ROTA PRINCIPAL
# -------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nome_crianca = request.form["nome_crianca"]
        responsavel = request.form["responsavel"]
        email = request.form["email"]
        valor = request.form["valor"]
        horario_str = request.form["horario"]

        # Horário escolhido pelo usuário
        ideal = datetime.strptime(horario_str, "%Y-%m-%d %H:%M")

        # Encontrar horário real disponível
        horario_final = encontrar_horario_real(ideal)

        # Salvar na planilha
        df = carregar_agendamentos()
        df.loc[len(df)] = [horario_final, nome_crianca, responsavel, email, valor]
        df.to_excel(PLANILHA, index=False)

        # Enviar e-mail
        dados = {
            "nome_crianca": nome_crianca,
            "responsavel": responsavel,
            "email": email,
            "valor": valor,
            "horario_str": horario_str
        }

        enviar_email_confirmacao(email, dados, horario_final)

        return "Agendamento realizado! Verifique seu e-mail."

    return render_template("index.html")


# -------------------------------
# INICIAR SERVIDOR
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)

