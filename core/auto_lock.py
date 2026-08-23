import time
import threading
import os
from core.encryption import encrypt_vault

class AutoLockManager:
    """Background timer that automatically encrypts open vault files after idle timeout."""
    def __init__(self, timeout_seconds=300):
        self.timeout_seconds = timeout_seconds
        self.last_activity = time.time()
        self.running = False
        self.thread = None

    def touch(self):
        """Update last activity timestamp"""
        self.last_activity = time.time()

    def start(self):
        """Start background monitor thread"""
        self.last_activity = time.time()
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop background monitor thread"""
        self.running = False

    def _monitor_loop(self):
        while self.running:
            time.sleep(5)
            idle_time = time.time() - self.last_activity
            if idle_time >= self.timeout_seconds:
                # Check if there are unencrypted files
                vault_path = "data/vault"
                if os.path.exists(vault_path):
                    unencrypted = [f for f in os.listdir(vault_path) if not f.endswith(".locked")]
                    if unencrypted:
                        print(f"\n⏰ Auto-Lock Triggered: Vault idle for {int(idle_time)}s. Locking files...")
                        encrypt_vault()
                        print("🔒 Vault automatically locked due to inactivity.")
                self.touch()  # reset timer after lock

auto_locker = AutoLockManager(timeout_seconds=300)
