# 🔐 SecureLocker
> Face-authenticated file vault with decoy system

A biometric security system that protects your files using facial recognition.
Wrong face gets shown empty decoy files. Right face unlocks the real vault.

---

## How It Works
Register face → 128-dimensional facial embedding saved (not a photo)
│
▼
Add files → Vault encrypts them immediately (Fernet encryption)
│
▼
Open locker → Face scan → Match? → Decrypt + show real files
→ No match? → Show decoy + log attempt silently

---

## Key Features

### 🧠 Facial Pattern Storage (not photo storage)
Your face is converted to 128 numbers representing facial geometry.
No photo is stored — just math. Useless to anyone without the code.

### 🎭 Decoy System
Wrong face or attacker sees convincing empty files.
Real vault stays hidden and encrypted.
This is called **plausible deniability** — used in professional security tools.

### 🔒 Fernet Encryption
Files are encrypted with a unique key using cryptography.fernet.
Without the key — encrypted files are unreadable.

### 🕵️ Silent Intruder Logging
Every failed access attempt is logged with timestamp.
Attacker never knows they're being logged.

### 🔄 Auto-lock
Vault automatically re-encrypts after you finish viewing.
Files are never left decrypted.

---

## Project Structure
SecureLocker/
├── core/
│   ├── face_auth.py      # Face registration + 128-dim embedding verification
│   ├── encryption.py     # Fernet encrypt/decrypt for vault files
│   └── decoy.py          # Decoy folder + silent intruder logging
├── data/                 # Created on first run (not in repo)
│   ├── face_embedding.npy  # Your facial pattern (gitignored)
│   ├── vault.key           # Encryption key (gitignored)
│   ├── vault/              # Your real encrypted files (gitignored)
│   └── decoy/              # Fake files shown to attackers (gitignored)
├── app.py                # Main locker interface
├── setup.py              # First-time setup wizard
└── requirements.txt

---

## Setup

```bash
git clone https://github.com/KARTHIK-2004-AI/SecureLocker
cd SecureLocker
python -m venv .venv
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

### First time — register your face
```bash
python setup.py
```
- Camera opens
- Look directly at camera
- Press SPACE to capture
- Your facial pattern is saved as 128 numbers

### Run the locker
```bash
python app.py
```

---

## Menu Options

| Option | What it does |
|---|---|
| 1. Lock vault | Encrypts all files in vault |
| 2. Unlock vault | Face scan → decrypt if matched |
| 3. View vault status | Shows locked/unlocked file count |
| 4. Re-register face | Update your facial pattern |
| 5. Exit | Close the app |
| 6. Export and clear | Decrypt + move files out + clear vault |

---

## Security Design

| Threat | Protection |
|---|---|
| Someone steals your files | Fernet encrypted — unreadable without key |
| Someone tries your face | 88% similarity threshold — wrong face denied |
| Attacker gets past auth | Sees empty decoy files — thinks nothing is there |
| Repeated break-in attempts | Silently logged with timestamps |
| Someone steals the repo | No keys or embeddings in repo — gitignored |

---

## Tech Stack

- Python 3.11
- DeepFace — facial embedding extraction
- OpenCV — camera capture
- cryptography.fernet — file encryption
- NumPy — embedding storage and cosine similarity

---

## Security Notice

> This is a project built for learning purposes.
> All facial data stays local — nothing is uploaded anywhere.
> Do not use as your only security layer for highly sensitive data.
