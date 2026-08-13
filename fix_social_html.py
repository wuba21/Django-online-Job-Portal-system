#!/usr/bin/env python
"""Fix social media HTML structure."""
file_path = r"C:\Users\HP\Downloads\django-job-portal-master\django-job-portal-master\templates\base.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the social-links section - add proper closing tags
import re

# Find and fix the social-links div
pattern = r'(<div class="social-links">.*?</div>)'
match = re.search(pattern, content, re.DOTALL)

if match:
    old_section = match.group(1)
    # Fix: ensure each <a> tag is properly closed
    new_section = '''<div class="social-links">
                    <a href="https://web.facebook.com/profile.php?id=100077897349623&sk=directory_personal_details" target="_blank" rel="noopener" title="Facebook">
                        <i class="fab fa-facebook-f"></i>
                    </a>
                    <a href="https://linkedin.com/in/wubante-tilahun-776ab7377" target="_blank" rel="noopener" title="LinkedIn">
                        <i class="fab fa-linkedin-in"></i>
                    </a>
                    <a href="https://t.me/UOGwuba" target="_blank" rel="noopener" title="Telegram">
                        <i class="fab fa-telegram"></i>
                    </a>
                    <a href="https://wuba21.github.io" target="_blank" rel="noopener" title="GitHub">
                        <i class="fab fa-github"></i>
                    </a>
                </div>'''
    
    content = content.replace(old_section, new_section)
    print("Social media HTML structure fixed!")
else:
    print("social-links div not found")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
