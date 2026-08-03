import os, sys, shutil, subprocess, site

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(PROJECT_DIR, "dist")
ICON_PATH = os.path.join(PROJECT_DIR, "resources", "icons", "clipmind.ico")
RESOURCES_DIR = os.path.join(PROJECT_DIR, "resources")

def build():
    # Clean previous builds
    for d in ["build", "dist"]:
        p = os.path.join(PROJECT_DIR, d)
        if os.path.exists(p):
            shutil.rmtree(p)

    # Ensure icon exists
    if not os.path.exists(ICON_PATH):
        print("ERROR: icon not found at", ICON_PATH)
        sys.exit(1)

    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",              # GUI mode, no console window
        "--onefile",                # single exe
        "--name", "ClipMind",
        "--icon", ICON_PATH,
        "--add-data", f"{RESOURCES_DIR}{os.pathsep}resources",
        "--hidden-import", "PySide6.QtWidgets",
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtGui",
        "--hidden-import", "database",
        "--hidden-import", "clipboard",
        "--hidden-import", "search",
        "--hidden-import", "ui",
        "--hidden-import", "utils",
        "--clean",
        os.path.join(PROJECT_DIR, "main.py"),
    ]

    print("Running PyInstaller...")
    print("Command:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=PROJECT_DIR, capture_output=True, text=True)
    if result.returncode != 0:
        print("STDOUT:", result.stdout[-2000:])
        print("STDERR:", result.stderr[-2000:])
        print("Build failed!")
        return False

    exe_path = os.path.join(DIST_DIR, "ClipMind.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"SUCCESS: {exe_path} ({size_mb:.1f} MB)")
        return True
    else:
        print("Build completed but exe not found at", exe_path)
        print("Files in dist:", os.listdir(DIST_DIR) if os.path.exists(DIST_DIR) else "N/A")
        return False

if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1)
