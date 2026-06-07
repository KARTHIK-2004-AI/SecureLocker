import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.face_auth import register_face
from core.encryption import generate_key, setup_decoy
from core.decoy import setup_decoy

def setup():
    print("\n" + "="*45)
    print("   🔐 SECURE LOCKER — FIRST TIME SETUP")
    print("="*45)

    # Step 1 — Create folders
    print("\n[1/3] Creating folder structure...")
    os.makedirs("data/vault", exist_ok=True)
    os.makedirs("data/decoy", exist_ok=True)
    print("✅ Folders created")

    # Step 2 — Generate encryption key
    print("\n[2/3] Generating encryption key...")
    generate_key()

    # Step 3 — Register face
    print("\n[3/3] Registering your face...")
    print("      This is your locker key — do this carefully")
    success = register_face()

    if not success:
        print("\n❌ Setup failed — face not registered")
        print("   Run setup.py again to retry")
        return False

    # Step 4 — Setup decoy
    setup_decoy()

    print("\n" + "="*45)
    print("   ✅ SETUP COMPLETE")
    print("="*45)
    print("\nYour locker is ready.")
    print("→ Add files to:  data/vault/")
    print("→ Run locker:    python app.py")
    print("="*45)
    return True

if __name__ == "__main__":
    setup()