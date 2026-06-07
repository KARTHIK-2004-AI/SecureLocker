import os
import datetime

VAULT_PATH = "data/vault"
DECOY_PATH = "data/decoy"

def setup_decoy():
    """Create decoy folder with fake empty-looking files"""
    os.makedirs(DECOY_PATH, exist_ok=True)
    decoys = ["notes.txt", "passwords.txt", "personal.txt"]
    for filename in decoys:
        path = os.path.join(DECOY_PATH, filename)
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write("")
    print("✅ Decoy folder ready")

def log_intruder():
    """Silently log failed access attempts"""
    log_path = "data/intruder_log.txt"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a") as f:
        f.write(f"[{timestamp}] Failed access attempt\n")

def show_decoy():
    """What attacker sees — empty files, logged silently"""
    log_intruder()
    files = os.listdir(DECOY_PATH)
    print("\n📁 Vault contents:")
    for f in files:
        print(f"   {f} (0 KB)")
    print("\n[No data found]")

def show_real_vault():
    """What real user sees after successful auth"""
    files = os.listdir(VAULT_PATH)
    if not files:
        print("\n📁 Vault is empty — add files to data/vault/")
        return
    print("\n📁 Vault contents:")
    for f in files:
        size = os.path.getsize(os.path.join(VAULT_PATH, f))
        print(f"   {f}  ({size} bytes)")

if __name__ == "__main__":
    setup_decoy()
    print("\n--- Attacker sees this ---")
    show_decoy()
    print("\n--- Real user sees this ---")
    show_real_vault()