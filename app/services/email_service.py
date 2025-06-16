# app/services/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

# Configuration SMTP (à remplacer par vos propres informations)
SMTP_SERVER = "sandbox.smtp.mailtrap.io" # Ex: smtp.gmail.com pour Gmail
SMTP_PORT = 2525 # 587 pour TLS, 465 pour SSL
SMTP_USERNAME = "9cd2e4844e1210" # Votre adresse email
SMTP_PASSWORD = "1050693059b1c1" # Votre mot de passe d'application (pour Gmail) ou mot de passe réel
# Looking to send emails in production? Check out our Email API/SMTP product!

def send_email(to_email: str, subject: str, body: str, html_body: Optional[str] = None):
    """
    Envoie un email via SMTP.
    """
    if not all([SMTP_USERNAME, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT]):
        print("Erreur: Configuration SMTP incomplète. Impossible d'envoyer l'email.")
        return False

    msg = MIMEMultipart("alternative")
    msg['From'] = SMTP_USERNAME
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))
    if html_body:
        msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Activer TLS
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, to_email, msg.as_string())
        print(f"Email envoyé avec succès à {to_email}")
        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email à {to_email}: {e}")
        return False