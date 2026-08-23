import os
import cv2
import json
from datetime import datetime

INTRUDER_DIR = "data/intruders"
INTRUDER_LOG = "data/intruder_log.jsonl"

def capture_intruder(frame, reason="Unrecognized face / Spoof attempt"):
    """
    Silently captures intruder photo and logs detailed event information.
    """
    os.makedirs(INTRUDER_DIR, exist_ok=True)
    os.makedirs("data", exist_ok=True)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    photo_name = f"intruder_{timestamp_str}.jpg"
    photo_path = os.path.join(INTRUDER_DIR, photo_name)

    # Save photo if frame is available
    if frame is not None and frame.size > 0:
        cv2.imwrite(photo_path, frame)
    else:
        photo_path = None

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "reason": reason,
        "photo_path": photo_path,
        "action": "Redirected to Decoy Vault"
    }

    with open(INTRUDER_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

    print(f"🚨 Security Alert: Intruder snapshot captured -> {photo_path}")
    return photo_path

def get_intruder_logs():
    """Returns list of all logged intruder events"""
    if not os.path.exists(INTRUDER_LOG):
        return []
    logs = []
    with open(INTRUDER_LOG, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                logs.append(json.loads(line.strip()))
    return logs

if __name__ == "__main__":
    dummy = np.zeros((300, 300, 3), dtype=np.uint8)
    capture_intruder(dummy, "Test intruder capture")
    print(get_intruder_logs())
