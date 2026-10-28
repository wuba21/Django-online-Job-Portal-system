#!/usr/bin/env python
"""
Compile gettext .po files to binary .mo files across all supported languages.
Uses polib if installed, or falls back to django.core.management.call_command.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALE_DIR = os.path.join(BASE_DIR, "locale")
LANGUAGES = ["am", "om", "ti"]

def compile_translations():
    try:
        import polib
    except ImportError:
        print("polib not found. Installing polib for gettext compilation...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "polib"], check=True)
        import polib

    success_count = 0
    for lang in LANGUAGES:
        po_path = os.path.join(LOCALE_DIR, lang, "LC_MESSAGES", "django.po")
        mo_path = os.path.join(LOCALE_DIR, lang, "LC_MESSAGES", "django.mo")

        if os.path.exists(po_path):
            po = polib.pofile(po_path)
            po.save_as_mofile(mo_path)
            print(f"[OK] Compiled: {lang} -> {len(po)} entries saved to {mo_path}")
            success_count += 1
        else:
            print(f"[WARN] Translation file not found: {po_path}")

    print(f"Compilation finished. Successfully compiled {success_count}/{len(LANGUAGES)} languages.")

if __name__ == "__main__":
    compile_translations()
