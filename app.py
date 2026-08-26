import os
import warnings
import logging

# Suppress TensorFlow C++ and Python log spam
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
warnings.filterwarnings('ignore')
logging.getLogger('tensorflow').setLevel(logging.ERROR)

from core.face_auth import register_face, verify_face
from core.encryption import encrypt_vault, decrypt_vault, generate_key, add_file_to_vault, decrypt_file
from core.decoy import setup_decoy, show_decoy, show_real_vault
from core.auto_lock import auto_locker
from core.intruder import get_intruder_logs
from core.user_manager import (
    init_user_system, list_users, register_user, decrypt_user_vault,
    encrypt_user_vault, add_file_to_user_vault, get_user_paths, delete_user_profile
)
import tkinter as tk
from tkinter import filedialog

EMBEDDING_PATH = "data/face_embedding.npy"
KEY_PATH = "data/vault.key"

def first_time_setup():
    """Runs only once — registers face and sets up vault"""
    print("\n" + "="*50)
    print("   SECURE LOCKER — FIRST TIME SETUP")
    print("="*50)
    
    os.makedirs("data/vault", exist_ok=True)
    os.makedirs("data/decoy", exist_ok=True)
    
    # Step 1: Register face
    print("\nStep 1: Register your face")
    success = register_face()
    if not success:
        print("❌ Setup failed — face registration unsuccessful")
        return False
    
    # Step 2: Generate encryption key
    print("\nStep 2: Generating encryption key...")
    generate_key()
    
    # Step 3: Setup decoy
    print("\nStep 3: Setting up decoy vault...")
    setup_decoy()
    
    print("\n✅ Setup complete! Your locker is ready.")
    print("📁 Add files you want to protect into: data/vault/")
    print("🔒 Run app.py again to lock them.\n")
    return True


def lock_vault():
    """Encrypt all files in vault"""
    print("\n🔒 Locking vault...")
    encrypt_vault()
    print("✅ Vault is now locked. Files are encrypted.")

def browse_file():
    """Open file picker dialog — user selects file visually"""
    root = tk.Tk()
    root.withdraw()  # Hide the empty tkinter window
    root.attributes('-topmost', True)  # Bring dialog to front
    
    file_path = filedialog.askopenfilename(
        title="Select file to secure",
        filetypes=[
            ("All files", "*.*"),
            ("Documents", "*.pdf *.docx *.txt"),
            ("Images", "*.jpg *.png *.jpeg"),
            ("Videos", "*.mp4 *.avi *.mkv"),
        ]
    )
    root.destroy()
    return file_path if file_path else None

def show_user_vault(username):
    """Displays files inside user's isolated vault"""
    paths = get_user_paths(username)
    vault_path = paths["vault"]
    os.makedirs(vault_path, exist_ok=True)
    files = os.listdir(vault_path)
    if not files:
        print(f"\n📁 {username}'s Vault is empty.")
        return
    print(f"\n📁 {username}'s Vault contents:")
    for f in files:
        size = os.path.getsize(os.path.join(vault_path, f))
        status = "🔒 LOCKED" if f.endswith(".locked") else "🔓 UNLOCKED"
        print(f"   [{status}] {f}  ({size} bytes)")

def manage_users_menu(current_admin_user="Admin"):
    """Admin User Management Menu"""
    print("\n" + "="*50)
    print("   ADMIN USER MANAGEMENT")
    print("="*50)
    print("1. List All Registered Users")
    print("2. Register New User Profile")
    print("3. Delete User Profile")
    print("4. Back to Main Session")

    choice = input("\nChoose: ").strip()

    if choice == "1":
        users = list_users()
        print("\n👥 Registered Profiles:")
        for u in users:
            print(f"   • {u['username']}  (Role: {u['role'].upper()})")

    elif choice == "2":
        new_name = input("Enter new username: ").strip()
        if not new_name:
            print("❌ Invalid username")
            return
        role_choice = input("Assign Role (1. Member / 2. Admin): ").strip()
        role = "admin" if role_choice == "2" else "member"
        register_face(username=new_name, role=role)

    elif choice == "3":
        users = list_users()
        print("\n👥 Registered Profiles:")
        for idx, u in enumerate(users, 1):
            print(f"   {idx}. {u['username']} ({u['role'].upper()})")
        target_input = input("Enter number or username to delete: ").strip()

        target_name = None
        if target_input.isdigit():
            idx = int(target_input) - 1
            if 0 <= idx < len(users):
                target_name = users[idx]['username']
        else:
            target_name = target_input

        if not target_name:
            print("❌ Invalid selection.")
            return

        if target_name.lower() == current_admin_user.lower():
            print(f"❌ Cannot delete your own active session profile ('{current_admin_user}').")
            return

        admin_count = len([u for u in users if u['role'].lower() == 'admin'])
        target_user_obj = next((u for u in users if u['username'].lower() == target_name.lower()), None)

        if target_user_obj and target_user_obj['role'].lower() == 'admin' and admin_count <= 1:
            print("❌ Cannot delete the primary Admin profile.")
            return

        delete_user_profile(target_name)

