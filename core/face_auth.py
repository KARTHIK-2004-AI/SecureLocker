import cv2
import numpy as np
from deepface import DeepFace
import os
import json
from datetime import datetime

EMBEDDING_PATH = "data/face_embedding.npy"
LOG_PATH = "data/verification_log.jsonl"
MATCH_THRESHOLD = 0.85


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


def capture_face(message="Press SPACE to capture, ESC to cancel"):
    """Opens camera and captures a frame with live lighting analysis"""
    
    cap = cv2.VideoCapture(0, cv2.CAP_MSMF)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    captured_frame = None

    print(f"\n📸 {message}")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Camera error")
            break

        brightness = check_brightness(frame)

        # Show live feed with instruction and brightness warning
        display = frame.copy()
        cv2.putText(display, "SPACE = Capture | ESC = Cancel",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 0), 2)
        
        if brightness < 65:
            cv2.putText(display, f"WARNING: Low Light ({int(brightness)}/255 - Too Dim)",
                        (10, 65), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 0, 255), 2)
        else:
            cv2.putText(display, f"Lighting OK ({int(brightness)}/255)",
                        (10, 65), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 255, 255), 1)

        cv2.imshow("SecureLocker - Face Capture", display)

        key = cv2.waitKey(1)
        if key == 32:  # SPACE
            captured_frame = frame
            print(f"✅ Face captured (Brightness score: {int(brightness)}/255)")
            if brightness < 65:
                print("⚠️ Warning: Low lighting detected. Applying auto-enhancement...")
            break
        elif key == 27:  # ESC
            print("❌ Cancelled")
            break

    cap.release()
    cv2.destroyAllWindows()
    return captured_frame


def extract_embedding(frame):
    """Extract 128-number facial pattern from a frame with lighting enhancement"""
    # Apply CLAHE histogram equalization for consistent feature representation
    enhanced_frame = enhance_lighting(frame)

    # Save frame temporarily for DeepFace to process
    temp_path = "data/temp_capture.jpg"
    cv2.imwrite(temp_path, enhanced_frame)

    try:
        # Extract embedding using Facenet model
        result = DeepFace.represent(
            img_path=temp_path,
            model_name="Facenet",
            enforce_detection=True
        )
        embedding = np.array(result[0]["embedding"])
        os.remove(temp_path)
        return embedding

    except Exception as e:
        print(f"❌ Face not detected clearly: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return None


def register_face():
    """Register user's face pattern — runs once during setup"""
    print("\n🔐 FACE REGISTRATION")
    print("="*40)
    print("Make sure:")
    print("  - Good lighting on your face")
    print("  - Look directly at the camera")
    print("  - No glasses or mask if possible")
    print("="*40)

    frame = capture_face("Look at camera and press SPACE to register")

    if frame is None:
        print("❌ Registration cancelled")
        return False

    print("⏳ Extracting facial pattern...")
    embedding = extract_embedding(frame)

    if embedding is None:
        print("❌ Could not detect face clearly. Try again with better lighting.")
        return False

    # Save the 128-number pattern
    np.save(EMBEDDING_PATH, embedding)
    print(f"✅ Facial pattern saved — {len(embedding)} dimensional embedding stored")
    print("✅ Registration complete")
    return True


def verify_face():
    """Verify user's face against stored pattern"""
    if not os.path.exists(EMBEDDING_PATH):
        print("❌ No registered face found. Run setup first.")
        log_verification_attempt(
            similarity=None,
            match=False,
            face_detected=False,
            message="No registered face found"
        )
        return False

    print("\n🔍 FACE VERIFICATION")
    frame = capture_face("Look at camera and press SPACE to verify")

    if frame is None:
        log_verification_attempt(
            similarity=None,
            match=False,
            face_detected=False,
            message="Verification cancelled by user"
        )
        return False

    print("⏳ Comparing facial pattern...")

    # Load stored pattern
    stored_embedding = np.load(EMBEDDING_PATH)

    # Extract pattern from current frame
    current_embedding = extract_embedding(frame)

    if current_embedding is None:
        print("❌ Face not detected clearly")
        log_verification_attempt(
            similarity=None,
            match=False,
            face_detected=False,
            message="Face not detected clearly"
        )
        return False

    # Calculate cosine similarity between the two patterns
    similarity = np.dot(stored_embedding, current_embedding) / (
        np.linalg.norm(stored_embedding) * np.linalg.norm(current_embedding)
    )

    print(f"📊 Similarity score: {similarity:.4f}")

    is_match = bool(similarity >= MATCH_THRESHOLD)

    if is_match:
        print(f"✅ Face verified! ({similarity:.2%} match)")
        log_verification_attempt(
            similarity=similarity,
            match=True,
            face_detected=True,
            message="Face verified successfully"
        )
        return True
    else:
        print(f"❌ Face not recognized ({similarity:.2%} match — below {MATCH_THRESHOLD:.0%} threshold)")
        log_verification_attempt(
            similarity=similarity,
            match=False,
            face_detected=True,
            message="Face not recognized (below threshold)"
        )
        return False


if __name__ == "__main__":
    print("Testing face_auth module")
    print("1. Register")
    print("2. Verify")
    choice = input("Choose: ")

    if choice == "1":
        register_face()
    elif choice == "2":
        result = verify_face()
        print(f"\nResult: {'GRANTED' if result else 'DENIED'}")