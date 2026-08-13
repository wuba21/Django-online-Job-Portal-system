#!/usr/bin/env python
"""Force dark footer background and white social icons with inline styles."""
file_path = r"C:\Users\HP\Downloads\django-job-portal-master\django-job-portal-master\templates\base.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Force footer to have dark gradient background
content = content.replace('<footer class="footer">', 
    '<footer class="footer" style="background: linear-gradient(135deg, #1e3c72 0%, #2b4d9 100%) !important; color: #ffffff !important; padding: 60px 0 0 0 !important;">')

# Force social media links to be white and visible
content = content.replace('<div class="social-links">', 
    '<div class="social-links" style="display: flex !important; gap: 15px !important;">')

# Add inline styles to each social media link to ensure white color
import re

# Pattern to find social media links and add inline styles
def add_inline_styles(match):
    text = match.group(0)
    # Add style to each <a> tag
    text = text.replace('<a href="https://web.facebook.com', '<a style="color: #ffffff !important; background: rgba(255,255,255,0.15) !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; border-radius: 50% !important; text-decoration: none !important; margin: 0 5px !important;" href="https://web.facebook.com')
    text = text.replace('<a href="https://linkedin.com', '<a style="color: #ffffff !important; background: rgba(255,255,255,0.15) !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; border-radius: 50% !important; text-decoration: none !important; margin: 0 5px !important;" href="https://linkedin.com')
    text = text.replace('<a href="https://t.me', '<a style="color: #ffffff !important; background: rgba(255,255,255,0.15) !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; border-radius: 50% !important; text-decoration: none !important; margin: 0 5px !important;" href="https://t.me')
    text = text.replace('<a href="https://wuba21.github.io', '<a style="color: #ffffff !important; background: rgba(255,255,255,0.15) !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; border-radius: 50% !important; text-decoration: none !important; margin: 0 5px !important;" href="https://wuba21.github.io')
    return text

content = re.sub(r'<div class="social-links".*?</div>', add_inline_styles, content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Inline styles added! Footer should now have dark background with white icons!")
