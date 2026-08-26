import os
import json
import shutil
import numpy as np
from cryptography.fernet import Fernet

USERS_DIR = "data/users"
LEGACY_EMBEDDING = "data/face_embedding.npy"
LEGACY_KEY = "data/vault.key"
LEGACY_VAULT = "data/vault"

def get_user_paths(username):
    """Returns directory structure for a specific user"""
    user_dir = os.path.join(USERS_DIR, username)
    return {
        "dir": user_dir,
        "embedding": os.path.join(user_dir, "embedding.npy"),
        "key": os.path.join(user_dir, "user.key"),
        "role": os.path.join(user_dir, "role.json"),
        "vault": os.path.join(user_dir, "vault")
    }

def init_user_system():
    """Initializes user system and migrates legacy single-user data to Admin profile"""
    os.makedirs(USERS_DIR, exist_ok=True)
    
    # Check if legacy single-user profile exists and migrate it
    if os.path.exists(LEGACY_EMBEDDING) and not os.path.exists(os.path.join(USERS_DIR, "Admin")):
        print("🔄 Migrating legacy single-user profile to Admin user...")
        admin_paths = get_user_paths("Admin")
        os.makedirs(admin_paths["dir"], exist_ok=True)
        os.makedirs(admin_paths["vault"], exist_ok=True)

        # Move embedding
        shutil.move(LEGACY_EMBEDDING, admin_paths["embedding"])

        # Move key or generate new key
        if os.path.exists(LEGACY_KEY):
            shutil.move(LEGACY_KEY, admin_paths["key"])
        else:
            key = Fernet.generate_key()
            with open(admin_paths["key"], "wb") as f:
                f.write(key)

        # Save role
        with open(admin_paths["role"], "w", encoding="utf-8") as f:
            json.dump({"username": "Admin", "role": "admin"}, f)

        # Move legacy vault files
        if os.path.exists(LEGACY_VAULT):
            for file_name in os.listdir(LEGACY_VAULT):
                src = os.path.join(LEGACY_VAULT, file_name)
                dst = os.path.join(admin_paths["vault"], file_name)
                if os.path.isfile(src):
                    shutil.move(src, dst)

        print("✅ Legacy profile successfully migrated to 'Admin'")

