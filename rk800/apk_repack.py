import zipfile
import subprocess
import shutil
import logging
from pathlib import Path
from importlib.resources import files

logger = logging.getLogger(__name__)


class APKRepack:

    def __init__(self, tmp_dir: Path, output_path: Path):
        self.tmp_dir = tmp_dir
        self.output_path = output_path

    def repack(self):
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
        
        logger.info(f"APK written to: {self.output_path}")

    @staticmethod
    def _align_apk(input_path: Path, output_path: Path):
        # i refuse to remake this in python
        # absolute waste of my time
        if not shutil.which("zipalign"):
            raise FileNotFoundError("zipalign not found in PATH - install Android SDK build tools")
        
        subprocess.run([
            "zipalign", "-p", "-f", "4096", 
            str(input_path), str(output_path)
        ], check=True)

    @staticmethod
    def _sign_apk(apk_path: Path, temp_dir: Path):
        if not shutil.which("apksigner"):
            logger.warning("apksigner not found in PATH - APK will need to be signed manually later")
            return
        
        keystore_data = files("rk800.assets").joinpath("debug.keystore").read_bytes()
        keystore_path = temp_dir / "debug.keystore"
        keystore_path.write_bytes(keystore_data)

        # need to find a better way because scuffed
        # nvm this whole process was not intented to be ripped apart and put back 
        # together, but im not putting my keys outside of my .so
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
