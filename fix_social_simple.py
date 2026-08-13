#!/usr/bin/env python
"""Simple fix for social media section."""
file_path = r"C:\Users\HP\Downloads\django-job-portal-master\django-job-portal-master\templates\base.html"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and replace the social-links section
new_lines = []
i = 0
skip_until_end = False

while i < len(lines):
    line = lines[i]
    
    # Check if we found the social-links div
    if 'social-links' in line and '<div' in line:
        # Write the correct social media section
        new_lines.append('                <div class="social-links">\n')
        new_lines.append('                    <a href="https://web.facebook.com/profile.php?id=100077897349623&sk=directory_personal_details" target="_blank" rel="noopener" title="Facebook">\n')
        new_lines.append('                        <i class="fab fa-facebook-f"></i>\n')
        new_lines.append('                    </a>\n')
        new_lines.append('                    <a href="https://linkedin.com/in/wubante-tilahun-776ab7377" target="_blank" rel="noopener" title="LinkedIn">\n')
        new_lines.append('                        <i class="fab fa-linkedin-in"></i>\n')
        new_lines.append('                    </a>\n')
        new_lines.append('                    <a href="https://t.me/UOGwuba" target="_blank" rel="noopener" title="Telegram">\n')
        new_lines.append('                        <i class="fab fa-telegram"></i>\n')
        new_lines.append('                    </a>\n')
        new_lines.append('                    <a href="https://wuba21.github.io" target="_blank" rel="noopener" title="GitHub">\n')
        new_lines.append('                        <i class="fab fa-github"></i>\n')
        new_lines.append('                    </a>\n')
        new_lines.append('                </div>\n')
        
        # Skip until we find the closing </div> for social-links
        div_count = 1
        i += 1
        while i < len(lines) and div_count > 0:
            if '<div' in lines[i]:
                div_count += 1
            if '</div>' in lines[i]:
                div_count -= 1
            i += 1
        continue
    
    new_lines.append(line)
    i += 1

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Social media section fixed!")
