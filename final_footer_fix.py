#!/usr/bin/env python
file_path = r"C:\Users\HP\Downloads\django-job-portal-master\django-job-portal-master\templates\base.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

footer_start = content.find('<footer')
if footer_start == -1:
    print("Footer not found!")
    exit()

footer_end = content.find('</footer>')
if footer_end == -1:
    print("Footer end not found!")
    exit()
footer_end += len('</footer>')

new_footer = '''
<footer style="background: linear-gradient(135deg, #1e3c72 0%, #2b4d9 100%); color: #ffffff; padding: 60px 0 0 0; margin-top: 0;">
    <div class="container">
        <div class="row">
            <div class="col-lg-3 col-md-6 mb-4">
                <h4 style="font-size: 1.1rem; font-weight: 600; margin-bottom: 20px; color: #ffffff; text-transform: uppercase; letter-spacing: 0.05em; position: relative; padding-bottom: 10px;">
                    About Django-Jobs
                    <span style="position: absolute; left: 0; bottom: 0; width: 40px; height: 3px; background: #ffffff; border-radius: 2px;"></span>
                </h4>
                <p style="color: rgba(255,255,255,0.85); line-height: 1.6; font-size: 0.9rem;">
                    Your premier platform for connecting talented professionals with outstanding career opportunities.
                </p>
            </div>
            
            <div class="col-lg-3 col-md-6 mb-4">
                <h4 style="font-size: 1.1rem; font-weight: 600; margin-bottom: 20px; color: #ffffff; text-transform: uppercase; letter-spacing: 0.05em; position: relative; padding-bottom: 10px;">
                    Contact Us
                    <span style="position: absolute; left: 0; bottom: 0; width: 40px; height: 3px; background: #ffffff; border-radius: 2px;"></span>
                </h4>
                <p style="color: rgba(255,255,255,0.85); line-height: 1.6; font-size: 0.9rem;">
                    <i class="fa fa-envelope" style="margin-right: 8px;"></i> Email: info@django-jobs.com
                </p>
                <p style="color: rgba(255,255,255,0.85); line-height: 1.6; font-size: 0.9rem;">
                    <i class="fa fa-phone" style="margin-right: 8px;"></i> Phone: +123 456 7890
                </p>
                <p style="color: rgba(255,255,255,0.85); line-height: 1.6; font-size: 0.9rem;">
                    <i class="fa fa-map-marker" style="margin-right: 8px;"></i> Location: Addis Ababa, Ethiopia
                </p>
            </div>
            
            <div class="col-lg-3 col-md-6 mb-4">
                <h4 style="font-size: 1.1rem; font-weight: 600; margin-bottom: 20px; color: #ffffff; text-transform: uppercase; letter-spacing: 0.05em; position: relative; padding-bottom: 10px;">
                    Quick Links
                    <span style="position: absolute; left: 0; bottom: 0; width: 40px; height: 3px; background: #ffffff; border-radius: 2px;"></span>
                </h4>
                <a href="/" style="color: rgba(255,255,255,0.85); text-decoration: none; display: block; margin-bottom: 10px; transition: all 0.3s ease;">Home</a>
                <a href="/jobs/" style="color: rgba(255,255,255,0.85); text-decoration: none; display: block; margin-bottom: 10px; transition: all 0.3s ease;">Jobs</a>
                <a href="/about-us/" style="color: rgba(255,255,255,0.85); text-decoration: none; display: block; margin-bottom: 10px; transition: all 0.3s ease;">About Us</a>
                <a href="#" style="color: rgba(255,255,255,0.85); text-decoration: none; display: block; margin-bottom: 10px; transition: all 0.3s ease;">Contact</a>
            </div>
            
            <div class="col-lg-3 col-md-6 mb-4">
                <h4 style="font-size: 1.1rem; font-weight: 600; margin-bottom: 20px; color: #ffffff; text-transform: uppercase; letter-spacing: 0.05em; position: relative; padding-bottom: 10px;">
                    Follow Us
                    <span style="position: absolute; left: 0; bottom: 0; width: 40px; height: 3px; background: #ffffff; border-radius: 2px;"></span>
                </h4>
                <div style="display: flex; gap: 15px;">
                    <a href="https://web.facebook.com/profile.php?id=100077897349623&sk=directory_personal_details" target="_blank" rel="noopener" title="Facebook" style="color: #1877F2; font-size: 1.3rem; width: 45px; height: 45px; display: inline-flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.15); border-radius: 50%; text-decoration: none; transition: all 0.3s ease;">
                        <i class="fab fa-facebook-f"></i>
                    </a>
                    <a href="https://linkedin.com/in/wubante-tilahun-776ab7377" target="_blank" rel="noopener" title="LinkedIn" style="color: #0A66C2; font-size: 1.3rem; width: 45px; height: 45px; display: inline-flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.15); border-radius: 50%; text-decoration: none; transition: all 0.3s ease;">
                        <i class="fab fa-linkedin-in"></i>
                    </a>
                    <a href="https://t.me/UOGwuba" target="_blank" rel="noopener" title="Telegram" style="color: #0088CC; font-size: 1.3rem; width: 45px; height: 45px; display: inline-flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.15); border-radius: 50%; text-decoration: none; transition: all 0.3s ease;">
                        <i class="fab fa-telegram"></i>
                    </a>
                    <a href="https://wuba21.github.io" target="_blank" rel="noopener" title="GitHub" style="color: #f5f5f5; font-size: 1.3rem; width: 45px; height: 45px; display: inline-flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.15); border-radius: 50%; text-decoration: none; transition: all 0.3s ease;">
                        <i class="fab fa-github"></i>
                    </a>
                </div>
            </div>
        </div>
    </div>
    <div style="margin-top: 40px; padding: 20px 0; border-top: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.1);">
        <div class="container">
            <div class="row">
                <div class="col-md-12 text-center">
                    <p style="margin-bottom: 0; text-align: center; font-size: 0.85rem; color: rgba(255,255,255,0.7);">
                        &copy; 2026 Django-Jobs. All rights reserved.
                    </p>
                </div>
            </div>
        </div>
    </div>
</footer>
'''

content = content[:footer_start] + new_footer + content[footer_end:]

# Add Font Awesome if not present
if 'font-awesome' not in content.lower():
    content = content.replace('</head>', '    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">\n</head>')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Footer completely rewritten with clean design!")
print("Brand colors: Facebook=#1877F2, LinkedIn=#0A66C2, Telegram=#0088CC, GitHub=#f5f5f5")
