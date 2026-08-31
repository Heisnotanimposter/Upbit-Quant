import os
import unittest
import tempfile
from pathlib import Path
from src.utils.security import SecurityGuard

class TestSecurityGuard(unittest.TestCase):

    def test_mask_secret(self):
        self.assertEqual(SecurityGuard.mask_secret(""), "<NOT SET>")
        self.assertEqual(SecurityGuard.mask_secret("12345"), "***")
        self.assertEqual(SecurityGuard.mask_secret("abcdefghijkl1234"), "ab***1234")

    def test_enforce_file_permissions(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"secret_data")
            tmp_path = tmp.name

        try:
            SecurityGuard.enforce_file_permissions(tmp_path, 0o600)
            mode = oct(os.stat(tmp_path).st_mode & 0o777)
            self.assertEqual(mode, "0o600")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_telegram_authorization(self):
        self.assertTrue(SecurityGuard.is_authorized_telegram_user("12345678", "12345678"))
        self.assertFalse(SecurityGuard.is_authorized_telegram_user("99999999", "12345678"))
        self.assertFalse(SecurityGuard.is_authorized_telegram_user("12345678", ""))

    def test_fat_finger_cap(self):
        self.assertTrue(SecurityGuard.check_fat_finger_cap(1_000_000, 10_000_000))
        self.assertFalse(SecurityGuard.check_fat_finger_cap(15_000_000, 10_000_000))

if __name__ == "__main__":
    unittest.main()
