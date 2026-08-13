#!/usr/bin/env python
"""Update social media links in footer."""
file_path = r"C:\Users\HP\Downloads\django-job-portal-master\django-job-portal-master\templates\base.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the social media section in footer and replace it
old_social_section = '''                <div class="col-lg-4 col-md-12 mb-5">
                    <h4 class="h5">Follow Us</h4>
                    <a href="https://www.facebook.com/django-jobs" target="_blank" rel="noopener">
                        <i class="fab fa-facebook-f"></i> Facebook
                    </a>
                    <a href="https://www.twitter.com/django-jobs" target="_blank" rel="noopener">
                        <i class="fab fa-twitter"></i> Twitter
                    </a>
                    <a href="https://www.linkedin.com/company/django-jobs" target="_blank" rel="noopener">
                        <i class="fab fa-linkedin-in"></i> LinkedIn
                    </a>
                </div>'''

new_social_section = '''                <div class="col-lg-4 col-md-12 mb-5">
                    <h4 class="h5">{% trans "Follow Us" %}</h4>
                    <a href="https://web.facebook.com/profile.php?id=100077897349623&sk=directory_personal_details" target="_blank" rel="noopener">
                        <i class="fab fa-facebook-f"></i> Facebook
                    </a>
                    <a href="https://linkedin.com/in/wubante-tilahun-776ab7377" target="_blank" rel="noopener">
                        <i class="fab fa-linkedin-in"></i> LinkedIn
                    </a>
                    <a href="https://t.me/UOGwuba" target="_blank" rel="noopener">
                        <i class="fab fa-telegram"></i> Telegram
                    </a>
                </div>'''

content = content.replace(old_social_section, new_social_section)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Social media links updated successfully!")
