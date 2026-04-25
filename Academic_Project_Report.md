# Secure Authentication Module for Operating Systems
**Complete Project Report**

## 1. Project Overview
**Goals and Objectives**
The primary goal of this project is to construct a "Secure Authentication Module" capable of integrating with host or simulated operating system layers to enforce robust access control. Grounded in the concepts of Pluggable Authentication Modules (PAM) and defense-in-depth, this project seeks to prevent unauthorized access while mitigating profound memory-level exploits like buffer overflows and logical flaws like trapdoors.

**Scope**
The scope of this project encompasses the design and implementation of a modular authentication stack. This includes:
- A primary credential verification component employing modern cryptographic hashing (bcrypt).
- A Multi-Factor Authentication (MFA) validation layer using Time-based One-Time Passwords (TOTP).
- Security controls preventing common system exploits—focusing on strict input sanitization, safe memory handling (via high-level language constraints and validation), and auditing to identify backdoor or trapdoor attempts.

**Expected Outcomes**
- A demonstrable and interactive secure authentication gateway.
- Comprehensive enforcement of MFA, bridging standard passwords with out-of-band verification.
- A resilient security model that explicitly logs all activities to trace unauthorized trapdoor access, and drops malformed, excessively long inputs before evaluation to prevent memory exhaustion architectures.

## 2. Module-Wise Breakdown
The architecture is decoupled into **EXACTLY THREE** major modules to ensure maintainability and separation of privileges.

### A. Authentication Core Module
**Role:** Handles all raw credential verification, session token generation, and the Multi-Factor Authentication pipeline.
**Architecture & Interaction:** This module acts as the "PAM module" equivalent. It interacts downwards with the local database or user registry. 

### B. Security Layer Module
**Role:** Inspects incoming payloads, maintains cryptographic hygiene, and mitigates attack vectors before they reach the core.
**Architecture & Interaction:** Operates globally as a middleware. It analyzes input buffers, strictly enforcing size and type constraints. It governs rate-limiting and verifies the integrity of hashes, eliminating any anomalies potentially injected via rootkits or trapdoors.

### C. User Interface & API Layer Module
**Role:** Facilitates the interaction between the system user/client and the kernel/backend security logic.
**Architecture & Interaction:** Renders the frontend forms, API gateways, and handles standard HTTP/IPC interactions. It converts user inputs into sanitized streams to be passed to the Security Layer. 

## 3. Functionalities
### Authentication Core Features
- **Secure Password Hashing:** Uses `bcrypt` with dynamic salting, mitigating rainbow table attacks.
- **MFA Flow (TOTP):** Upon correct password, requires a time-based code derived from `pyotp` and an authenticator app (QR Code generation included).

### Security Layer Features
- **Buffer Overflow Prevention:** Rejects inputs exceeding predefined maximum bounds (e.g., rejecting strings over 128 bytes natively before any string parsing or memory allocation at the database level).
- **Trapdoor/Backdoor Prevention:** All authentication attempts (successful or failed) are logged in real-time (`logging.info`). No undocumented "hardcoded" admin accounts can bypass the `check_password` functions. 

### User Interface / API Layer Features
- **Login Flow Control:** Standardized `POST` login endpoints. Throttles consecutive failed requests.
- **Account Reset via Secure Token:** One-time cryptographically secure reset URL sent out-of-band (via SMTP).

## 4. Technology Used
- **Programming Language:** Python (Justification: Provides memory-safe string handling to natively mitigate traditional C-level buffer overflows, while providing rapid integration with modern crypto libraries. Serves as a perfect high-level interface for OS tools).
- **Libraries & Security Tools:** 
  - `bcrypt`: For mathematical heavy-lifting during hashing, effectively deterring brute-force.
  - `pyotp` / `qrcode`: For RFC 6238 compliant TOTP MFA logic.
  - `Flask` / `logging`: For API delivery and persistent authentication event auditing.
  - *Conceptual equivalents:* Python's `secrets` module replicates `OpenSSL` pseudo-random generation, and the architecture mirrors Linux `PAM`.
- **Other Tools:** GitHub (revision control), SQLite (file-based user persistence mimicking `/etc/shadow`), Environment Variables (`dotenv`).

