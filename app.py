from flask import Flask, render_template, request, redirect, session
import pyotp
import datetime
from database import (
    create_db, add_user, get_user, get_user_by_email,
    update_attempts, lock_user, unlock_user, update_password,
    create_session, get_active_sessions, revoke_session, revoke_all_sessions,
    is_session_active, mark_totp_confirmed,
    save_reset_token, get_reset_token, mark_token_used,
    get_audit_logs
)
from security import (
    hash_password, check_password,
    verify_otp, log_event,
    generate_reset_token, send_reset_email,
    generate_qr_code,
    validate_and_sanitize, validate_otp_format, validate_reset_token_format
)

app = Flask(__name__)
app.secret_key = "supersecretkey"

create_db()

# --- Validate session on every request (enforces remote session revocation) ---
SKIP_SESSION_CHECK = {"/login", "/register", "/logout", "/forgot_password", "/", "/otp"}

@app.before_request
def check_session_validity():
    # Skip static files and public routes
    if request.path.startswith("/static") or request.path.startswith("/reset_password"):
        return
    if request.path in SKIP_SESSION_CHECK:
        return
    # If the user is logged in, verify their session is still active in DB
    sid = session.get("session_id")
    if sid is not None:
        if not is_session_active(sid):
            session.clear()
            return redirect("/login")


@app.route("/")
def home():
    return redirect("/login")


# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        email = request.form["email"].strip()

        # --- Input validation (overflow + trapdoor protection) ---
        val_err = validate_and_sanitize({
            "username": username,
            "email":    email,
            "password": password,
        })
        if val_err:
            error = val_err
        elif get_user(username):
            error = "Username already exists."
        elif get_user_by_email(email):
            error = "Email already registered."
        else:
            hashed = hash_password(password)
            otp_secret = pyotp.random_base32()
            add_user(username, hashed, email, otp_secret)
            log_event(f"New user registered: {username}")
            session["setup_username"] = username
            return redirect("/setup_2fa")

    return render_template("register.html", error=error)


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    remaining_time = None
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        # --- Input validation (overflow + trapdoor protection) ---
        val_err = validate_and_sanitize({
            "username": username,
            "password": password,
        })
        if val_err:
            error = val_err
            return render_template("login.html", error=error)

        user = get_user(username)

        if not user:
            error = "Invalid username or password."
        else:
            if user["locked"] == 1:
                locked_until_str = user.get("locked_until")
                if locked_until_str:
                    try:
                        dt_until = datetime.datetime.fromisoformat(locked_until_str.replace("Z", "+00:00"))
                        now_utc = datetime.datetime.now(datetime.timezone.utc)
                        if now_utc >= dt_until:
                            unlock_user(username)
                            user["locked"] = 0
                            user["attempts"] = 0
                        else:
                            remaining_time = int((dt_until - now_utc).total_seconds())
                            error = "Account blocked due to too many failed attempts."
                    except Exception:
                        unlock_user(username)
                        user["locked"] = 0
                        user["attempts"] = 0
                else:
                    unlock_user(username)
                    user["locked"] = 0
                    user["attempts"] = 0

            if user["locked"] == 0:
                if check_password(password, user["password"]):
                    if not user.get("totp_confirmed"):
                        session["setup_username"] = username
                        log_event(f"Password correct but 2FA not set up for {username}")
                        return redirect("/setup_2fa")

                    session["pending_username"] = username
                    session["otp_secret"] = user["otp_secret"]
                    log_event(f"Password correct for {username}")
                    return redirect("/otp")
                else:
                    attempts = user["attempts"] + 1
                    update_attempts(username, attempts)
                    if attempts >= 3:
                        lock_user(username)
                        error = "Account blocked due to too many failed attempts."
                        remaining_time = 180
                    else:
                        error = f"Invalid username or password. ({3 - attempts} attempts left)"
                    log_event(f"Failed login for {username}")

    return render_template("login.html", error=error, remaining=remaining_time)


# ================= OTP =================

@app.route("/otp", methods=["GET", "POST"])
def otp():
    if "pending_username" not in session:
        return redirect("/login")
    error = None
    if request.method == "POST":
        otp_input = request.form["otp"].strip()

        # --- OTP format validation (overflow + trapdoor protection) ---
        val_err = validate_otp_format(otp_input)
        if val_err:
            error = val_err
        else:
            secret = session.get("otp_secret")
            if verify_otp(secret, otp_input):
                username = session["pending_username"]
                ip = request.remote_addr
                browser = request.user_agent.string[:120]
                sid = create_session(username, ip, browser)
                session["session_id"] = sid
                session["username"] = username
                session.pop("pending_username", None)
                session.pop("otp_secret", None)
                log_event(f"OTP verified for {username} from {ip}")
                return redirect("/dashboard")
            else:
                error = "Invalid or expired code. Try again."
                log_event(f"Wrong OTP attempt for {session.get('pending_username')}")

    return render_template("otp.html", error=error)


# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/login")
    return render_template("dashboard.html", user=session["username"])


# ================= SESSION MANAGEMENT =================

@app.route("/sessions")
def sessions():
    if "username" not in session:
        return redirect("/login")
    active_sessions = get_active_sessions(session["username"])
    current_sid = session.get("session_id")
    return render_template("sessions.html", sessions=active_sessions, current_sid=current_sid)


@app.route("/sessions/revoke/<int:sid>")
def revoke(sid):
    if "username" not in session:
        return redirect("/login")
    revoke_session(sid, session["username"])
    log_event(f"Session {sid} revoked by {session['username']}")
    return redirect("/sessions")


@app.route("/sessions/revoke_all")
def revoke_all():
    if "username" not in session:
        return redirect("/login")
    revoke_all_sessions(session["username"])
    session.clear()
    return redirect("/login")


# ================= QR CODE / 2FA SETUP =================

@app.route("/setup_2fa", methods=["GET", "POST"])
def setup_2fa():
    username = session.get("setup_username") or session.get("username")
    if not username:
        return redirect("/login")
        
    user = get_user(username)
    if not user:
        return redirect("/login")
        
    error = None
    if request.method == "POST":
        otp_input = request.form.get("otp", "").strip()
        val_err = validate_otp_format(otp_input)
        if val_err:
            error = val_err
        elif verify_otp(user["otp_secret"], otp_input):
            mark_totp_confirmed(username)
            log_event(f"TOTP confirmed and set up for {username}")
            if "setup_username" in session:
                session.pop("setup_username", None)
                return redirect("/login")
            else:
                return redirect("/dashboard")
        else:
            error = "Invalid code. Try again."
            log_event(f"Failed TOTP setup attempt for {username}")

    qr_b64 = generate_qr_code(username, user["otp_secret"])
    secret = user["otp_secret"]
    return render_template("setup_2fa.html", qr_b64=qr_b64, secret=secret, error=error)


# ================= PASSWORD RESET =================

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    message = None
    error = None
    if request.method == "POST":
        email = request.form["email"].strip()

        # --- Input validation (overflow + trapdoor protection) ---
        val_err = validate_and_sanitize({"email": email})
        if val_err:
            error = val_err
            return render_template("forgot_password.html", message=None, error=error)

        user = get_user_by_email(email)
        if user:
            token = generate_reset_token()
            save_reset_token(user["username"], token)
            reset_link = f"{request.url_root}reset_password/{token}"
            send_reset_email(email, reset_link)
            log_event(f"Password reset requested for {user['username']}")
        message = "If that email exists, a reset link has been sent."
    return render_template("forgot_password.html", message=message, error=error)


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    # --- Validate the token format before any DB lookup ---
    token_err = validate_reset_token_format(token)
    if token_err:
        return render_template("reset_password.html", invalid=True)

    record = get_reset_token(token)
    error = None

    if not record:
        return render_template("reset_password.html", invalid=True)

    # Check 15 min expiry
    created = datetime.datetime.strptime(record["created_at"], "%Y-%m-%d %H:%M:%S")
    if (datetime.datetime.now() - created).seconds > 900:
        return render_template("reset_password.html", invalid=True)

    if request.method == "POST":
        new_password = request.form["password"]
        confirm = request.form["confirm"]

        # --- Input validation (overflow + trapdoor protection) ---
        val_err = validate_and_sanitize({"password": new_password})
        if val_err:
            error = val_err
        elif new_password != confirm:
            error = "Passwords do not match."
        elif len(new_password) < 6:
            error = "Password must be at least 6 characters."
        else:
            hashed = hash_password(new_password)
            update_password(record["username"], hashed)
            mark_token_used(token)
            log_event(f"Password reset successful for {record['username']}")
            return redirect("/login")

    return render_template("reset_password.html", token=token, invalid=False, error=error)


# ================= AUDIT LOG =================

@app.route("/audit_log")
def audit_log():
    if "username" not in session:
        return redirect("/login")
    
    db_logs = get_audit_logs()
    logs = []
    if db_logs:
        for row in db_logs:
            dt_str = row.get("created_at", "")
            try:
                # Parse Supabase UTC time and convert to IST (+5:30)
                dt_obj = datetime.datetime.strptime(dt_str[:19], "%Y-%m-%dT%H:%M:%S")
                dt_obj += datetime.timedelta(hours=5, minutes=30)
                dt = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                dt = dt_str.replace("T", " ")[:19]
            logs.append({"time": dt, "event": row.get("event", "Unknown Event")})
            
    return render_template("audit_log.html", logs=logs)


#  LOGOUT 

@app.route("/logout")
def logout():
    if "session_id" in session:
        revoke_session(session["session_id"], session.get("username"))
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True, port=5002)
