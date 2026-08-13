#!/usr/bin/env python
"""Change social media icons to their brand colors."""
file_path = r"C:\Users\HP\Downloads\django-job-portal-master\django-job-portal-master\templates\base.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Change social media links to brand colors
# Facebook: #1877F2 (blue)
# LinkedIn: #0A66C2 (blue)
# Telegram: #0088CC (blue)
# GitHub: #f5f5f5 (light/white)

content = content.replace(
    '<a href="https://web.facebook.com/profile.php?id=100077897349623&sk=directory_personal_details" target="_blank" rel="noopener" title="Facebook" style="color: #ffffff !important; font-size: 1.3rem !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; background: rgba(255,255,255,0.15) !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">',
    '<a href="https://web.facebook.com/profile.php?id=100077897349623&sk=directory_personal_details" target="_blank" rel="noopener" title="Facebook" style="color: #1877F2 !important; font-size: 1.3rem !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; background: rgba(24,119,242,0.15) !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">'
)

content = content.replace(
    '<a href="https://linkedin.com/in/wubante-tilahun-776ab7377" target="_blank" rel="noopener" title="LinkedIn" style="color: #ffffff !important; font-size: 1.3rem !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; background: rgba(255,255,255,0.15) !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">',
    '<a href="https://linkedin.com/in/wubante-tilahun-776ab7377" target="_blank" rel="noopener" title="LinkedIn" style="color: #0A66C2 !important; font-size: 1.3rem !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; background: rgba(10,102,194,0.15) !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">'
)

content = content.replace(
    '<a href="https://t.me/UOGwuba" target="_blank" rel="noopener" title="Telegram" style="color: #ffffff !important; font-size: 1.3rem !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; background: rgba(255,255,255,0.15) !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">',
    '<a href="https://t.me/UOGwuba" target="_blank" rel="noopener" title="Telegram" style="color: #0088CC !important; font-size: 1.3rem !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; background: rgba(0,136,204,0.15) !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">'
)

content = content.replace(
    '<a href="https://wuba21.github.io" target="_blank" rel="noopener" title="GitHub" style="color: #ffffff !important; font-size: 1.3rem !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; background: rgba(255,255,255,0.15) !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">',
    '<a href="https://wuba21.github.io" target="_blank" rel="noopener" title="GitHub" style="color: #f5f5f5 !important; font-size: 1.3rem !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; background: rgba(245,245,245,0.15) !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Social media icons changed to brand colors!")
print("Facebook: #1877F2 (blue)")
print("LinkedIn: #0A66C2 (blue)")
print("Telegram: #0088CC (blue)")
print("GitHub: #f5f5f5 (light gray)")
