#!/usr/bin/env python
"""Fix social media to be a proper list with inline-block."""
file_path = r"C:\Users\HP\Downloads\django-job-portal-master\django-job-portal-master\templates\base.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the social-links div with a proper list
old_section = '''                <div class="social-links">
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

new_section = '''                <ul class="social-links" style="list-style:none; padding:0; margin:0; display:flex; gap:10px;">
                    <li><a href="https://web.facebook.com/profile.php?id=100077897349623&sk=directory_personal_details" target="_blank" rel="noopener" title="Facebook" style="color:rgba(255,255,255,0.85); font-size:1.2rem; width:40px; height:40px; line-height:40px; text-align:center; background:rgba(255,255,255,0.1); border-radius:50%; display:block; text-decoration:none; transition:all 0.3s ease;">
                        <i class="fab fa-facebook-f"></i>
                    </a></li>
                    <li><a href="https://linkedin.com/in/wubante-tilahun-776ab7377" target="_blank" rel="noopener" title="LinkedIn" style="color:rgba(255,255,255,0.85); font-size:1.2rem; width:40px; height:40px; line-height:40px; text-align:center; background:rgba(255,255,255,0.1); border-radius:50%; display:block; text-decoration:none; transition:all 0.3s ease;">
                        <i class="fab fa-linkedin-in"></i>
                    </a></li>
                    <li><a href="https://t.me/UOGwuba" target="_blank" rel="noopener" title="Telegram" style="color:rgba(255,255,255,0.85); font-size:1.2rem; width:40px; height:40px; line-height:40px; text-align:center; background:rgba(255,255,255,0.1); border-radius:50%; display:block; text-decoration:none; transition:all 0.3s ease;">
                        <i class="fab fa-telegram"></i>
                    </a></li>
                    <li><a href="https://wuba21.github.io" target="_blank" rel="noopener" title="GitHub" style="color:rgba(255,255,255,0.85); font-size:1.2rem; width:40px; height:40px; line-height:40px; text-align:center; background:rgba(255,255,255,0.1); border-radius:50%; display:block; text-decoration:none; transition:all 0.3s ease;">
                        <i class="fab fa-github"></i>
                    </a></li>
                </ul>'''

if old_section in content:
    content = content.replace(old_section, new_section)
    print("Social media list fixed!")
else:
    print("Old section not found - trying alternative search...")
    # Try to find any social-links div
    if 'social-links' in content:
        print("Found social-links in content - manual check needed")
    else:
        print("No social-links found")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
