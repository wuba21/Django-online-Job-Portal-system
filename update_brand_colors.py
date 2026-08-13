#!/usr/bin/env python
"""Update social media to brand colors."""
file_path = r"C:\Users\HP\Downloads\django-job-portal-master\django-job-portal-master\templates\base.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Facebook color from white to blue (#1877F2)
content = content.replace(
    '<a href="https://web.facebook.com/profile.php?id=100077897349623&sk=directory_personal_details" target="_blank" rel="noopener" title="Facebook" style="color: #ffffff !important;',
    '<a href="https://web.facebook.com/profile.php?id=100077897349623&sk=directory_personal_details" target="_blank" rel="noopener" title="Facebook" style="color: #1877F2 !important;'
)

# Replace LinkedIn color from white to blue (#0A66C2)
content = content.replace(
    '<a href="https://linkedin.com/in/wubante-tilahun-776ab7377" target="_blank" rel="noopener" title="LinkedIn" style="color: #ffffff !important;',
    '<a href="https://linkedin.com/in/wubante-tilahun-776ab7377" target="_blank" rel="noopener" title="LinkedIn" style="color: #0A66C2 !important;'
)

# Replace Telegram color from white to blue (#0088CC)
content = content.replace(
    '<a href="https://t.me/UOGwuba" target="_blank" rel="noopener" title="Telegram" style="color: #ffffff !important;',
    '<a href="https://t.me/UOGwuba" target="_blank" rel="noopener" title="Telegram" style="color: #0088CC !important;'
)

# Replace GitHub color (keep light/white #f5f5f5)
content = content.replace(
    '<a href="https://wuba21.github.io" target="_blank" rel="noopener" title="GitHub" style="color: #ffffff !important;',
    '<a href="https://wuba21.github.io" target="_blank" rel="noopener" title="GitHub" style="color: #f5f5f5 !important;'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Social media updated to brand colors!")
print("Facebook: #1877F2 (blue)")
print("LinkedIn: #0A66C2 (blue)")
print("Telegram: #0088CC (blue)")
print("GitHub: #f5f5f5 (light gray)")
