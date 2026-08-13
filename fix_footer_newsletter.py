#!/usr/bin/env python
"""Remove newsletter and fix social media section."""
file_path = r"C:\Users\HP\Downloads\django-job-portal-master\django-job-portal-master\templates\base.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the newsletter section
import re

# Pattern to remove newsletter div
newsletter_pattern = r'<div class="newsletter mt-4">.*?</div>\s*</div>'
content = re.sub(newsletter_pattern, '', content, flags=re.DOTALL)

# Fix social media section - make it a simple horizontal list
social_pattern = r'<div class="social-links">.*?</div>\s*</div>'
new_social = '''<div class="social-links">
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

content = re.sub(social_pattern, new_social, content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Newsletter removed and social media fixed!")
