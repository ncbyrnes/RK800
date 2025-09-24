import zipfile
import subprocess
import shutil
import os
from pathlib import Path
from importlib.resources import files


class APKRepack:
    """Handle APK repacking with custom shared libraries

    Replaces lib/ directory in APK with custom binaries and signs result.
    """

    def __init__(self, tmp_dir: Path, output_path: Path, ctx):
        """Initialize APK repacker

        Args:
            tmp_dir (Path): temporary directory containing .so files
            output_path (Path): path for output APK
            ctx: RK800Context instance with view manager
        """
        self.tmp_dir = tmp_dir
        self.output_path = output_path
        self.ctx = ctx

    def repack(self):
        """Repack APK with custom shared libraries

        Extracts APK, replaces lib/ directory, aligns, and signs.
        """
        apk_data = (
            files("rk800.assets").joinpath("app-release-unsigned.apk").read_bytes()
        )
        apk_path = self.tmp_dir / "input.apk"
        apk_path.write_bytes(apk_data)

        temp_apk_path = self.tmp_dir / "temp.apk"

        with zipfile.ZipFile(apk_path, "r") as input_zip:
            with zipfile.ZipFile(temp_apk_path, "w") as output_zip:
                for item in input_zip.infolist():
                    if not item.filename.startswith("lib/"):
                        data = input_zip.read(item.filename)
                        output_zip.writestr(item, data)

                for so_file in self.tmp_dir.rglob("*.so"):
                    relative_path = so_file.relative_to(self.tmp_dir)
                    so_name = f"lib/{relative_path}"
                    output_zip.writestr(so_name, so_file.read_bytes())

        apk_path.unlink()
        temp_apk_path.rename(apk_path)

        aligned_apk_path = self.tmp_dir / "aligned.apk"
        self._align_apk(apk_path, aligned_apk_path)
        self._sign_apk(aligned_apk_path, self.tmp_dir)

        with open(self.output_path, "wb") as output_file:
            output_file.write(aligned_apk_path.read_bytes())

        self.ctx.view.success(f"APK written to: {self.output_path}")

    @staticmethod
    def _align_apk(input_path: Path, output_path: Path):
        """Align APK using zipalign tool

        Args:
            input_path (Path): input APK path
            output_path (Path): aligned APK output path
        """
        # i refuse to remake this in python
        # absolute waste of my time
        if not shutil.which("zipalign"):
            raise FileNotFoundError(
                "zipalign not found in PATH - install Android SDK build tools"
            )

        subprocess.run(
            ["zipalign", "-p", "-f", "4096", str(input_path), str(output_path)],
            check=True,
        )

    def _sign_apk(self, apk_path: Path, temp_dir: Path):
        """Sign APK using apksigner tool

        Args:
            apk_path (Path): APK file to sign
            temp_dir (Path): temporary directory for keystore
        """
        apksigner_path = os.environ.get("APKSIGNER_PATH", "apksigner")
        if not shutil.which(apksigner_path):
            self.ctx.view.warning(
                f"{apksigner_path} not found in PATH - APK will need to be signed manually later"
            )
            return

        keystore_path = os.environ.get("KEYSTORE_PATH")
        keystore_pass = os.environ.get("KEYSTORE_PASS")

        if not keystore_path:
            try:
                keystore_data = (
                    files("rk800.assets").joinpath("debug.keystore").read_bytes()
                )
                keystore_path = temp_dir / "debug.keystore"
                keystore_path.write_bytes(keystore_data)
                keystore_pass = "android"
                self.ctx.view.warning(
                    "Using embedded debug keystore - not for production use"
                )
                self.ctx.view.warning(
                    "Set KEYSTORE_PATH and KEYSTORE_PASS for production"
                )
            except FileNotFoundError:
                self.ctx.view.error(
                    "No keystore found. Set KEYSTORE_PATH environment variable or provide debug.keystore"
                )
                return
        elif not keystore_pass:
            self.ctx.view.error(
                "Keystore password required. Set KEYSTORE_PASS environment variable"
            )
            return

        key_pass = os.environ.get("KEY_PASS", keystore_pass)

        try:
            result = subprocess.run(
                [
                    apksigner_path,
                    "sign",
                    "--ks",
                    str(keystore_path),
                    "--ks-pass",
                    f"pass:{keystore_pass}",
                    "--key-pass",
                    f"pass:{key_pass}",
                    str(apk_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.ctx.view.success("APK signed successfully")
        except subprocess.CalledProcessError as error:
            self.ctx.view.error(f"apksigner failed: {error.stderr or error.stdout}")
            raise
