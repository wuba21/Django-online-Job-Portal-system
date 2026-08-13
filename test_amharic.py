#!/usr/bin/env python
"""Test if Amharic translations are working correctly."""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobs.settings')

import django
django.setup()

from django.utils.translation import activate, gettext

# Test Amharic
activate('am')
tests = [
    ("About Django-Jobs", "ስለ Django-Jobs"),
    ("Contact Us", "ከኛ ይገናኙ"),
    ("Quick Links", "ፈጣን ማገናኛዎች"),
    ("Follow Us", "ከኛ ይከተሉ"),
    ("Home", "መነሻ"),
]

print("Testing Amharic translations:")
print("=" * 50)
all_passed = True
for english, expected_amharic in tests:
    result = gettext(english)
    if result == expected_amharic:
        print(f"✓ '{english}' -> '{result}'")
    else:
        print(f"✗ '{english}' -> '{result}' (expected: '{expected_amharic}')")
        all_passed = False

print("=" * 50)
if all_passed:
    print("All Amharic translations are working!")
else:
    print("Some translations are not working correctly.")
