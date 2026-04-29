import bcrypt
import pyotp
import logging
import os
import re
import smtplib
import secrets
import io
import base64
import threading
import qrcode
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Use a NAMED logger so Supabase/HTTP library logs don't pollute auth.log
auth_logger = logging.getLogger("secureauth")
auth_logger.setLevel(logging.INFO)
_file_handler = logging.FileHandler(f"{LOG_DIR}/auth.log")
_file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
auth_logger.addHandler(_file_handler)
auth_logger.propagate = False  # don't send to root logger


# ================================================================
# INPUT LENGTH LIMITS  (simulate buffer-overflow protection)
# ================================================================

INPUT_LIMITS = {
    "username":  32,
    "email":     120,
    "password":  128,
    "otp":       6,
    "token":     64,     # reset-token URL param
}

# ================================================================
# SUSPICIOUS PATTERN DETECTION  (trapdoor / backdoor protection)
# ================================================================

# Compiled once at import time for performance
_SUSPICIOUS_PATTERNS = [
    # Null bytes
    re.compile(r"\x00"),
    # SQL injection fragments
    re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|EXEC|EXECUTE)\b"
               r"|\b(OR|AND)\s+[\'\"]?\d+[\'\"]?\s*=\s*[\'\"]?\d+)",
               re.IGNORECASE),
    # Classic 1=1 / 'OR 1=1-- patterns
    re.compile(r"['\"]?\s*(OR|AND)\s+['\"]?1['\"]?\s*=\s*['\"]?1", re.IGNORECASE),
    # Comment-based SQL injection
    re.compile(r"(--|/\*|\*/|;--)", re.IGNORECASE),
    # Script / XSS tags
    re.compile(r"<\s*script", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on(load|error|click|mouseover)\s*=", re.IGNORECASE),
    # Path traversal
    re.compile(r"\.\./|\.\.\\"),
    # Control characters  (ASCII 0-8, 14-31 except \t \n \r)
    re.compile(r"[\x01-\x08\x0e-\x1f]"),
    # Shell injection characters
    re.compile(r"[`|;&$]"),
]


def _contains_suspicious_patterns(value):
    """Return the name of the first matched threat category, or None."""
    checks = [
        (r"\x00",                                 "null-byte injection"),
        (_SUSPICIOUS_PATTERNS[1],                  "SQL-injection keywords"),
        (_SUSPICIOUS_PATTERNS[2],                  "SQL tautology (1=1)"),
        (_SUSPICIOUS_PATTERNS[3],                  "SQL comment injection"),
        (_SUSPICIOUS_PATTERNS[4],                  "XSS script tag"),
        (_SUSPICIOUS_PATTERNS[5],                  "javascript: URI"),
        (_SUSPICIOUS_PATTERNS[6],                  "XSS event handler"),
        (_SUSPICIOUS_PATTERNS[7],                  "path traversal"),
        (_SUSPICIOUS_PATTERNS[8],                  "control character"),
        (_SUSPICIOUS_PATTERNS[9],                  "shell metacharacter"),
    ]
    for pattern, label in checks:
        if isinstance(pattern, str):
            if pattern in value:
                return label
        else:
            if pattern.search(value):
                return label
    return None


# ================================================================
# PUBLIC VALIDATION API  (called from app.py routes)
# ================================================================

def validate_input_length(value, field_name):
    """Check value length against INPUT_LIMITS.

    Returns an error string if the limit is exceeded, else None.
    """
    limit = INPUT_LIMITS.get(field_name)
    if limit is None:
        return None
    if len(value) > limit:
        log_event(
            f"[BLOCKED] Potential overflow-style input blocked | "
            f"field={field_name} | length={len(value)} | limit={limit}"
        )
        return (
            f"⚠ Buffer Overflow Protection: {field_name.capitalize()} exceeds "
            f"maximum allowed length of {limit} characters (received {len(value)}). "
            f"Input rejected."
        )
    return None


