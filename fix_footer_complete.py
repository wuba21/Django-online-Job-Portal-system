#!/usr/bin/env python
"""Completely rewrite footer with proper social media list."""
file_path = r"C:\Users\HP\Downloads\django-job-portal-master\django-job-portal-master\templates\base.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the footer and replace the entire thing
footer_start = content.find('<footer class="footer">')
footer_end = content.find('</footer>') + len('</footer>')

# New complete footer HTML
new_footer = '''<footer class="footer">
    <div class="container">
        <div class="row">
            <!-- About Section -->
            <div class="col-lg-3 col-md-6 mb-4">
                <h4 class="h5">{% trans "About django-jobs" %}</h4>
                <p>{% trans "Your premier platform for connecting talented professionals with outstanding career opportunities. We simplify the job search and hiring process for both job seekers and employers." %}</p>
            </div>
            
            <!-- Contact Section -->
            <div class="col-lg-3 col-md-6 mb-4">
                <h4 class="h5">{% trans "Contact Us" %}</h4>
                <p><i class="fa fa-envelope"></i> {% trans "Email" %}: info@django-jobs.com</p>
                <p><i class="fa fa-phone"></i> {% trans "Phone" %}: +123 456 7890</p>
                <p><i class="fa fa-map-marker"></i> {% trans "Location" %}: Addis Ababa, Ethiopia</p>
            </div>
            
            <!-- Quick Links Section -->
            <div class="col-lg-3 col-md-6 mb-4">
                <h4 class="h5">{% trans "Quick Links" %}</h4>
                <a href="{% url 'jobs:home' %}">{% trans "Home" %}</a>
                <a href="{% url 'jobs:jobs' %}">{% trans "Jobs" %}</a>
                <a href="/{% get_current_language as LANGUAGE_CODE %}{{ LANGUAGE_CODE }}/about-us/">{% trans "About Us" %}</a>
                <a href="#">{% trans "Contact" %}</a>
            </div>
            
            <!-- Social Media Section -->
            <div class="col-lg-3 col-md-6 mb-4">
                <h4 class="h5">{% trans "Follow Us" %}</h4>
                <div class="social-links">
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
                </div>
                <div class="newsletter mt-4">
                    <h4 class="h5">{% trans "Newsletter" %}</h4>
                    <div class="newsletter-input">
                        <input type="email" placeholder="{% trans "Enter your email" %}" class="form-control">
                        <button class="btn">{% trans "Subscribe" %}</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="footer__copyright">
        <div class="container">
            <div class="row">
                <div class="col-md-12 text-center">
                    <p>&copy;{% now "Y" %} Django-Jobs. {% trans "All rights reserved." %}</p>
                </div>
            </div>
        </div>
    </div>
</footer>'''

content = content[:footer_start] + new_footer + content[footer_end:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Footer completely rewritten with proper social media list!")
