#!/usr/bin/env python
"""Change footer to solid dark background."""
import os
file_path = r"C:\Users\HP\Downloads\django-job-portal-master\django-job-portal-master\templates\base.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Change from gradient to solid dark color
content = content.replace(
    '<footer style="background: linear-gradient(135deg, #1e3c72 0%, #2b4d9 100%) !important; color: #ffffff !important; padding: 60px 0 0 0 !important; margin-top: 0 !important;">',
    '<footer style="background: #1a1a2e !important; color: #ffffff !important; padding: 60px 0 0 0 !important; margin-top: 0 !important;">'
)

# Also update CSS file
css_path = r"C:\Users\HP\Downloads\django-job-portal-master\django-job-portal-master\static\css\footer-modern.css"
if os.path.exists(css_path):
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    css_content = css_content.replace(
        'background: linear-gradient(135deg, #1e3c72 0%, #2b4d9 100%);',
        'background: #1a1a2e;'
    )
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_content)
    print("CSS updated to solid dark background!")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Footer changed to solid dark background (#1a1a2e)!")
print("This is a solid dark navy/charcoal color.")
