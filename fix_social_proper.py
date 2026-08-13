#!/usr/bin/env python
"""Fix social media - write correct HTML with proper closing tags."""
file_path = r"C:\Users\HP\Downloads\django-job-portal-master\django-job-portal-master\templates\base.html"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the social-links div and fix it
new_lines = []
i = 0
in_social_section = False
fixed = False

while i < len(lines):
    line = lines[i]
    
    # Check if we're entering social-links section
    if 'social-links' in line and '<div' in line:
        in_social_section = True
        # Write the corrected social media section
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
        fixed = True
        
        # Skip until we find the closing </div> for social-links
        div_depth = 1
        i += 1
        while i < len(lines) and div_depth > 0:
            if '<div' in lines[i]:
                div_depth += 1
            if '</div>' in lines[i]:
                div_depth -= 1
            i += 1
        continue
    
    new_lines.append(line)
    i += 1

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

if fixed:
    print("Social media section completely fixed with proper HTML!")
else:
    print("Social media section not found - manual check needed")
