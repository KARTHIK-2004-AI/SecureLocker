import os
import warnings
import logging

# Suppress TensorFlow C++ and Python log spam
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
warnings.filterwarnings('ignore')
logging.getLogger('tensorflow').setLevel(logging.ERROR)

import cv2
import numpy as np
from deepface import DeepFace
import json
from datetime import datetime

EMBEDDING_PATH = "data/face_embedding.npy"
LOG_PATH = "data/verification_log.jsonl"
MATCH_THRESHOLD = 0.70


def log_verification_attempt(similarity, match, face_detected, message=""):
    """Appends a single JSON Lines (.jsonl) record to data/verification_log.jsonl"""
    os.makedirs("data", exist_ok=True)
    record = {
        "timestamp": datetime.now().isoformat(),
        "similarity": round(float(similarity), 4) if similarity is not None else None,
        "threshold": MATCH_THRESHOLD,
        "match": bool(match),
        "face_detected": bool(face_detected),
        "message": message
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def check_brightness(frame):
    """Returns average brightness (0-255) of a frame"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(np.mean(gray))


def enhance_lighting(frame):
    """Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) to balance lighting"""
    ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    y, cr, cb = cv2.split(ycrcb)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    y_eq = clahe.apply(y)
    ycrcb_eq = cv2.merge((y_eq, cr, cb))
    return cv2.cvtColor(ycrcb_eq, cv2.COLOR_YCrCb2BGR)


def capture_face(cap=None, message="Look at camera to authenticate", countdown_seconds=3.0, auto_capture=True):
    """
    Opens/uses camera and captures a steady face frame with live lighting analysis & countdown timer.
    Gives the user ~3 seconds to position their face, hold steady, and ensure lighting is clear.
    """
    import time
    release_cap_at_end = False
    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(0, cv2.CAP_MSMF)
        if not cap.isOpened():
            cap = cv2.VideoCapture(0)
        release_cap_at_end = True

    captured_frame = None
    start_time = time.time()
    print(f"\n📸 {message}")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Camera error")
            break

        brightness = check_brightness(frame)
        display = frame.copy()
        elapsed = time.time() - start_time
        remaining = max(0.0, countdown_seconds - elapsed)

        # Draw UI overlay
        if auto_capture and countdown_seconds > 0:
            status_str = f"Hold steady: Capturing in {remaining:.1f}s... (or press SPACE)"
        else:
            status_str = "SPACE = Capture | ESC = Cancel"

        cv2.putText(display, status_str,
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 255, 0), 2)

        if brightness < 65:
            cv2.putText(display, f"WARNING: Low Light ({int(brightness)}/255 - Too Dim)",
                        (10, 65), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 0, 255), 2)
        else:
            cv2.putText(display, f"Lighting OK ({int(brightness)}/255)",
                        (10, 65), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 255, 255), 1)

        cv2.imshow("SecureLocker - Face Capture", display)

        key = cv2.waitKey(30)
        if key == 32:  # SPACE
            captured_frame = frame.copy()
            print(f"✅ Face captured manually (Brightness score: {int(brightness)}/255)")
            break
        elif key == 27:  # ESC
            print("❌ Cancelled")
            break

        if auto_capture and countdown_seconds > 0 and elapsed >= countdown_seconds:
            captured_frame = frame.copy()
            print(f"✅ Auto-captured steady face (Brightness score: {int(brightness)}/255)")
            if brightness < 65:
                print("⚠️ Warning: Low lighting detected. Applying auto-enhancement...")
            break

    if release_cap_at_end:
        cap.release()
    cv2.destroyAllWindows()
    return captured_frame


def extract_embedding(frame):
    """Extract 128-number facial pattern from a frame with lighting enhancement and fallback"""
    if frame is None or frame.size == 0:
        return None

    # Apply CLAHE histogram equalization for consistent feature representation
    enhanced_frame = enhance_lighting(frame)

    os.makedirs("data", exist_ok=True)
    temp_path = "data/temp_capture.jpg"
    cv2.imwrite(temp_path, enhanced_frame)

    # 1. Primary extraction with enforced detection
    try:
        result = DeepFace.represent(
            img_path=temp_path,
            model_name="Facenet",
            enforce_detection=True
        )
        if result and len(result) > 0 and "embedding" in result[0]:
            embedding = np.array(result[0]["embedding"])
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return embedding
    except Exception:
        pass

    # 2. Fallback extraction without enforced detection (handles minor angles/lighting)
    try:
        result = DeepFace.represent(
            img_path=temp_path,
            model_name="Facenet",
            enforce_detection=False
        )
        if result and len(result) > 0 and "embedding" in result[0]:
            embedding = np.array(result[0]["embedding"])
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return embedding
    except Exception as e:
        print(f"❌ Could not extract facial features: {e}")

    if os.path.exists(temp_path):
        os.remove(temp_path)
    return None


def register_face(username="Admin", role="admin"):
    """Register user's face pattern with multi-user user_manager integration"""
    print(f"\n🔐 FACE REGISTRATION — Profile: '{username}' ({role.upper()})")
    print("="*45)
    print("Make sure:")
    print("  - Good lighting on your face")
    print("  - Look directly at the camera")
    print("  - No glasses or mask if possible")
    print("="*45)

    frame = capture_face(
        message=f"Hold steady & look at camera to register profile for '{username}'",
        countdown_seconds=3.0,
        auto_capture=True
    )

    if frame is None:
        print("❌ Registration cancelled")
        return False

    print("⏳ Extracting facial pattern...")
    embedding = extract_embedding(frame)

    if embedding is None:
        print("❌ Could not detect face clearly. Try again with better lighting.")
        return False

    from core.user_manager import register_user
    register_user(username, role, embedding)
    return True


