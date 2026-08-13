#!/usr/bin/env python
# -*- coding: utf-8 -*-
import struct
import os

def create_mo_file(mo_path, translations):
    """Create a .mo file from a dictionary of translations"""
    with open(mo_path, 'wb') as f:
        # Header
        f.write(struct.pack('<I', 0x950412de))  # magic number
        f.write(struct.pack('<I', 0))  # version
        f.write(struct.pack('<I', len(translations)))  # number of strings
        f.write(struct.pack('<I', 20))  # offset of original table
        f.write(struct.pack('<I', 20 + len(translations) * 8))  # offset of translation table
        
        # Calculate string offsets
        base = 20 + len(translations) * 16
        current = base
        
        keys = list(translations.keys())
        key_offsets = []
        for key in keys:
            key_offsets.append((len(key), current))
            current += len(key)
        
        val_offsets = []
        for key in keys:
            val = translations[key]
            val_offsets.append((len(val), current))
            current += len(val)
        
        # Write offset tables
        for length, offset in key_offsets:
            f.write(struct.pack('<II', length, offset))
        
        for length, offset in val_offsets:
            f.write(struct.pack('<II', length, offset))
        
        # Write strings
        for key in keys:
            f.write(key)
        
        for key in keys:
            f.write(translations[key])

base_dir = os.path.dirname(os.path.abspath(__file__))

# Amharic translations
am_trans = {}
am_trans[b'English'] = 'English'.encode('utf-8')
am_trans[b'Amharic'] = 'አማርኛ'.encode('utf-8')
am_trans[b'Oromo'] = 'ኦሮምኛ'.encode('utf-8')
am_trans[b'Tigrinya'] = 'ትግርኛ'.encode('utf-8')
am_trans[b'Language'] = 'ቋንቋ'.encode('utf-8')
am_trans[b'Home'] = 'መነሻ'.encode('utf-8')
am_trans[b'Jobs'] = 'ስራዎች'.encode('utf-8')
am_trans[b'Create ResumeCV'] = 'CV ይፍጠር'.encode('utf-8')

mo_path = os.path.join(base_dir, 'locale', 'am', 'LC_MESSAGES', 'django.mo')
create_mo_file(mo_path, am_trans)
print('Created Amharic .mo file')

# Oromo translations
om_trans = {}
om_trans[b'English'] = 'Ingiliffaa'.encode('utf-8')
om_trans[b'Amharic'] = 'Amaaraa'.encode('utf-8')
om_trans[b'Oromo'] = 'Oromoo'.encode('utf-8')
om_trans[b'Tigrinya'] = 'Tigree'.encode('utf-8')
om_trans[b'Language'] = 'Afaan'.encode('utf-8')
om_trans[b'Home'] = 'Mana'.encode('utf-8')
om_trans[b'Jobs'] = 'Hojiileen'.encode('utf-8')
om_trans[b'Create ResumeCV'] = 'CV Uumu'.encode('utf-8')

mo_path = os.path.join(base_dir, 'locale', 'om', 'LC_MESSAGES', 'django.mo')
create_mo_file(mo_path, om_trans)
print('Created Oromo .mo file')

# Tigrinya translations
ti_trans = {}
ti_trans[b'English'] = 'English'.encode('utf-8')
ti_trans[b'Amharic'] = 'አማርኛ'.encode('utf-8')
ti_trans[b'Oromo'] = 'ኦሮምኛ'.encode('utf-8')
ti_trans[b'Tigrinya'] = 'ትግርኛ'.encode('utf-8')
ti_trans[b'Language'] = 'ቋንቋ'.encode('utf-8')
ti_trans[b'Home'] = 'መነሻ'.encode('utf-8')
ti_trans[b'Jobs'] = 'ስራሕት'.encode('utf-8')
ti_trans[b'Create ResumeCV'] = 'CV ይፍጠር'.encode('utf-8')

mo_path = os.path.join(base_dir, 'locale', 'ti', 'LC_MESSAGES', 'django.mo')
create_mo_file(mo_path, ti_trans)
print('Created Tigrinya .mo file')

print('All translation files created successfully!')
