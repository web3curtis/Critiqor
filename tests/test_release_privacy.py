from __future__ import annotations

import importlib.util
import io
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "audit_release_artifacts.py"
SPEC = importlib.util.spec_from_file_location("audit_release_artifacts", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReleasePrivacyTests(unittest.TestCase):
    def test_clean_wheel_passes(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            artifact = Path(root) / "clean.whl"
            with zipfile.ZipFile(artifact, "w") as archive:
                archive.writestr("package/module.py", "TOKEN_ENV = 'CRITIQOR_API_KEY'")
            self.assertEqual(MODULE.audit(artifact), [])

    def test_private_path_and_secret_fail(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            artifact = Path(root) / "unsafe.tar.gz"
            payload = b"/Users/private-name/project\nAuthorization: Bearer abcdefghijklmnopqrstuvwxyz"
            with tarfile.open(artifact, "w:gz") as archive:
                info = tarfile.TarInfo("package/config.txt")
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))
            findings = MODULE.audit(artifact)
            self.assertTrue(any("macOS home path" in item for item in findings))
            self.assertTrue(any("bearer credential" in item for item in findings))

    def test_css_mask_identifier_is_not_a_secret(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            artifact = Path(root) / "styles.whl"
            with zipfile.ZipFile(artifact, "w") as archive:
                archive.writestr("package/styles.css", "mask-image-linear-from-position: 0")
            self.assertEqual(MODULE.audit(artifact), [])


if __name__ == "__main__":
    unittest.main()
