import os
from cryptography.fernet import Fernet

KEY_PATH = "data/vault.key"

def generate_key():
    """Generate and save encryption key — runs once during setup"""
    key = Fernet.generate_key()
    with open(KEY_PATH, "wb") as f:
        f.write(key)
    print("✅ Encryption key generated")
    return key

def load_key():
    if not os.path.exists(KEY_PATH): 
        return generate_key()
    with open(KEY_PATH, "rb") as f:
        return f.read()

def encrypt_file(file_path):
    """Encrypt a single file in place"""
    fernet = Fernet(load_key())
    with open(file_path, "rb") as f:
        data = f.read()
    encrypted = fernet.encrypt(data)
    with open(file_path + ".locked", "wb") as f:
        f.write(encrypted)
    os.remove(file_path)
    print(f"🔒 Encrypted: {os.path.basename(file_path)}")

def decrypt_file(file_path):
    """Decrypt a .locked file"""
    fernet = Fernet(load_key())
    with open(file_path, "rb") as f:
        data = f.read()
    decrypted = fernet.decrypt(data)
    original_path = file_path.replace(".locked", "")
    with open(original_path, "wb") as f:
        f.write(decrypted)
    os.remove(file_path)
    print(f"🔓 Decrypted: {os.path.basename(original_path)}")

def encrypt_vault():
    """Encrypt everything in data/vault/"""
    vault_path = "data/vault"
    files = [f for f in os.listdir(vault_path) if not f.endswith(".locked")]
    if not files:
        print("ℹ️  No unencrypted files in vault")
        return
    for filename in files:
        encrypt_file(os.path.join(vault_path, filename))
    print(f"✅ Vault locked — {len(files)} file(s) encrypted")

def decrypt_vault():
    """Decrypt everything in data/vault/"""
    vault_path = "data/vault"
    files = [f for f in os.listdir(vault_path) if f.endswith(".locked")]
    if not files:
        print("ℹ️  No encrypted files to decrypt")
        return
    for filename in files:
        decrypt_file(os.path.join(vault_path, filename))
    print(f"✅ Vault unlocked — {len(files)} file(s) decrypted")

def add_file_to_vault(source_path):
    """MOVE file into vault and encrypt it — original location becomes empty"""
    import shutil
    if not os.path.exists(source_path):
        print(f"❌ File not found: {source_path}")
        return False

    vault_path = "data/vault"
    filename = os.path.basename(source_path)
    dest_path = os.path.join(vault_path, filename)

    # MOVE file into vault (not copy)
    shutil.move(source_path, dest_path)
    print(f"📦 File moved into vault: {filename}")

    # Encrypt it inside vault
    encrypt_file(dest_path)
    print(f"🔒 File locked: {filename}")
    
    return True
def setup_decoy():
    """Create convincing empty decoy folder"""
    decoy_path = "data/decoy"
    os.makedirs(decoy_path, exist_ok=True)
    decoys = ["documents.txt", "notes.txt", "readme.txt"]
    for decoy in decoys:
        path = os.path.join(decoy_path, decoy)
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write("")
    print("✅ Decoy folder ready")


if __name__ == "__main__":
    # Quick test
    test_file = "data/vault/test.txt"
    with open(test_file, "w") as f:
        f.write("This is a secret file inside the vault.")
    
    print("Before encryption:")
    print(os.listdir("data/vault"))
    
    encrypt_vault()
    print("\nAfter encryption:")
    print(os.listdir("data/vault"))
    
    decrypt_vault()
    print("\nAfter decryption:")
    print(os.listdir("data/vault"))