def verify_face(enable_liveness=True):
    """
    Verify user's face against all registered profiles with anti-spoof liveness check and steady 3s capture.
    Returns (username, role, similarity) if verified, else (None, None, similarity).
    """
    from core.user_manager import list_users, match_user_embedding
    from core.liveness import check_liveness
    from core.intruder import capture_intruder

    users = list_users()
    if not users:
        print("❌ No registered users found. Please run setup or register a user first.")
        return None, None, 0.0

    print("\n🔍 MULTI-USER FACE VERIFICATION")

    cap = cv2.VideoCapture(0, cv2.CAP_MSMF)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)

    if enable_liveness:
        liveness_ok, _ = check_liveness(cap)
        if not liveness_ok:
            print("❌ Anti-Spoofing Check Failed: Liveness not verified.")
            capture_intruder(None, reason="Liveness check failed / Anti-spoof trigger")
            log_verification_attempt(
                similarity=None,
                match=False,
                face_detected=False,
                message="Liveness check failed"
            )
            cap.release()
            cv2.destroyAllWindows()
            return None, None, 0.0

        # After liveness is verified, give user 3 seconds in live camera preview to hold steady
        frame = capture_face(
            cap=cap,
            message="Liveness verified! Please HOLD STEADY & look at camera",
            countdown_seconds=3.0,
            auto_capture=True
        )
        cap.release()
        cv2.destroyAllWindows()
    else:
        frame = capture_face(
            cap=cap,
            message="Look at camera and hold steady to verify",
            countdown_seconds=3.0,
            auto_capture=True
        )
        cap.release()
        cv2.destroyAllWindows()

    if frame is None:
        log_verification_attempt(
            similarity=None,
            match=False,
            face_detected=False,
            message="Verification cancelled by user"
        )
        return None, None, 0.0

    print("⏳ Matching facial pattern against registered user profiles...")

    current_embedding = extract_embedding(frame)

    if current_embedding is None:
        print("❌ Face not detected clearly")
        capture_intruder(frame, reason="Face not detected clearly during extraction")
        log_verification_attempt(
            similarity=None,
            match=False,
            face_detected=False,
            message="Face not detected clearly"
        )
        return None, None, 0.0

    # Match against multi-user embeddings database
    matched_username, matched_role, similarity = match_user_embedding(current_embedding, MATCH_THRESHOLD)

    print(f"📊 Best Similarity Score: {similarity:.4f}")

    if matched_username:
        print(f"✅ Welcome, {matched_username}! ({matched_role.upper()}) — Verified ({similarity:.2%} match)")
        log_verification_attempt(
            similarity=similarity,
            match=True,
            face_detected=True,
            message=f"Verified user: {matched_username} ({matched_role})"
        )
        return matched_username, matched_role, similarity
    else:
        print(f"❌ Face not recognized ({similarity:.2%} match — below {MATCH_THRESHOLD:.0%} threshold)")
        capture_intruder(frame, reason=f"Unrecognized face ({similarity:.2%} match)")
        log_verification_attempt(
            similarity=similarity,
            match=False,
            face_detected=True,
            message="Face not recognized"
        )
        return None, None, similarity


if __name__ == "__main__":
    print("Testing multi-user face_auth module")
    print("1. Register User")
    print("2. Verify Face")
    choice = input("Choose: ")

    if choice == "1":
        uname = input("Username: ").strip()
        urole = input("Role (admin/member): ").strip()
        register_face(uname, urole)
    elif choice == "2":
        user, role, score = verify_face()
        print(f"\nResult: User={user}, Role={role}, Score={score}")