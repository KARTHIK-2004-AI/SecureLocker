import cv2
import numpy as np
from deepface import DeepFace
import os

EMBEDDING_PATH = "data/face_embedding.npy"

def capture_face(message="Press SPACE to capture, ESC to cancel"):
    """Opens camera and captures a frame"""
    
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

        # Show live feed with instruction
        display = frame.copy()
        cv2.putText(display, "SPACE = Capture | ESC = Cancel",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 0), 2)
        cv2.imshow("SecureLocker - Face Capture", display)

        key = cv2.waitKey(1)
        if key == 32:  # SPACE
            captured_frame = frame
            print("✅ Face captured")
            break
        elif key == 27:  # ESC
            print("❌ Cancelled")
            break

    cap.release()
    cv2.destroyAllWindows()
    return captured_frame


def extract_embedding(frame):
    """Extract 128-number facial pattern from a frame"""
    # Save frame temporarily for DeepFace to process
    temp_path = "data/temp_capture.jpg"
    cv2.imwrite(temp_path, frame)

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
        return False

    print("\n🔍 FACE VERIFICATION")
    frame = capture_face("Look at camera and press SPACE to verify")

    if frame is None:
        return False

    print("⏳ Comparing facial pattern...")

    # Load stored pattern
    stored_embedding = np.load(EMBEDDING_PATH)

    # Extract pattern from current frame
    current_embedding = extract_embedding(frame)

    if current_embedding is None:
        print("❌ Face not detected clearly")
        return False

    # Calculate cosine similarity between the two patterns
    similarity = np.dot(stored_embedding, current_embedding) / (
        np.linalg.norm(stored_embedding) * np.linalg.norm(current_embedding)
    )

    print(f"📊 Similarity score: {similarity:.4f}")

    # Threshold — above 0.85 = same person
    THRESHOLD = 0.85

    if similarity >= THRESHOLD:
        print(f"✅ Face verified! ({similarity:.2%} match)")
        return True
    else:
        print(f"❌ Face not recognized ({similarity:.2%} match — below {THRESHOLD:.0%} threshold)")
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