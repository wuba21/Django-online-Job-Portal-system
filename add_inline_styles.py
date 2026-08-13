#!/usr/bin/env python
"""Add inline styles to footer to ensure colors show."""
file_path = r"C:\Users\HP\Downloads\django-job-portal-master\django-job-portal-master\templates\base.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add inline styles to footer tag
content = content.replace('<footer class="footer">', 
    '<footer class="footer" style="background: linear-gradient(135deg, #1e3c72 0%, #2b4d9 100%) !important; color: #ffffff !important;">')

# Add inline styles to social links
content = content.replace('<div class="social-links">', 
    '<div class="social-links" style="display: flex !important; gap: 15px !important;">')

# Make social links white and visible
content = content.replace('<a href="https://web.facebook.com/profile.php?id=100077897349623&sk=directory_personal_details" target="_blank" rel="noopener" title="Facebook">',
    '<a href="https://web.facebook.com/profile.php?id=100077897349623&sk=directory_personal_details" target="_blank" rel="noopener" title="Facebook" style="color: #ffffff !important; background: rgba(255,255,255,0.15) !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">')

content = content.replace('<a href="https://linkedin.com/in/wubante-tilahun-776ab7377" target="_blank" rel="noopener" title="LinkedIn">',
    '<a href="https://linkedin.com/in/wubante-tilahun-776ab7377" target="_blank" rel="noopener" title="LinkedIn" style="color: #ffffff !important; background: rgba(255,255,255,0.15) !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">')

content = content.replace('<a href="https://t.me/UOGwuba" target="_blank" rel="noopener" title="Telegram">',
    '<a href="https://t.me/UOGwuba" target="_blank" rel="noopener" title="Telegram" style="color: #ffffff !important; background: rgba(255,255,255,0.15) !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">')

content = content.replace('<a href="https://wuba21.github.io" target="_blank" rel="noopener" title="GitHub">',
    '<a href="https://wuba21.github.io" target="_blank" rel="noopener" title="GitHub" style="color: #ffffff !important; background: rgba(255,255,255,0.15) !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Inline styles added to footer!")