## 5. Flow Diagram
```text
[ User / System Process ] 
       | (Initiates Auth Request: Username + Password)
       V
+---------------------------------------+
| 1. API Layer (Receives Input)         |
+---------------------------------------+
       | (Payload)
       V
+---------------------------------------+
| 2. Security Layer (Sanitization)      |
|    - String Length Check <= 128 chars | --> [Drop & Log if Overflow Attempt]
|    - SQL Injection / Type checking    |
+---------------------------------------+
       | (Clean Payload)
       V
+---------------------------------------+
| 3. Authentication Core Module         |
|    a. Fetch user hash from DB         |
|    b. `bcrypt.checkpw` evaluation      | --> [Fail? Log & Disconnect]
+---------------------------------------+
       | (Password Match)
       V
+---------------------------------------+
| 4. Multi-Factor Auth Prompt (TOTP)    |
|    - User inputs 6-digit PIN          |
|    - `pyotp.verify()` sequence          |
+---------------------------------------+
       | (MFA Match)
       V
[ Access Granted / Session Issued ]
```

## 6. Revision Tracking on GitHub
- **Repository Name:** `OS-SecureAuth-Module`
- **GitHub Link Format:** `https://github.com/YourUsername/OS-SecureAuth-Module`
- **Branching Strategy:** 
  - `main`: Production-ready, stable codebase.
  - `develop`: Integration branch for new features.
  - `feature/mfa-integration`: Feature-specific branch, merged into `develop` via Pull Requests.

**Sample Commit Messages:**
1. `init: setup base Python architecture and SQLite schema for user storage`
2. `feat(auth): implement bcrypt password hashing and verification`
3. `fix(security): strictly enforce 128-byte input limit to prevent buffer overflow`
4. `feat(mfa): integrate pyotp and QR code generation for TOTP`
5. `feat(logging): establish global audit trails for trapdoor detection`
6. `refactor(core): decouple security layer from api routing logic`
7. `docs: finalize academic project report and README instructions`

## 7. Conclusion and Future Scope
**Conclusion**
The Secure Authentication Module successfully demonstrates how multi-tiered security paradigms—combining modern cryptographic hashing, out-of-band MFA, and strict input policing—can mitigate severe systemic vulnerabilities. By emulating PAM workflows in a high-level environment, the module avoids buffer overflow risks while detecting trapdoor anomalies.

**Future Scope**
- **Biometric Integration:** Implementing FIDO2/WebAuthn for fingerprint or facial recognition handshakes.
- **AI Anomaly Detection:** Feeding auth logs into a machine learning model to heuristically detect and block brute-force or lateral movement.
- **Kernel-Level Integration:** Extracting the Python logic into C and wrapping it natively into a standard Linux `/lib/security/pam_secureauth.so` module for true root-level Operating System usage.

## 8. References
1. B. Schneier. "Applied Cryptography: Protocols, Algorithms, and Source Code in C." Wiley, 2015.
2. N. Provos and D. Mazières. "A Future-Adaptable Password Scheme (bcrypt)." USENIX Annual Technical Conference, 1999.
3. RFC 6238: "TOTP: Time-Based One-Time Password Algorithm", Internet Engineering Task Force (IETF), 2011.
4. "Defeating Buffer Overflows," OWASP Foundation. [Online]. Available: https://owasp.org.
5. V. Samar and C. Lai. "Making Login Services Independent from Authentication Technologies" (SunSoft PAM Specification), Sun Microsystems, 1996.

---

## APPENDIX A: AI-Generated Project Elaboration/Breakdown Report
### Extensive Architecture & Security Mechanics

**Detailed Architecture:**
The system is constructed with a zero-trust model at its boundary. The gateway API (Module 3) performs basic translation of incoming network requests. Immediately, the payload is serialized and transferred to the Security Layer (Module 2). Here, memory safety is enforced. While Python natively manages dynamic memory allocation—making traditional stack-smashing buffer overflows difficult—the application explicitly mirrors strict C-level memory rules by truncating or rejecting inputs exceeding exact buffer expectations (e.g., username > 32 bytes, password > 128 bytes). This prevents application-layer Service Exhaustion via memory ballooning.

**Operating System Integration (PAM Simulation):**
In a standard Unix/Linux environment, Pluggable Authentication Modules (PAM) abstract authentication. This Python module serves as a simulation of a PAM stack. Instead of directly interacting with `/etc/shadow`, it utilizes an encrypted `SQLite` registry. 