def view_intruder_logs():
    """Display logged security events and captured intruder photos"""
    print("\n" + "="*50)
    print("   SECURITY AUDIT & INTRUDER LOGS")
    print("="*50)
    logs = get_intruder_logs()
    if not logs:
        print("✅ No intruder activity recorded. System secure.")
        return

    print(f"\n🚨 Total Security Events Logged: {len(logs)}\n")
    for idx, entry in enumerate(logs, 1):
        print(f"[{idx}] Timestamp : {entry.get('timestamp')}")
        print(f"    Reason    : {entry.get('reason')}")
        print(f"    Snapshot  : {entry.get('photo_path', 'None')}")
        print(f"    Action    : {entry.get('action')}\n")

def unlock_vault():
    """Face auth → decrypt isolated user vault or show decoy"""
    print("\n" + "="*50)
    print("   SECURE LOCKER PRO — UNLOCK")
    print("="*50)
    
    print("\nLook at the camera to authenticate...")
    matched_user, matched_role, similarity = verify_face(enable_liveness=True)
    
    if matched_user:
        print(f"\n✅ Access granted! Welcome, {matched_user} ({matched_role.upper()})")
        decrypt_user_vault(matched_user)
        show_user_vault(matched_user)
        
        while True:
            print(f"\n--- {matched_user}'s Session ---")
            print("1. Add a file to your vault")
            print("2. View your vault contents")
            print("3. Lock and exit session")
            if matched_role == "admin":
                print("4. Admin User Management (Register/List Users)")
                print("5. View Intruder Snapshots & Security Audit")

            action = input("Choose: ").strip()
            auto_locker.touch()

            if action == "1":
                print("\n📂 Opening file browser...")
                path = browse_file()
                if path:
                    print(f"Selected: {os.path.basename(path)}")
                    add_file_to_user_vault(matched_user, path)
                    # Decrypt newly added file for active session
                    locked_added = os.path.join(get_user_paths(matched_user)["vault"], os.path.basename(path) + ".locked")
                    if os.path.exists(locked_added):
                        from cryptography.fernet import Fernet
                        from core.user_manager import get_user_key
                        fernet = Fernet(get_user_key(matched_user))
                        with open(locked_added, "rb") as f:
                            data = f.read()
                        decrypted = fernet.decrypt(data)
                        orig = locked_added[:-7]
                        with open(orig, "wb") as f:
                            f.write(decrypted)
                        os.remove(locked_added)
                    show_user_vault(matched_user)
                else:
                    print("❌ No file selected")

            elif action == "2":
                show_user_vault(matched_user)

            elif action == "3":
                break

            elif action == "4" and matched_role == "admin":
                manage_users_menu(current_admin_user=matched_user)

            elif action == "5" and matched_role == "admin":
                view_intruder_logs()

            else:
                print("Invalid choice")

        encrypt_user_vault(matched_user)
        print(f"🔒 {matched_user}'s vault locked. Session ended.")

    else:
        print("\n❌ Face not recognized.")
        show_decoy()
        print("\n🔒 Access denied.")

def main():
    auto_locker.start()
    init_user_system()
    
    print("\n" + "="*50)
    print("        SECURE LOCKER PRO (MULTI-USER)")
    print("="*50)

    users = list_users()
    if not users:
        print("\nNo registered user profile found.")
        setup = input("Register initial Admin face profile? (y/n): ")
        if setup.lower() == "y":
            register_face(username="Admin", role="admin")
        return

    print("\nRegistered Profiles:", ", ".join([f"{u['username']} ({u['role'].upper()})" for u in users]))
    print("\n1. Unlock Vault (Face Authentication)")
    print("2. Register New User Profile")
    print("3. Exit")

    choice = input("\nChoose: ").strip()
    auto_locker.touch()

    if choice == "1":
        unlock_vault()
    elif choice == "2":
        uname = input("Username for new profile: ").strip()
        if uname:
            r_choice = input("Role (1. Member / 2. Admin): ").strip()
            role = "admin" if r_choice == "2" else "member"
            register_face(username=uname, role=role)
    elif choice == "3":
        auto_locker.stop()
        print("Goodbye.")
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()