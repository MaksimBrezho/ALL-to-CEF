import subprocess
import sys
import os


def build():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(root_dir, "icon", "ALLtoCEF.ico")
    data_files = [
        ("data/cef_fields.json", "data"),
        ("data/patterns_builtin.json", "data"),
        ("data/translations.json", "data"),
        ("icon/ALLtoCEF.ico", "icon"),
    ]
    pyinstaller_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--onefile",
        f"--icon={icon_path}",
        "--name=ALLtoCEF",
        os.path.join(root_dir, "main.py"),
    ]
    for src, dest in data_files:
        pyinstaller_cmd.append(
            f"--add-data={os.path.join(root_dir, src)}{os.pathsep}{dest}"
        )
    subprocess.run(pyinstaller_cmd, check=True)


if __name__ == "__main__":
    build()
