#!/usr/bin/env python
"""Fix footer - rewrite with correct Django i18n syntax."""
file_path = r"C:\Users\HP\Downloads\django-job-portal-master\django-job-portal-master\templates\base.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find footer position
footer_start = content.find('<footer')
if footer_start == -1:
    print("Footer not found!")
    exit()

footer_end = content.find('</footer>')
if footer_end == -1:
    print("Footer end not found!")
    exit()
footer_end += len('</footer>')

# New footer with CORRECT Django i18n syntax
new_footer = '''
<footer style="background: #1a1a2e !important; color: #ffffff !important; padding: 60px 0 0 0 !important; margin-top: 0 !important;">
    <div class="container">
        <div class="row">
            <!-- About Section -->
            <div class="col-lg-3 col-md-6 mb-4">
                <h4 style="font-size: 1.1rem !important; font-weight: 600 !important; margin-bottom: 20px !important; color: #ffffff !important; text-transform: uppercase !important; letter-spacing: 0.05em !important; position: relative !important; padding-bottom: 10px !important;">
                    {% trans "About Django-Jobs" %}
                    <span style="position: absolute !important; left: 0 !important; bottom: 0 !important; width: 40px !important; height: 3px !important; background: #ffffff !important; border-radius: 2px !important;"></span>
                </h4>
                <p style="color: rgba(255,255,255,0.85) !important; line-height: 1.6 !important; font-size: 0.9rem !important;">
                    {% trans "Your premier platform for connecting talented professionals with outstanding career opportunities. We simplify the job search and hiring process for both job seekers and employers." %}
                </p>
            </div>
            
            <!-- Contact Section -->
            <div class="col-lg-3 col-md-6 mb-4">
                <h4 style="font-size: 1.1rem !important; font-weight: 600 !important; margin-bottom: 20px !important; color: #ffffff !important; text-transform: uppercase !important; letter-spacing: 0.05em !important; position: relative !important; padding-bottom: 10px !important;">
                    {% trans "Contact Us" %}
                    <span style="position: absolute !important; left: 0 !important; bottom: 0 !important; width: 40px !important; height: 3px !important; background: #ffffff !important; border-radius: 2px !important;"></span>
                </h4>
                <p style="color: rgba(255,255,255,0.85) !important; line-height: 1.6 !important; font-size: 0.9rem !important;"><i class="fa fa-envelope" style="margin-right: 8px;"></i> {% trans "Email" %}: info@django-jobs.com</p>
                <p style="color: rgba(255,255,255,0.85) !important; line-height: 1.6 !important; font-size: 0.9rem !important;"><i class="fa fa-phone" style="margin-right: 8px;"></i> {% trans "Phone" %}: +123 456 7890</p>
                <p style="color: rgba(255,255,255,0.85) !important; line-height: 1.6 !important; font-size: 0.9rem !important;"><i class="fa fa-map-marker" style="margin-right: 8px;"></i> {% trans "Location" %}: Addis Ababa, Ethiopia</p>
            </div>
            
            <!-- Quick Links Section -->
            <div class="col-lg-3 col-md-6 mb-4">
                <h4 style="font-size: 1.1rem !important; font-weight: 600 !important; margin-bottom: 20px !important; color: #ffffff !important; text-transform: uppercase !important; letter-spacing: 0.05em !important; position: relative !important; padding-bottom: 10px !important;">
                    {% trans "Quick Links" %}
                    <span style="position: absolute !important; left: 0 !important; bottom: 0 !important; width: 40px !important; height: 3px !important; background: #ffffff !important; border-radius: 2px !important;"></span>
                </h4>
                <a href="/" style="color: rgba(255,255,255,0.85) !important; text-decoration: none !important; display: block !important; margin-bottom: 10px !important; transition: all 0.3s ease !important;">{% trans "Home" %}</a>
                <a href="/jobs/" style="color: rgba(255,255,255,0.85) !important; text-decoration: none !important; display: block !important; margin-bottom: 10px !important; transition: all 0.3s ease !important;">{% trans "Jobs" %}</a>
                <a href="/{% get_current_language as LANGUAGE_CODE %}{{ LANGUAGE_CODE }}/about-us/" style="color: rgba(255,255,255,0.85) !important; text-decoration: none !important; display: block !important; margin-bottom: 10px !important; transition: all 0.3s ease !important;">{% trans "About Us" %}</a>
                <a href="#" style="color: rgba(255,255,255,0.85) !important; text-decoration: none !important; display: block !important; margin-bottom: 10px !important; transition: all 0.3s ease !important;">{% trans "Contact" %}</a>
            </div>
            
            <!-- Social Media Section -->
            <div class="col-lg-3 col-md-6 mb-4">
                <h4 style="font-size: 1.1rem !important; font-weight: 600 !important; margin-bottom: 20px !important; color: #ffffff !important; text-transform: uppercase !important; letter-spacing: 0.05em !important; position: relative !important; padding-bottom: 10px !important;">
                    {% trans "Follow Us" %}
                    <span style="position: absolute !important; left: 0 !important; bottom: 0 !important; width: 40px !important; height: 3px !important; background: #ffffff !important; border-radius: 2px !important;"></span>
                </h4>
                <div style="display: flex !important; gap: 15px !important;">
                    <a href="https://web.facebook.com/profile.php?id=100077897349623&sk=directory_personal_details" target="_blank" rel="noopener" title="Facebook" style="color: #1877F2 !important; font-size: 1.3rem !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; background: rgba(255,255,255,0.15) !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">
                        <i class="fab fa-facebook-f"></i>
                    </a>
                    <a href="https://linkedin.com/in/wubante-tilahun-776ab7377" target="_blank" rel="noopener" title="LinkedIn" style="color: #0A66C2 !important; font-size: 1.3rem !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; background: rgba(255,255,255,0.15) !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">
                        <i class="fab fa-linkedin-in"></i>
                    </a>
                    <a href="https://t.me/UOGwuba" target="_blank" rel="noopener" title="Telegram" style="color: #0088CC !important; font-size: 1.3rem !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; background: rgba(255,255,255,0.15) !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">
                        <i class="fab fa-telegram"></i>
                    </a>
                    <a href="https://wuba21.github.io" target="_blank" rel="noopener" title="GitHub" style="color: #f5f5f5 !important; font-size: 1.3rem !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; background: rgba(255,255,255,0.15) !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">
                        <i class="fab fa-github"></i>
                    </a>
                </div>
            </div>
        </div>
    </div>
    <div style="margin-top: 40px !important; padding: 20px 0 !important; border-top: 1px solid rgba(255,255,255,0.1) !important; background: rgba(0,0,0,0.1) !important;">
        <div class="container">
            <div class="row">
                <div class="col-md-12 text-center">
                    <p style="margin-bottom: 0 !important; text-align: center !important; font-size: 0.85rem !important; color: rgba(255,255,255,0.7) !important;">
                        &copy;{% now "Y" %} {% trans "Django-Jobs. All rights reserved." %}
                    </p>
                </div>
            </div>
        </div>
    </div>
</footer>
'''

# Replace footer
content = content[:footer_start] + new_footer + content[footer_end:]

# Ensure {% load i18n %} is present
if '{% load i18n %}' not in content:
    content = content.replace('{% load static %}', '{% load static i18n %}')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Footer completely rewritten with CORRECT Django i18n syntax!")
print("Now translations will work properly!")