def validate_suspicious(value, field_name):
    """Screen a single value for trapdoor / backdoor patterns.

    Returns an error string if suspicious, else None.
    """
    threat = _contains_suspicious_patterns(value)
    if threat:
        # Truncate for safe logging (don't echo the full payload)
        safe_preview = value[:40].encode("unicode_escape").decode("ascii")
        log_event(
            f"[BLOCKED] Suspicious/trapdoor-style input blocked | "
            f"field={field_name} | threat={threat} | preview={safe_preview}"
        )
        return (
            f"⚠ Backdoor/Trapdoor Protection: Suspicious pattern detected "
            f"in {field_name}. Input rejected for security."
        )
    return None


def validate_and_sanitize(fields):
    """Validate a dict of {field_name: value} pairs.

    Runs length checks AND suspicious-pattern checks on every field.
    Returns the first error message encountered, or None if all clean.
    """
    for field_name, value in fields.items():
        if value is None:
            continue
        # --- length check (buffer-overflow simulation) ---
        err = validate_input_length(value, field_name)
        if err:
            return err
        # --- suspicious-pattern check (trapdoor/backdoor simulation) ---
        err = validate_suspicious(value, field_name)
        if err:
            return err
    return None


def validate_otp_format(otp_value):
    """OTP must be exactly 6 digits.  Returns error string or None."""
    if not re.fullmatch(r"\d{6}", otp_value):
        log_event(
            f"[BLOCKED] Malformed OTP input | "
            f"length={len(otp_value)} | preview={otp_value[:20]}"
        )
        return "OTP must be exactly 6 digits."
    return None


def validate_reset_token_format(token_value):
    """Reset tokens are base64url strings ≤ 64 chars.  Returns error or None."""
    if len(token_value) > INPUT_LIMITS["token"]:
        log_event(
            f"[BLOCKED] Oversized reset token | length={len(token_value)}"
        )
        return "Invalid reset link."
    if not re.fullmatch(r"[A-Za-z0-9_\-]+", token_value):
        log_event(
            f"[BLOCKED] Malformed reset token | preview={token_value[:30]}"
        )
        return "Invalid reset link."
    return None


# ================================================================
# ORIGINAL HELPER FUNCTIONS  (unchanged)
# ================================================================

SMTP_TIMEOUT = 10  # seconds – fail fast instead of blocking the worker


def _send_email_otp_sync(to_email, otp):
    """Synchronous OTP email sender (called in a background thread)."""
    try:
        msg = MIMEText(f"Your OTP is: {otp}\n\nThis code expires in 30 seconds.")
        msg["Subject"] = "Your Secure Login OTP"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=SMTP_TIMEOUT) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        log_event(f"OTP email sent to {to_email}")
    except Exception as e:
        log_event(f"OTP email FAILED for {to_email}: {e}")


def send_email_otp(to_email, otp):
    """Send OTP email in a background thread so the request doesn't block."""
    thread = threading.Thread(target=_send_email_otp_sync, args=(to_email, otp), daemon=True)
    thread.start()


def _send_reset_email_sync(to_email, reset_link):
    """Synchronous reset email sender (called in a background thread)."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Password Reset - SecureAuth"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        body = f"""Hello,

You requested a password reset for your SecureAuth account.

Click the link below to reset your password:
{reset_link}

This link is valid for 15 minutes. If you did not request this, ignore this email.

- SecureAuth System
"""
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=SMTP_TIMEOUT) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        log_event(f"Reset email sent to {to_email}")
    except Exception as e:
        log_event(f"Reset email FAILED for {to_email}: {e}")


def send_reset_email(to_email, reset_link):
    """Send reset email in a background thread so the request doesn't block."""
    thread = threading.Thread(target=_send_reset_email_sync, args=(to_email, reset_link), daemon=True)
    thread.start()


def hash_password(password):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hashed.decode()


def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())


def generate_otp(secret):
    totp = pyotp.TOTP(secret)
    return totp.now()


def verify_otp(secret, otp):
    totp = pyotp.TOTP(secret)
    return totp.verify(otp, valid_window=1)


def generate_reset_token():
    return secrets.token_urlsafe(32)


def generate_qr_code(username, secret):
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=username, issuer_name="SecureAuth")
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    return encoded


def log_event(message):
    auth_logger.info(message)