**MFA Design:**
We deploy an HMAC-based Time-based One-Time Password (TOTP) algorithm. A unique secret string is generated for each OS user and shared via a Base64-encoded QR Code. This decouples authentication into two domains: 'Something you know' (the bcrypt-hashed password) and 'Something you have' (the continuously rotating PyOTP token).

**Trapdoor and Backdoor Detection:**
Trapdoors are often placed by attackers to retain access. To counter this, all conditional logic is centralized. There are no hardcoded "super-admin" overrides. Furthermore, every invocation of the authentication method records contextual data (timestamp, IP, success/failure) into a protected OS-level log dir (`/logs/auth.log`). Heuristic analysis of this log can expose unauthorized trapdoors.

---

## APPENDIX B: Problem Statement
**Formal Problem Statement:**
*In contemporary Operating Systems, traditional single-factor authentication mechanisms are susceptible to brute-force attacks, memory-corruption exploits such as buffer overflows, and unauthorized persistence via hidden trapdoors. The objective of this project is to architect, develop, and evaluate a robust, modular Secure Authentication System that hardens user verification through cryptographic hashing (bcrypt), enforces strict buffer constraints on user input to preclude memory vulnerabilities, integrates Time-Based Multi-Factor Authentication (TOTP), and establishes immutable audit trails to detect and prevent backdoor access, thereby significantly enhancing overall kernel and user-space security.*

---

## APPENDIX C: Solution/Code

Below is the sample pseudo-production Python codebase demonstrating the core integration of hashing, strict buffer constraints, and MFA.

```python
import bcrypt
import pyotp
import logging
import os

# Setup immutable audit trail to detect trapdoors
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "auth_audit.log"),
    level=logging.INFO,
    format="%(asctime)s - [OS-AUTH-MODULE] - %(message)s",
)

class SecureAuthenticationModule:
    def __init__(self):
        # Simulated database storing hash and MFA secret
        self.os_user_db = {
            "root": {
                "hash": bcrypt.hashpw(b"SuperSecretRoot123", bcrypt.gensalt()),
                "mfa_secret": pyotp.random_base32()
            }
        }

    # ==========================================
    # SECURITY LAYER: Buffer Overflow Prevention
    # ==========================================
    def sanitize_input(self, username, password):
        """
        Enforce strict memory bounds to prevent buffer/stack overflow.
        Maximum username length: 32 bytes
        Maximum password length: 128 bytes
        """
        if len(username) > 32 or len(password) > 128:
            logging.warning(f"Buffer overflow attempt detected! Lengths: User={len(username)}, Pass={len(password)}")
            return False
            
        if not username.isalnum():
            logging.warning("Trapdoor prevention: Non-alphanumeric username input blocked.")
            return False
            
        return True

    # ==========================================
    # AUTHENTICATION CORE: Verification
    # ==========================================
    def authenticate_user(self, username, password, mfa_code):
        # 1. Validation Layer (Buffer Checks)
        if not self.sanitize_input(username, password):
            return False

        # 2. Trapdoor Prevention: No hardcoded backdoors
        if username not in self.os_user_db:
            logging.warning(f"Failed login attempt for unknown user: {username}")
            return False

        user_record = self.os_user_db[username]
        
        # 3. Cryptographic Validation
        if not bcrypt.checkpw(password.encode('utf-8'), user_record["hash"]):
            logging.warning(f"Failed login attempt: Invalid password for {username}")
            return False

        # 4. Multi-Factor Authentication (TOTP)
        totp = pyotp.TOTP(user_record["mfa_secret"])
        if not totp.verify(mfa_code, valid_window=1):
            logging.warning(f"Failed login attempt: MFA mismatch for {username}")
            return False

        logging.info(f"Successful OS authentication for {username}")
        return True

# --- Simulation / Usage --- #
if __name__ == "__main__":
    module = SecureAuthenticationModule()
    
    # Simulating a buffer overflow attack
    payload_username = "admin"
    payload_password = "A" * 500  # 500 bytes, exceeds 128 byte limit
    module.authenticate_user(payload_username, payload_password, "123456")
    # Action: REJECTED intrinsically by Security Layer
    
    # Valid Flow requires fetching TOTP code contextually
    root_secret = module.os_user_db["root"]["mfa_secret"]
    valid_mfa = pyotp.TOTP(root_secret).now()
    module.authenticate_user("root", "SuperSecretRoot123", valid_mfa)
    # Action: SUCCESS
```
