#!/usr/bin/env python
"""Fix social media section to remove incorrect li tags."""
file_path = r"C:\Users\HP\Downloads\django-job-portal-master\templates\base.html"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix the social-links section
new_lines = []
skip_until_end = False
social_fixed = False

i = 0
while i < len(lines):
    line = lines[i]
    
    # Find the start of social-links
    if 'social-links' in line and '<ul' in line:
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
        
        # Skip until we find the closing </ul>
        skip_until_end = True
        social_fixed = True
        i += 1
        continue
    
    if skip_until_end:
        if '</ul>' in line:
            skip_until_end = False
        i += 1
        continue
    
    new_lines.append(line)
    i += 1

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

if social_fixed:
    print("Social media section fixed!")
else:
    print("Social media section not found - checking alternative...")
    # Check if it's already fixed
    content = ''.join(lines)
    if '<div class="social-links">' in content and '<a href=' in content:
        print("Social media looks correct already!")
    else:
        print("Manual check needed")
