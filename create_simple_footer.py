#!/usr/bin/env python
"""Create a simple, clean footer that will definitely be visible."""
file_path = r"C:\Users\HP\Downloads\django-job-portal-master\django-job-portal-master\templates\base.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the footer and replace it completely
footer_start = content.find('<footer')
if footer_start == -1:
    print("Footer not found!")
    exit()

# Find the end of footer
footer_end = content.find('</footer>') + len('</footer>')

# Simple, clean footer with inline styles
new_footer = '''<footer style="background: linear-gradient(135deg, #1e3c72 0%, #2b4d9 100%) !important; color: #ffffff !important; padding: 60px 0 0 0 !important; margin-top: 0 !important;">
    <div class="container">
        <div class="row">
            <!-- About Section -->
            <div class="col-lg-3 col-md-6 mb-4">
                <h4 style="font-size: 1.1rem !important; font-weight: 600 !important; margin-bottom: 20px !important; color: #ffffff !important; text-transform: uppercase !important;">About django-jobs</h4>
                <p style="color: rgba(255,255,255,0.85) !important; line-height: 1.6 !important; font-size: 0.9rem !important;">Your premier platform for connecting talented professionals with outstanding career opportunities. We simplify the job search and hiring process for both job seekers and employers.</p>
            </div>
            
            <!-- Contact Section -->
            <div class="col-lg-3 col-md-6 mb-4">
                <h4 style="font-size: 1.1rem !important; font-weight: 600 !important; margin-bottom: 20px !important; color: #ffffff !important; text-transform: uppercase !important;">Contact Us</h4>
                <p style="color: rgba(255,255,255,0.85) !important;"><i class="fa fa-envelope"></i> Email: info@django-jobs.com</p>
                <p style="color: rgba(255,255,255,0.85) !important;"><i class="fa fa-phone"></i> Phone: +123 456 7890</p>
                <p style="color: rgba(255,255,255,0.85) !important;"><i class="fa fa-map-marker"></i> Location: Addis Ababa, Ethiopia</p>
            </div>
            
            <!-- Quick Links Section -->
            <div class="col-lg-3 col-md-6 mb-4">
                <h4 style="font-size: 1.1rem !important; font-weight: 600 !important; margin-bottom: 20px !important; color: #ffffff !important; text-transform: uppercase !important;">Quick Links</h4>
                <a href="/" style="color: rgba(255,255,255,0.85) !important; text-decoration: none !important; display: block !important; margin-bottom: 10px !important;">Home</a>
                <a href="/jobs/" style="color: rgba(255,255,255,0.85) !important; text-decoration: none !important; display: block !important; margin-bottom: 10px !important;">Jobs</a>
                <a href="/about-us/" style="color: rgba(255,255,255,0.85) !important; text-decoration: none !important; display: block !important; margin-bottom: 10px !important;">About Us</a>
                <a href="#" style="color: rgba(255,255,255,0.85) !important; text-decoration: none !important; display: block !important; margin-bottom: 10px !important;">Contact</a>
            </div>
            
            <!-- Social Media Section -->
            <div class="col-lg-3 col-md-6 mb-4">
                <h4 style="font-size: 1.1rem !important; font-weight: 600 !important; margin-bottom: 20px !important; color: #ffffff !important; text-transform: uppercase !important;">Follow Us</h4>
                <div style="display: flex !important; gap: 15px !important;">
                    <a href="https://web.facebook.com/profile.php?id=100077897349623&sk=directory_personal_details" target="_blank" rel="noopener" title="Facebook" style="color: #ffffff !important; font-size: 1.3rem !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; background: rgba(255,255,255,0.15) !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">
                        <i class="fab fa-facebook-f"></i>
                    </a>
                    <a href="https://linkedin.com/in/wubante-tilahun-776ab7377" target="_blank" rel="noopener" title="LinkedIn" style="color: #ffffff !important; font-size: 1.3rem !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; background: rgba(255,255,255,0.15) !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">
                        <i class="fab fa-linkedin-in"></i>
                    </a>
                    <a href="https://t.me/UOGwuba" target="_blank" rel="noopener" title="Telegram" style="color: #ffffff !important; font-size: 1.3rem !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; background: rgba(255,255,255,0.15) !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">
                        <i class="fab fa-telegram"></i>
                    </a>
                    <a href="https://wuba21.github.io" target="_blank" rel="noopener" title="GitHub" style="color: #ffffff !important; font-size: 1.3rem !important; width: 45px !important; height: 45px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; background: rgba(255,255,255,0.15) !important; border-radius: 50% !important; text-decoration: none !important; transition: all 0.3s ease !important;">
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
                    <p style="margin-bottom: 0 !important; text-align: center !important; font-size: 0.85rem !important; color: rgba(255,255,255,0.7) !important;">&copy; 2026 Django-Jobs. All rights reserved.</p>
                </div>
            </div>
        </div>
    </div>
</footer>'''

content = content[:footer_start] + new_footer + content[footer_end:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Simple, clean footer created with inline styles!")
