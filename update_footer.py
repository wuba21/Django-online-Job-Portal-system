#!/usr/bin/env python
"""Update footer to remove GitHub badges."""
file_path = r"C:\Users\HP\Downloads\django-job-portal-master\django-job-portal-master\templates\base.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the footer copyright section
old_footer = '''    <div class="footer__copyright">
        <div class="container">
            <div class="row">
                <div class="col-md-4 text-md-left text-center">
                    <p>&copy;{% now "Y" %} django-jobs!</p>
                </div>
                <div class="col-md-8 text-center text-md-right github-buttons">
                    <a href="https://github.com/manjurulhoque/django-job-portal" target="_blank" rel="noopener">
                        <img alt="stars"
                             src="https://img.shields.io/github/stars/manjurulhoque/django-job-portal?style=social"/>
                    </a>
                    <a href="https://github.com/manjurulhoque/django-job-portal" target="_blank" rel="noopener">
                        <img alt="forks"
                             src="https://img.shields.io/github/forks/manjurulhoque/django-job-portal?style=social"/>
                    </a>
                    <a href="https://github.com/manjurulhoque/django-job-portal/issues" target="_blank" rel="noopener">
                        <img alt="issues"
                             src="https://img.shields.io/github/issues/manjurulhoque/django-job-portal?style=social"/>
                    </a>
                    <a href="https://github.com/manjurulhoque/django-job-portal/#contributors-" target="_blank"
                       rel="noopener">
                        <img alt="translation"
                             src="https://img.shields.io/badge/all_contributors-18-orange.svg?style=flat-square"/>
                    </a>
                </div>
            </div>
        </div>
    </div>'''

new_footer = '''    <div class="footer__copyright">
        <div class="container">
            <div class="row">
                <div class="col-md-12 text-center">
                    <p>&copy;{% now "Y" %} django-jobs!</p>
                </div>
            </div>
        </div>
    </div>'''

content = content.replace(old_footer, new_footer)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Footer updated successfully!")
