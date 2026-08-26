import os
import cv2
import numpy as np
import time

def load_cascade(xml_filename):
    """
    Safely loads a Haar Cascade classifier from OpenCV.
    Handles module attribute differences (cv2, cv2.cv2, cv2.objdetect)
    and checks multiple search locations for xml cascade files.
    """
    cascade_cls = getattr(cv2, 'CascadeClassifier', None)
    if cascade_cls is None and hasattr(cv2, 'cv2'):
        cascade_cls = getattr(cv2.cv2, 'CascadeClassifier', None)
    if cascade_cls is None and hasattr(cv2, 'objdetect'):
        cascade_cls = getattr(cv2.objdetect, 'CascadeClassifier', None)

    if cascade_cls is None:
        return None

    possible_paths = []
    
    # Try cv2.data.haarcascades if available
    if hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
        possible_paths.append(os.path.join(cv2.data.haarcascades, xml_filename))
        
    # Try working directory and relative paths
    possible_paths.append(xml_filename)
    possible_paths.append(os.path.join(os.path.dirname(__file__), xml_filename))
    possible_paths.append(os.path.join(os.path.dirname(__file__), '..', xml_filename))

    for path in possible_paths:
        if path and os.path.isfile(path) and os.path.getsize(path) > 0:
            try:
                cascade = cascade_cls(path)
                if hasattr(cascade, 'empty') and not cascade.empty():
                    return cascade
            except Exception:
                pass

    return None

def check_liveness(cap, timeout_seconds=10):
    """
    Prompts user to blink or move to verify liveness before facial authentication.
    Uses OpenCV Haar cascade eye detection when available, or motion fallback.
    Returns (True, frame) if liveness verified, otherwise (False, last_frame).
    """
    face_cascade = load_cascade('haarcascade_frontalface_default.xml')
    eye_cascade = load_cascade('haarcascade_eye.xml')

    print("\n👁️ LIVENESS CHECK")
    if face_cascade and eye_cascade:
        print("   Please look at camera and BLINK your eyes naturally...")
    else:
        print("   Please look at camera and MOVE your head slightly or BLINK...")

    start_time = time.time()
    blink_counter = 0
    eyes_closed_state = False
    last_frame = None
    prev_gray = None

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

        if face_cascade and eye_cascade:
            # Standard Haar Cascade detection
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
                    blink_counter += 1
                    eyes_closed_state = False
                    print(f"✨ Blink detected! ({blink_counter}/1)")
            else:
                if len(faces) > 0:
                    eyes_closed_state = True
        else:
            # Fallback Motion / Head Movement Detection when Haar Cascades are unavailable
            if prev_gray is not None:
                diff = cv2.absdiff(gray, prev_gray)
                motion_score = float(np.mean(diff))
                # Significant movement detected (human present)
                if 4.0 < motion_score < 40.0:
                    blink_counter = 1
                    print("✨ Motion/Liveness detected!")
            prev_gray = gray.copy()

        # Draw UI overlay
        status_color = (0, 255, 0) if blink_counter > 0 else (0, 165, 255)
        instruction_text = "LIVENESS CHECK: Please BLINK eyes" if (face_cascade and eye_cascade) else "LIVENESS CHECK: Please MOVE head / BLINK"
        cv2.putText(display, instruction_text,
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(display, f"Liveness: {'OK' if blink_counter > 0 else 'Pending'} | Timeout in: {remaining}s",
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
            print("❌ Liveness check timed out (No blink/motion detected - possible photo attack)")
            cv2.destroyAllWindows()
            return False, last_frame

    cv2.destroyAllWindows()
    return False, last_frame

if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    success, frame = check_liveness(cap)
    cap.release()
    print(f"Result: {success}")

