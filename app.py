import os
from core.face_auth import register_face, verify_face
from core.encryption import encrypt_vault, decrypt_vault, generate_key
from core.decoy import setup_decoy, show_decoy, show_real_vault

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


def unlock_vault():
    """Face auth → decrypt or show decoy"""
    print("\n" + "="*50)
    print("   SECURE LOCKER — UNLOCK")
    print("="*50)
    
    print("\nLook at the camera to unlock...")
    verified = verify_face()
    
    if verified:
        print("\n✅ Access granted!")
        decrypt_vault()
        show_real_vault()
        
        try:
            input("\nPress ENTER when done to lock vault again...")
        finally:
            encrypt_vault()
            print("🔒 Vault locked again.")
    else:
        print("\n❌ Face not recognized.")
        print("Showing vault contents...")
        show_decoy()
        print("\n🔒 Access denied.")
def export_and_clear():
    """Decrypt files, copy to export folder, then clear vault"""
    print("\n" + "="*50)
    print("   EXPORT AND CLEAR VAULT")
    print("="*50)
    
    print("\nVerify your face to export files...")
    verified = verify_face()
    
    if not verified:
        print("❌ Face not recognized. Export denied.")
        show_decoy()
        return
    
    # Decrypt first
    decrypt_vault()
    
    files = os.listdir("data/vault")
    if not files:
        print("ℹ️  Vault is already empty.")
        return
    
    # Create export folder
    export_path = "data/exported"
    os.makedirs(export_path, exist_ok=True)
    
    # Copy files out
    for filename in files:
        src = os.path.join("data/vault", filename)
        dst = os.path.join(export_path, filename)
        import shutil
        shutil.copy2(src, dst)
        os.remove(src)
        print(f"📤 Exported: {filename}")
    
    print(f"\n✅ Files moved to: data/exported/")
    print("✅ Vault is now empty and clean.")


def main():
    print("\n" + "="*50)
    print("        SECURE LOCKER")
    print("="*50)
    
    # Check if first time
    if not os.path.exists(EMBEDDING_PATH):
        print("\nNo registered user found.")
        setup = input("Run first time setup? (y/n): ")
        if setup.lower() == "y":
            first_time_setup()
        return
    
    # Main menu
    print("\n1. Lock vault")
    print("2. Unlock vault")
    print("3. View vault status")
    print("4. Re-register face")
    print("5. Exit")
    print("6. Export and clear vault")
    
    choice = input("\nChoose: ").strip()
    
    if choice == "1":
        lock_vault()
    elif choice == "2":
        unlock_vault()
    elif choice == "3":
        files = os.listdir("data/vault")
        locked = [f for f in files if f.endswith(".locked")]
        unlocked = [f for f in files if not f.endswith(".locked")]
        print(f"\n📊 Vault status:")
        print(f"   Locked files   : {len(locked)}")
        print(f"   Unlocked files : {len(unlocked)}")
    elif choice == "4":
        register_face()
    elif choice == "5":
        print("Goodbye.")
    elif choice == "6":
        export_and_clear()
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()