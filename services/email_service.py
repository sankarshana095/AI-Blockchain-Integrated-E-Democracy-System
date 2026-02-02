# services/email_service.py

def send_otp_email(email, otp):
    # TODO: integrate real email (SMTP / SendGrid)
    print(f"[OTP EMAIL] Sent OTP {otp} to {email}")
