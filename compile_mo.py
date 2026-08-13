#!/usr/bin/env python
"""Compile .po to .mo files using polib since GNU gettext is not available."""
import os

try:
    import polib
    
    base_dir = r"C:\Users\HP\Downloads\django-job-portal-master\django-job-portal-master\locale"
    
    for lang in ['am', 'om', 'ti']:
        po_path = os.path.join(base_dir, lang, 'LC_MESSAGES', 'django.po')
        mo_path = os.path.join(base_dir, lang, 'LC_MESSAGES', 'django.mo')
        
        if os.path.exists(po_path):
            po = polib.pofile(po_path)
            po.save_as_mofile(mo_path)
            print(f"Compiled: {lang} - {len(po)} entries")
        else:
            print(f"Missing: {po_path}")

    print("\nAll translation files compiled successfully!")
    
except ImportError:
    print("polib not installed. Installing...")
    import subprocess
    subprocess.run(["pip", "install", "polib"], check=True)
    print("Please run this script again.")
