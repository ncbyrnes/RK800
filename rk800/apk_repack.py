import tempfile
import shutil
import zipfile
import os
import subprocess
from pathlib import Path
from importlib.resources import files


class APKRepack:

    @staticmethod
    def repack(shared_object: bytearray, is_64: bool):
        temp_dir = None
        try:
            temp_dir = Path(tempfile.mkdtemp(prefix="rk800_apk_"))

            apk_data = (
                files("rk800.assets").joinpath("app-release-unsigned.apk").read_bytes()
            )
            apk_path = temp_dir / "input.apk"
            apk_path.write_bytes(apk_data)

            lib_dir = "arm64-v8a" if is_64 else "armeabi-v7a"
            so_name = f"lib/{lib_dir}/libsystemcache.so"

            with zipfile.ZipFile(apk_path, "a") as apk_zip:
                apk_zip.writestr(so_name, shared_object)

            APKRepack._sign_apk(apk_path, temp_dir)
            return apk_path.read_bytes()

        finally:
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir)

    @staticmethod
    def _sign_apk(apk_path: Path, temp_dir: Path):
        keystore_data = files("rk800.assets").joinpath("debug.keystore").read_bytes()
        keystore_path = temp_dir / "debug.keystore"
        keystore_path.write_bytes(keystore_data)

        # need to find a better way because scuffed
        subprocess.run(
            [
                "apksigner",
                "sign",
                "--ks",
                str(keystore_path),
                "--ks-pass",
                "pass:android",
                "--key-pass",
                "pass:android",
                str(apk_path),
            ],
            check=True,
        )
