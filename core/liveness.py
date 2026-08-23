import cv2
import numpy as np
import time

def check_liveness(cap, timeout_seconds=10):
    """
    Prompts user to blink to verify liveness before facial authentication.
    Uses OpenCV Haar cascade eye detection to detect eye open/close transitions.
    Returns (True, frame) if liveness verified, otherwise (False, last_frame).
    """
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

    print("\n👁️ LIVENESS CHECK")
    print("   Please look at camera and BLINK your eyes naturally...")

    start_time = time.time()
    blink_counter = 0
    eyes_closed_state = False
    last_frame = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        last_frame = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        display = frame.copy()
        elapsed = time.time() - start_time
        remaining = max(0, int(timeout_seconds - elapsed))

        # Detect face
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(100, 100))

        eyes_found = False

        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            cv2.rectangle(display, (x, y), (x + w, y + h), (255, 200, 0), 2)
            
            # ROI for upper half of face (eyes region)
            eye_roi_gray = gray[y:y + int(h * 0.6), x:x + w]
            eyes = eye_cascade.detectMultiScale(eye_roi_gray, scaleFactor=1.1, minNeighbors=4, minSize=(20, 20))

            if len(eyes) >= 1:
                eyes_found = True

        # Blink Detection State Machine
        if eyes_found:
            if eyes_closed_state:
                # Transition from closed -> open = 1 Blink!
                blink_counter += 1
                eyes_closed_state = False
                print(f"✨ Blink detected! ({blink_counter}/1)")
        else:
            # No eyes detected in face ROI (likely closed or mid-blink)
            if len(faces) > 0:
                eyes_closed_state = True

        # Draw UI overlay
        status_color = (0, 255, 0) if blink_counter > 0 else (0, 165, 255)
        cv2.putText(display, "LIVENESS CHECK: Please BLINK eyes",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(display, f"Blinks: {blink_counter}/1 | Timeout in: {remaining}s",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)

        cv2.imshow("SecureLocker - Anti-Spoofing Check", display)

        key = cv2.waitKey(30)
        if key == 27:  # ESC
            print("❌ Liveness check cancelled")
            cv2.destroyAllWindows()
            return False, last_frame

        if blink_counter >= 1:
            cv2.putText(display, "LIVENESS VERIFIED ✅",
                        (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow("SecureLocker - Anti-Spoofing Check", display)
            cv2.waitKey(400)
            cv2.destroyAllWindows()
            print("✅ Liveness verified (Live human present)")
            return True, last_frame

        if elapsed >= timeout_seconds:
            print("❌ Liveness check timed out (No blink detected - possible photo attack)")
            cv2.destroyAllWindows()
            return False, last_frame

    cv2.destroyAllWindows()
    return False, last_frame

if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    success, frame = check_liveness(cap)
    cap.release()
    print(f"Result: {success}")
