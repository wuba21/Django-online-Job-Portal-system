#!/usr/bin/env python
"""Add translation tags to footer."""
file_path = r"C:\Users\HP\Downloads\django-job-portal-master\django-job-portal-master\templates\base.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace static text with translation tags
replacements = [
    ('About Django-Jobs', '{% trans "About Django-Jobs" %}'),
    ('Contact Us', '{% trans "Contact Us" %}'),
    ('Quick Links', '{% trans "Quick Links" %}'),
    ('Follow Us', '{% trans "Follow Us" %}'),
    ('Home', '{% trans "Home" %}'),
    ('Jobs', '{% trans "Jobs" %}'),
    ('About Us', '{% trans "About Us" %}'),
    ('Contact', '{% trans "Contact" %}'),
    ('Your premier platform for connecting talented professionals with outstanding career opportunities.', 
     '{% trans "Your premier platform for connecting talented professionals with outstanding career opportunities. We simplify the job search and hiring process for both job seekers and employers." %}'),
    ('Email:', '{% trans "Email" %}:'),
    ('Phone:', '{% trans "Phone" %}:'),
    ('Location:', '{% trans "Location" %}:'),
    ('info@django-jobs.com', '{% trans "info@django-jobs.com" %}'),
    ('+123 456 7890', '{% trans "+123 456 7890" %}'),
    ('Addis Ababa, Ethiopia', '{% trans "Addis Ababa, Ethiopia" %}'),
    ('© 2026 Django-Jobs. All rights reserved.', '&copy;{% now "Y" %} {% trans "Django-Jobs. All rights reserved." %}'),
]

for old, new in replacements:
    content = content.replace(old, new)

# Add {% load i18n %} if not present
if '{% load i18n %}' not in content:
    content = content.replace('{% load static %}', '{% load static i18n %}')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Translation tags added to footer!")
print("Now footer text will translate when language is switched!")
