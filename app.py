import os
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import pandas as pd  # usado apenas na rota que salva/consulta planilha

app = Flask(__name__)

# ---------------------------
# CONFIG VIA VARIÁVEIS DE AMBIENTE (RENDER)
# ---------------------------
EMAIL_USER = os.environ.get("EMAIL_USER")               # ex: amagiadopapainoel1@gmail.com
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")       # App Password do Gmail
EMAIL_SMTP = os.environ.get("EMAIL_SMTP", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
SENDER_NAME = os.environ.get("SENDER_NAME", "Central de Distribuição de Presentes do Papai Noel")

# Paths (usando app.root_path para caminho absoluto no servidor)
QR_CODE_REL = os.path.join("static", "KrCode pix Paulo.jpg")
NOEL_IMG_REL = os.path.join("static", "papai_noel.png")
PLANILHA = os.path.join("templates", "Agenda_Papai_Noel_Atualizada.xlsx")

# Horários reais
INICIO = datetime(2024, 12, 24, 14, 0)
FIM = datetime(2024, 12, 25, 11, 0)
INTERVALO_MIN = 2


# ---------------------------
# UTIL: gerar horários reais (gera datetimes)
# ---------------------------
def gerar_horarios_reais():
    atual = INICIO
    result = []
    delta = timedelta(minutes=INTERVALO_MIN)
    while atual <= FIM:
        result.append(atual)
        atual += delta
    return result


HORARIOS_REAIS = gerar_horarios_reais()


# ---------------------------
# UTIL: carregar agendamentos (somente quando necessário)
# ---------------------------
def carregar_agendamentos_planilha():
    # tenta ler planilha se existir, senão cria DataFrame vazio com colunas esperadas
    try:
        df = pd.read_excel(PLANILHA)
        return df
    except Exception:
        cols = ["horario_real", "nome_crianca", "responsavel", "email", "valor", "status"]
        return pd.DataFrame(columns=cols)


def salvar_agendamento_planilha(linha_dict):
    df = carregar_agendamentos_planilha()
    df = df.append(linha_dict, ignore_index=True)
    df.to_excel(PLANILHA, index=False)


# ---------------------------
# UTIL: encontrar próximo horário livre (posterior ou igual)
# ---------------------------
def horarios_ocupados_set():
    df = carregar_agendamentos_planilha()
    # armazenamos horários em mesmo formato dd/mm/YYYY HH:MM utilizado no e-mail/planilha
    return set(df["horario_real"].astype(str).tolist()) if not df.empty else set()


def encontrar_horario_real_posterior(horario_desejado_dt):
    ocupados = horarios_ocupados_set()
    for hr in HORARIOS_REAIS:
        if hr >= horario_desejado_dt:
            hr_str = hr.strftime("%d/%m/%Y %H:%M")
            if hr_str not in ocupados:
                return hr, hr_str
    return None, None


# ---------------------------
# FUNÇÃO: enviar email HTML com imagens inline (QR + Noel)
# ---------------------------
def enviar_email_confirmacao(destinatario, dados, horario_final_dt, horario_final_str):
    if not EMAIL_USER or not EMAIL_PASSWORD:
        # Falha segura: não tentar enviar se variáveis de ambiente não estiverem configuradas
        app.logger.error("E-mail não enviado: variáveis EMAIL_USER/EMAIL_PASSWORD ausentes.")
        return False

    msg = MIMEMultipart("related")
    msg["Subject"] = "🎅 Confirmação de Agendamento — Central de Distribuição de Presentes do Papai Noel"
    msg["From"] = f"{SENDER_NAME} <{EMAIL_USER}>"
    msg["To"] = destinatario

    PIX_COPIA_COLA = (
        "00020126360014br.gov.bcb.pix0114+55419975658825204000053039865802BR5912PAULO_DUARTE"
        "6008Curitiba610981550-bc1qruqmcx20vwhv5dav2hlr4yg9n20kqz0fescezh"
    )

    horario_formatado = horario_final_dt.strftime("%d/%m/%Y %H:%M")

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background:#f7f7f7; padding:20px;">
      <div style="max-width:650px;margin:auto;background:#fff;padding:20px;border-radius:8px;">
        <h2 style="color:#b30000; text-align:center;">Central de Distribuição de Presentes do Papai Noel</h2>

        <p>Olá <strong>{dados['responsavel']}</strong>,</p>

        <p>Recebemos sua solicitação. Seguem os dados confirmados:</p>
        <p><strong>Criança:</strong> {dados['nome_crianca']}<br>
           <strong>Horário solicitado:</strong> {dados['horario_solicitado_str']}<br>
           <strong>Horário confirmado pelo sistema:</strong> <span style="color:#b30000;"><strong>{horario_formatado}</strong></span><br>
           <strong>Valor:</strong> R$ {float(dados['valor']):.2f}
        </p>

        <hr>
        <h3 style="color:#b30000;">Instruções de Pagamento</h3>
        <p><strong>1) PIX - Copia e Cola</strong></p>
        <div style="background:#eee;padding:12px;border-radius:6px;word-break:break-all;">
            <code style="font-family:monospace;">{PIX_COPIA_COLA}</code>
        </div>

        <p><strong>2) PIX - QR Code</strong></p>
        <div style="text-align:center;">
          <img src='cid:qrcode' style='width:260px;border-radius:8px;border:2px solid #ddd;'/>
        </div>

        <hr>
        <p>Após o pagamento, envie o comprovante para:</p>
        <p><strong>E-mail:</strong> amagiadopapainoel1@gmail.com<br>
           <strong>WhatsApp:</strong> (41) 99756-5882
        </p>

        <p>Ao enviar o comprovante, por favor informe:</p>
        <ul>
          <li>Nome da criança</li>
          <li>Descrição do presente</li>
        </ul>

        <p style="text-align:center;margin-top:18px;">
          <img src='cid:noel' style='width:160px;'><br>
          <strong>Papai Noel — Paulo Duarte</strong>
        </p>
      </div>
    </body>
    </html>
    """

    msg_html = MIMEText(html, "html")
    msg.attach(msg_html)

    # anexar imagens inline (usando caminhos relativos dentro de app.root_path)
    qr_path = os.path.join(app.root_path, QR_CODE_REL)
    noel_path = os.path.join(app.root_path, NOEL_IMG_REL)

    try:
        with open(qr_path, "rb") as f:
            img = MIMEImage(f.read())
            img.add_header("Content-ID", "<qrcode>")
            img.add_header("Content-Disposition", "inline")
            msg.attach(img)
    except FileNotFoundError:
        app.logger.warning(f"QR code não encontrado em: {qr_path}")

    try:
        with open(noel_path, "rb") as f:
            img2 = MIMEImage(f.read())
            img2.add_header("Content-ID", "<noel>")
            img2.add_header("Content-Disposition", "inline")
            msg.attach(img2)
    except FileNotFoundError:
        app.logger.warning(f"Imagem do Noel não encontrada em: {noel_path}")

    # Envio SMTP
    try:
        server = smtplib.SMTP(EMAIL_SMTP, EMAIL_PORT, timeout=60)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        app.logger.error(f"Erro ao enviar email: {e}")
        return False


# ---------------------------
# ROTA: formulário (index)
# ---------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Campos esperados no seu form — adapte nomes conforme seu template
        nome_crianca = request.form.get("nome_crianca", "").strip()
        responsavel = request.form.get("responsavel", "").strip()
        email = request.form.get("email", "").strip()
        horario_solicitado = request.form.get("horario")  # ex: "2024-12-24 18:30" ou formato que seu form usa
        valor = request.form.get("valor", "0").replace(",", ".")
        try:
            valor = float(valor)
        except:
            valor = 0.0

        # parse do horário solicitado para datetime (ajuste format se necessário)
        try:
            horario_dt = datetime.strptime(horario_solicitado, "%Y-%m-%d %H:%M")
            horario_solicitado_str = horario_dt.strftime("%d/%m/%Y %H:%M")
        except Exception:
            # fallback: tentar outro formato dd/mm/YYYY HH:MM
            horario_dt = datetime.strptime(horario_solicitado, "%d/%m/%Y %H:%M")
            horario_solicitado_str = horario_solicitado

        # encontra horário real (posterior ou igual)
        horario_real_dt, horario_real_str = encontrar_horario_real_posterior(horario_dt)
        if horario_real_dt is None:
            return "Agenda cheia para o período escolhido. Entre em contato."

        # salvar na planilha (linha)
        linha = {
            "horario_real": horario_real_str,
            "nome_crianca": nome_crianca,
            "responsavel": responsavel,
            "email": email,
            "valor": valor,
            "status": "Pendente"
        }
        salvar_agendamento_planilha(linha)

        # enviar e-mail de confirmação
        dados = {
            "nome_crianca": nome_crianca,
            "responsavel": responsavel,
            "email": email,
            "valor": valor,
            "horario_solicitado_str": horario_solicitado_str
        }
        enviar_email_confirmacao(email, dados, horario_real_dt, horario_real_str)

        return redirect(url_for("sucesso"))

    # GET — renderiza seu formulário (index.html)
    # NÃO carregamos planilha pesada aqui para evitar timeout no boot/deploy
    return render_template("index.html")


@app.route("/sucesso")
def sucesso():
    return "Agendamento realizado com sucesso! Verifique seu e-mail."


# ---------------------------
# ROTA: painel administrativo simples (lista e marca como pago)
# ---------------------------
@app.route("/admin")
def admin():
    # carrega planilha e renderiza uma página simples (templates/admin.html)
    df = carregar_agendamentos_planilha()
    # passa para o template como lista de dicts
    ags = df.to_dict(orient="records")
    return render_template("admin.html", agendamentos=ags)


@app.route("/admin/marcar_pago", methods=["POST"])
def admin_marcar_pago():
    horario_real = request.form.get("horario_real")
    email = request.form.get("email")
    df = carregar_agendamentos_planilha()
    # localizar linha por horario_real + email (ajuste chave se preferir id)
    mask = (df["horario_real"].astype(str) == horario_real) & (df["email"].astype(str) == email)
    if mask.any():
        df.loc[mask, "status"] = "Pago"
        df.to_excel(PLANILHA, index=False)
        return redirect(url_for("admin"))
    return "Registro não encontrado", 404


# ---------------------------
# RODAR SERVIDOR (apenas local dev)
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)