def list_users():
    """Returns list of registered user dicts [{'username': 'Admin', 'role': 'admin'}]"""
    init_user_system()
    users = []
    if not os.path.exists(USERS_DIR):
        return users

    for entry in os.listdir(USERS_DIR):
        user_dir = os.path.join(USERS_DIR, entry)
        if os.path.isdir(user_dir):
            role_file = os.path.join(user_dir, "role.json")
            role = "member"
            if os.path.exists(role_file):
                try:
                    with open(role_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        role = data.get("role", "member")
                except Exception:
                    pass
            users.append({"username": entry, "role": role})
    return users

def get_user_key(username):
    """Loads or generates per-user encryption key"""
    paths = get_user_paths(username)
    if not os.path.exists(paths["key"]):
        key = Fernet.generate_key()
        with open(paths["key"], "wb") as f:
            f.write(key)
        return key
    with open(paths["key"], "rb") as f:
        return f.read()

def register_user(username, role, embedding):
    """Registers a new user profile with face embedding and private encryption key"""
    init_user_system()
    
    # Check if face already matches an existing user profile
    existing_user, existing_role, similarity = match_user_embedding(embedding, match_threshold=0.70)
    if existing_user and existing_user.lower() != username.lower():
        print(f"\n❌ Duplicate Face Detected: This face is already registered to user '{existing_user}' ({similarity:.2%} match).")
        print("   Registration blocked: One person cannot create multiple profiles under different names.")
        return False

    paths = get_user_paths(username)
    os.makedirs(paths["dir"], exist_ok=True)
    os.makedirs(paths["vault"], exist_ok=True)

    # Save face embedding
    np.save(paths["embedding"], embedding)

    # Generate user private key
    get_user_key(username)

    # Save role metadata
    with open(paths["role"], "w", encoding="utf-8") as f:
        json.dump({"username": username, "role": role.lower()}, f)

    print(f"✅ User '{username}' ({role.upper()}) registered successfully!")
    return True

def match_user_embedding(current_embedding, match_threshold=0.70):
    """
    Compares current face embedding against all registered users.
    Returns (username, role, similarity) if match found, else (None, None, max_similarity).
    """
    init_user_system()
    users = list_users()
    if not users:
        return None, None, 0.0

    best_match_user = None
    best_match_role = None
    best_similarity = 0.0

    for user in users:
        username = user["username"]
        paths = get_user_paths(username)
        if os.path.exists(paths["embedding"]):
            stored_embedding = np.load(paths["embedding"])
            similarity = np.dot(stored_embedding, current_embedding) / (
                np.linalg.norm(stored_embedding) * np.linalg.norm(current_embedding)
            )
            if similarity > best_similarity:
                best_similarity = similarity
                if similarity >= match_threshold:
                    best_match_user = username
                    best_match_role = user["role"]

    return best_match_user, best_match_role, float(best_similarity)

def encrypt_user_vault(username):
    """Encrypts all files in user's isolated vault using user's private key"""
    paths = get_user_paths(username)
    vault_path = paths["vault"]
    os.makedirs(vault_path, exist_ok=True)
    files = [f for f in os.listdir(vault_path) if not f.endswith(".locked")]
    if not files:
        print(f"ℹ️  No unencrypted files in {username}'s vault")
        return
    fernet = Fernet(get_user_key(username))
    for filename in files:
        file_path = os.path.join(vault_path, filename)
        with open(file_path, "rb") as f:
            data = f.read()
        encrypted = fernet.encrypt(data)
        with open(file_path + ".locked", "wb") as f:
            f.write(encrypted)
        os.remove(file_path)
    print(f"🔒 {username}'s vault locked — {len(files)} file(s) encrypted")

def decrypt_user_vault(username):
    """Decrypts all .locked files in user's isolated vault using user's private key"""
    paths = get_user_paths(username)
    vault_path = paths["vault"]
    os.makedirs(vault_path, exist_ok=True)
    files = [f for f in os.listdir(vault_path) if f.endswith(".locked")]
    if not files:
        print(f"ℹ️  No encrypted files in {username}'s vault")
        return
    fernet = Fernet(get_user_key(username))
    success_count = 0
    for filename in files:
        file_path = os.path.join(vault_path, filename)
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            decrypted = fernet.decrypt(data)
            original_path = file_path[:-7]
            with open(original_path, "wb") as f:
                f.write(decrypted)
            os.remove(file_path)
            success_count += 1
        except Exception as e:
            print(f"❌ Decryption failed for {filename}: {e}")
    print(f"🔓 {username}'s vault unlocked — {success_count} file(s) decrypted")

def add_file_to_user_vault(username, source_path):
    """Moves file to user's vault and encrypts it with user's key"""
    if not os.path.exists(source_path):
        print(f"❌ File not found: {source_path}")
        return False
    paths = get_user_paths(username)
    os.makedirs(paths["vault"], exist_ok=True)
    filename = os.path.basename(source_path)
    dest_path = os.path.join(paths["vault"], filename)
    shutil.move(source_path, dest_path)
    fernet = Fernet(get_user_key(username))
    with open(dest_path, "rb") as f:
        data = f.read()
    encrypted = fernet.encrypt(data)
    with open(dest_path + ".locked", "wb") as f:
        f.write(encrypted)
    os.remove(dest_path)
    print(f"📦 Moved and locked in {username}'s vault: {filename}")
    return True

def delete_user_profile(username):
    """Deletes user profile directory"""
    paths = get_user_paths(username)
    if os.path.exists(paths["dir"]):
        shutil.rmtree(paths["dir"])
        print(f"🗑️ User profile '{username}' deleted.")
        return True
    return False

if __name__ == "__main__":
    init_user_system()
    print("Users:", list_users())
