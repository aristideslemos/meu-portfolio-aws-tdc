"""
contact_handler.py
Função Lambda que processa o formulário de contato e envia e-mail via SES.
"""

import json
import logging
import os
import re

import boto3
from botocore.exceptions import ClientError

# Configuração de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Cliente SES — reutilizado entre invocações (fora do handler)
ses = boto3.client("ses", region_name=os.environ.get("AWS_SES_REGION", "us-east-2"))

# Variáveis de ambiente (configuradas na função Lambda)
RECIPIENT_EMAIL = os.environ["RECIPIENT_EMAIL"]   # aristideslemos7245@gmail.com
SENDER_EMAIL = os.environ["SENDER_EMAIL"]         # mesmo e-mail verificado no SES
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")  # domínio do Amplify após deploy

# Limites de tamanho dos campos (defesa em profundidade)
MAX_NAME_LEN = 100
MAX_EMAIL_LEN = 200
MAX_MESSAGE_LEN = 2000

# Regex simples para validar e-mail
EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# Headers CORS reutilizados em todas as respostas
CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def response(status_code: int, message: str) -> dict:
    """Monta a resposta no formato esperado pelo API Gateway HTTP API."""
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps({"message": message}),
    }


def validate_fields(name: str, email: str, message: str) -> str | None:
    """
    Valida os campos do formulário.
    Retorna uma mensagem de erro ou None se tudo estiver válido.
    """
    if not name or not email or not message:
        return "Todos os campos são obrigatórios."

    if len(name) > MAX_NAME_LEN:
        return f"Nome deve ter no máximo {MAX_NAME_LEN} caracteres."

    if len(email) > MAX_EMAIL_LEN:
        return f"E-mail deve ter no máximo {MAX_EMAIL_LEN} caracteres."

    if not EMAIL_REGEX.match(email):
        return "E-mail inválido."

    if len(message) < 10:
        return "Mensagem deve ter pelo menos 10 caracteres."

    if len(message) > MAX_MESSAGE_LEN:
        return f"Mensagem deve ter no máximo {MAX_MESSAGE_LEN} caracteres."

    return None


def send_email(name: str, email: str, message: str) -> None:
    """Envia o e-mail via Amazon SES."""
    subject = f"[Portfolio] Nova mensagem de {name}"

    body_text = (
        f"Nova mensagem recebida pelo formulário de contato do portfolio.\n\n"
        f"Nome: {name}\n"
        f"E-mail: {email}\n\n"
        f"Mensagem:\n{message}\n"
    )

    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
      <h2 style="color: #ff9900; border-bottom: 2px solid #ff9900; padding-bottom: 8px;">
        Nova mensagem — Portfolio
      </h2>
      <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
        <tr>
          <td style="padding: 8px; font-weight: bold; width: 80px;">Nome:</td>
          <td style="padding: 8px;">{name}</td>
        </tr>
        <tr style="background: #f9f9f9;">
          <td style="padding: 8px; font-weight: bold;">E-mail:</td>
          <td style="padding: 8px;"><a href="mailto:{email}">{email}</a></td>
        </tr>
      </table>
      <h3 style="color: #555;">Mensagem:</h3>
      <p style="background: #f5f5f5; padding: 16px; border-radius: 6px; white-space: pre-wrap;">{message}</p>
      <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
      <p style="font-size: 12px; color: #999;">
        Enviado pelo formulário de contato do seu portfolio AWS.
      </p>
    </body>
    </html>
    """

    ses.send_email(
        Source=SENDER_EMAIL,
        Destination={"ToAddresses": [RECIPIENT_EMAIL]},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {
                "Text": {"Data": body_text, "Charset": "UTF-8"},
                "Html": {"Data": body_html, "Charset": "UTF-8"},
            },
        },
        ReplyToAddresses=[email],  # Ao responder, vai direto para quem enviou
    )


def lambda_handler(event: dict, context) -> dict:
    """Handler principal da função Lambda."""
    http_method = event.get("requestContext", {}).get("http", {}).get("method", "")

    # Preflight CORS — navegadores enviam OPTIONS antes do POST
    if http_method == "OPTIONS":
        return response(200, "OK")

    if http_method != "POST":
        return response(405, "Método não permitido.")

    # Parse do body
    try:
        body = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        logger.warning("Body inválido recebido.")
        return response(400, "Corpo da requisição inválido.")

    name = str(body.get("name", "")).strip()
    email = str(body.get("email", "")).strip().lower()
    message = str(body.get("message", "")).strip()

    # Validação dos campos
    error = validate_fields(name, email, message)
    if error:
        logger.info("Validação falhou: %s", error)
        return response(400, error)

    # Envio do e-mail
    try:
        send_email(name, email, message)
        logger.info("E-mail enviado com sucesso para %s.", RECIPIENT_EMAIL)
        return response(200, "Mensagem enviada com sucesso!")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        logger.error("Erro SES [%s]: %s", error_code, e.response["Error"]["Message"])

        if error_code == "MessageRejected":
            return response(400, "E-mail do remetente inválido ou não verificado.")
        if error_code in ("Throttling", "SendingPausedException"):
            return response(503, "Serviço temporariamente indisponível. Tente novamente.")

        return response(500, "Erro ao enviar mensagem. Tente novamente mais tarde.")
    except Exception as e:
        logger.exception("Erro inesperado: %s", str(e))
        return response(500, "Erro interno. Tente novamente mais tarde.")
