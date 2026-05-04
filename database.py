import os
import datetime
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Get Supabase credentials from environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client if credentials are present
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("WARNING: SUPABASE_URL and SUPABASE_KEY not found in .env!")
    supabase = None

def create_db():
    # Tables are created manually in Supabase SQL Editor.
    # IMPORTANT: The 'users' table must have an integer column 'totp_confirmed' 
    # (default 0) to track 2FA onboarding status.
    pass

def get_user(username):
    if not supabase: return None
    res = supabase.table("users").select("*").eq("username", username).execute()
    return res.data[0] if res.data else None

def get_user_by_email(email):
    if not supabase: return None
    res = supabase.table("users").select("*").eq("email", email).execute()
    return res.data[0] if res.data else None

def add_user(username, password, email, otp_secret):
    if not supabase: return
    supabase.table("users").insert({
        "username": username,
        "password": password,
        "email": email,
        "otp_secret": otp_secret,
        "attempts": 0,
        "locked": 0,
        "totp_confirmed": 0
    }).execute()

def mark_totp_confirmed(username):
    if not supabase: return
    supabase.table("users").update({"totp_confirmed": 1}).eq("username", username).execute()

def update_attempts(username, attempts):
    if not supabase: return
    supabase.table("users").update({"attempts": attempts}).eq("username", username).execute()

def lock_user(username):
    if not supabase: return
    unlock_time = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=3)).isoformat()
    supabase.table("users").update({"locked": 1, "locked_until": unlock_time}).eq("username", username).execute()

def unlock_user(username):
    if not supabase: return
    supabase.table("users").update({"locked": 0, "attempts": 0, "locked_until": None}).eq("username", username).execute()

def update_password(username, new_hashed):
    if not supabase: return
    supabase.table("users").update({
        "password": new_hashed,
        "attempts": 0,
        "locked": 0,
        "locked_until": None
    }).eq("username", username).execute()

# Sessions
def create_session(username, ip, browser):
    if not supabase: return None
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    res = supabase.table("sessions").insert({
        "username": username,
        "ip": ip,
        "browser": browser,
        "login_time": now,
        "active": 1
    }).execute()
    return res.data[0]["id"] if res.data else None

def get_active_sessions(username):
    if not supabase: return []
    res = supabase.table("sessions").select("*").eq("username", username).eq("active", 1).order("login_time", desc=True).execute()
    return res.data

def is_session_active(session_id):
    """Check if a session is still active (not revoked) in the database."""
    if not supabase or not session_id:
        return False
    res = supabase.table("sessions").select("active").eq("id", session_id).execute()
    if res.data and res.data[0]["active"] == 1:
        return True
    return False

def revoke_session(session_id, username):
    if not supabase: return
    supabase.table("sessions").update({"active": 0}).eq("id", session_id).eq("username", username).execute()

def revoke_all_sessions(username):
    if not supabase: return
    supabase.table("sessions").update({"active": 0}).eq("username", username).execute()

# Reset Tokens
def save_reset_token(username, token):
    if not supabase: return
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    supabase.table("reset_tokens").insert({
        "username": username,
        "token": token,
        "created_at": now,
        "used": 0
    }).execute()

def get_reset_token(token):
    if not supabase: return None
    res = supabase.table("reset_tokens").select("*").eq("token", token).eq("used", 0).execute()
    return res.data[0] if res.data else None

def mark_token_used(token):
    if not supabase: return
    supabase.table("reset_tokens").update({"used": 1}).eq("token", token).execute()

# Audit Logs
def log_audit_event(message):
    if not supabase: return
    supabase.table("audit_logs").insert({
        "event": message
    }).execute()

def get_audit_logs():
    if not supabase: return []
    res = supabase.table("audit_logs").select("*").order("created_at", desc=True).limit(200).execute()
    return res.data
