from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from accounts.models import Company, CompanyReview
from categories.models import Category
from jobsapp.models import CandidateSkill, ChatMessage, Conversation, Education, Job, JobAlert

User = get_user_model()


class AdvancedPortalFeaturesTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Employer & Company
        self.employer_user = User.objects.create_user(
            email="employer.test@gmail.com",
            password="StrongPassword123!#",
            first_name="Tech",
            last_name="Ethiopia",
            role="employer"
        )
        self.company = Company.objects.create(
            user=self.employer_user,
            name="Tech Ethiopia PLC",
            location="Addis Ababa",
            industry="Information Technology & Software"
        )

        # Create Candidate
        self.candidate_user = User.objects.create_user(
            email="candidate.test@gmail.com",
            password="StrongPassword123!#",
            first_name="Abebe",
            last_name="Kebede",
            role="employee"
        )

        # Create Category & Job
        self.category = Category.objects.create(name="Software Engineering")
        from django.utils import timezone
        self.job = Job.objects.create(
            user=self.employer_user,
            company=self.company,
            title="Senior Python Django Developer",
            category=self.category,
            location="Addis Ababa",
            salary=45000,
            status="approved",
            last_date=timezone.now() + timezone.timedelta(days=30)
        )

    def test_company_reviews_and_ratings(self):
        """Test submitting reviews, computing average ratings and review counts."""
        self.client.login(email="candidate.test@gmail.com", password="StrongPassword123!#")

        # Submit review
        review_url = reverse("jobs:add-company-review", kwargs={"company_id": self.company.id})
        response = self.client.post(review_url, {
            "rating": 5,
            "title": "Outstanding work environment",
            "review_text": "Great management, flexible working hours and competitive compensation.",
            "pros": "High salaries, health insurance",
            "cons": "Challenging deadlines"
        })
        self.assertEqual(response.status_code, 302)

        # Verify DB record
        review = CompanyReview.objects.get(company=self.company, user=self.candidate_user)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.title, "Outstanding work environment")
        self.assertEqual(self.company.average_rating, 5.0)
        self.assertEqual(self.company.reviews_count, 1)

        # Company owner cannot review their own company
        self.client.logout()
        self.client.login(email="employer.test@gmail.com", password="StrongPassword123!#")
        response_owner = self.client.post(review_url, {
            "rating": 5,
            "title": "Self review",
            "review_text": "We are the best!"
        })
        self.assertEqual(CompanyReview.objects.filter(company=self.company).count(), 1)

    def test_direct_messaging_conversation_and_chat(self):
        """Test conversation creation and sending 2-way chat messages between employer and candidate."""
        self.client.login(email="employer.test@gmail.com", password="StrongPassword123!#")

        # Start conversation
        start_url = reverse("jobs:start-conversation", kwargs={"candidate_id": self.candidate_user.id})
        response = self.client.get(f"{start_url}?job_id={self.job.id}")
        self.assertEqual(response.status_code, 302)

        conv = Conversation.objects.get(employer=self.employer_user, candidate=self.candidate_user)
        self.assertEqual(conv.job, self.job)

        # Send a message
        inbox_url = reverse("jobs:inbox")
        post_response = self.client.post(inbox_url, {
            "conversation_id": conv.id,
            "message": "Hello Abebe, we loved your CV and would like to schedule an interview!"
        })
        self.assertEqual(post_response.status_code, 302)

        msg = ChatMessage.objects.filter(conversation=conv).first()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.sender, self.employer_user)
        self.assertIn("interview", msg.message)

        # Candidate checks inbox
        self.client.logout()
        self.client.login(email="candidate.test@gmail.com", password="StrongPassword123!#")
        inbox_get = self.client.get(inbox_url)
        self.assertEqual(inbox_get.status_code, 200)

    def test_ai_resume_auto_profile_parser(self):
        """Test extracting skills, title, and education from resume text into candidate profile."""
        self.client.login(email="candidate.test@gmail.com", password="StrongPassword123!#")

        resume_text = """
        Abebe Kebede
        Full Stack Developer
        Addis Ababa, Ethiopia | Phone: +251911223344
        Summary: Experienced software engineer building scalable web applications.
        Skills: Python, Django, React, PostgreSQL, Docker, Git, REST API.
        Education: Bachelor of Science in Computer Science from Addis Ababa University (2020-2024).
        """

        url = reverse("jobs:ai-parse-resume")
        response = self.client.post(url, {"resume_text": resume_text})
        self.assertEqual(response.status_code, 302)

        # Verify candidate profile got auto-populated
        profile = self.candidate_user.applicant_profile
        self.assertEqual(profile.title, "Full Stack Developer")
        self.assertEqual(profile.location, "Addis Ababa")

        # Verify skills got extracted
        user_skills = list(CandidateSkill.objects.filter(user=self.candidate_user).values_list("name", flat=True))
        self.assertIn("Python", user_skills)
        self.assertIn("Django", user_skills)
        self.assertIn("React", user_skills)
        self.assertIn("Docker", user_skills)

        # Verify education was created
        edu = Education.objects.filter(user=self.candidate_user).first()
        self.assertIsNotNone(edu)
        self.assertEqual(edu.degree, "Bachelor's Degree")

    def test_telegram_mini_app_portal(self):
        """Test Telegram Mini App mobile portal returns 200 OK with jobs."""
        url = reverse("jobs:telegram-webapp")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ethio Job Portal")
        self.assertContains(response, "Senior Python Django Developer")

    def test_real_time_chat_live_status_and_conversations_sync(self):
        """Test dynamic live status polling and conversation sync APIs for zero-refresh updates."""
        # Create conversation and unread message for candidate
        conv = Conversation.objects.create(employer=self.employer_user, candidate=self.candidate_user, job=self.job)
        ChatMessage.objects.create(
            conversation=conv,
            sender=self.employer_user,
            message="Hey Abebe, are you available tomorrow?"
        )

        # Log in as candidate
        self.client.login(email="candidate.test@gmail.com", password="StrongPassword123!#")

        # 1. Live status heartbeat API
        status_url = reverse("jobs:live-chat-status")
        res_status = self.client.get(status_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res_status.status_code, 200)
        data_status = res_status.json()
        self.assertEqual(data_status["status"], "success")
        self.assertEqual(data_status["unread_messages"], 1)

        # 2. Conversations sync API (updates left inbox pane)
        sync_url = reverse("jobs:conversations-sync")
        res_sync = self.client.get(sync_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res_sync.status_code, 200)
        data_sync = res_sync.json()
        self.assertEqual(data_sync["status"], "success")
        self.assertEqual(len(data_sync["conversations"]), 1)
        c_item = data_sync["conversations"][0]
        self.assertEqual(c_item["id"], conv.id)
        self.assertEqual(c_item["unread_count"], 1)
        self.assertIn("Hey Abebe", c_item["last_message"])
        self.assertFalse(c_item["is_me"])

    def test_job_save_or_check_does_not_auto_broadcast_to_telegram(self):
        """Verify that creating, checking, or approving a job does NOT automatically broadcast to Telegram."""
        from unittest.mock import patch
        from jobsapp.views.admin_dashboard import approve_job
        from django.test import RequestFactory
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.utils import timezone

        superuser = User.objects.create_superuser(
            email="admin.check@test.com",
            password="AdminPassword123!#",
            first_name="Super",
            last_name="Admin"
        )

        with patch("jobsapp.utils.telegram.broadcast_job_to_telegram") as mock_broadcast:
            # 1. Save new job
            new_job = Job.objects.create(
                user=self.employer_user,
                title="Frontend Vue Developer",
                category=self.category,
                location="Addis Ababa",
                salary=35000,
                status="approved",
                last_date=timezone.now() + timezone.timedelta(days=30)
            )
            # Ensure mock was NOT called
            self.assertFalse(mock_broadcast.called, "broadcast_job_to_telegram should not be called automatically on Job save!")

            # 2. Admin approves job
            factory = RequestFactory()
            req = factory.get(f"/platform-admin/approve-job/{new_job.id}/")
            req.user = superuser
            setattr(req, "session", "session")
            messages_storage = FallbackStorage(req)
            setattr(req, "_messages", messages_storage)

            approve_job(req, new_job.id)
            self.assertFalse(mock_broadcast.called, "broadcast_job_to_telegram should not be called automatically on approve_job!")

    def test_job_application_requires_complete_profile_and_cv(self):
        """Test that applying for a job verifies all required information (name, phone, email, gender, location, title, experience, skills, CV) before allowing submission."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from jobsapp.models import Applicant, ApplicantProfile, CandidateSkill, WorkExperience

        # Create incomplete candidate (missing everything)
        incomplete_user = User.objects.create_user(
            email="incomplete.applicant@test.com",
            password="StrongPassword123!#",
            first_name="",
            last_name="",
            role="employee"
        )
        self.client.login(email="incomplete.applicant@test.com", password="StrongPassword123!#")

        apply_url = reverse("jobs:apply-job", kwargs={"job_id": self.job.id})
        res = self.client.post(apply_url, {})
        self.assertEqual(res.status_code, 302)
        # Verify no applicant record was created
        self.assertFalse(Applicant.objects.filter(user=incomplete_user, job=self.job).exists())

        # Now fulfill ALL 8 required items
        incomplete_user.first_name = "Almaz"
        incomplete_user.last_name = "Ayana"
        incomplete_user.phone_number = "+251911002233"
        incomplete_user.gender = "female"
        incomplete_user.save()

        profile, _ = ApplicantProfile.objects.get_or_create(user=incomplete_user)
        profile.title = "Software Engineer"
        profile.location = "Addis Ababa"
        profile.save()

        CandidateSkill.objects.create(user=incomplete_user, name="Python", level="expert")

        # Add work experience
        from datetime import date
        WorkExperience.objects.create(
            user=incomplete_user,
            title="Junior Developer",
            company="Tech Corp",
            is_current=True,
            start_date=date.today()
        )

        # Create a realistic CV content that passes AI verification
        cv_content = b"""%PDF-1.4
        ALMAZ AYANA
        Software Engineer
        Email: almaz.ayana@test.com
        Phone: +251911002233
        Address: Addis Ababa, Ethiopia

        PROFESSIONAL SUMMARY
        Experienced software engineer with expertise in Python, Django, and web development.
        Strong background in building scalable applications and RESTful APIs.

        WORK EXPERIENCE
        Junior Developer at Tech Corp (2023 - Present)
        - Developed and maintained web applications using Python and Django framework
        - Implemented RESTful APIs for mobile application backend services
        - Collaborated with cross-functional teams to deliver quality software solutions
        - Participated in code reviews and improved code quality standards

        EDUCATION
        Bachelor of Science in Computer Science
        Addis Ababa University, 2019-2023
        Graduated with distinction in software engineering track

        SKILLS
        Python, Django, JavaScript, React, SQL, PostgreSQL, Git, REST API, Docker
        Communication, Leadership, Project Management, Problem Solving

        CERTIFICATIONS
        AWS Certified Cloud Practitioner
        Google IT Automation with Python Professional Certificate
        """
        fake_cv = SimpleUploadedFile("my_resume.pdf", cv_content, content_type="application/pdf")
        res_success = self.client.post(apply_url, {"cv": fake_cv, "comment": "I meet all criteria!"})
        self.assertEqual(res_success.status_code, 302)

        # Verify applicant record was created and CV attached
        app = Applicant.objects.filter(user=incomplete_user, job=self.job).first()
        self.assertIsNotNone(app)
        self.assertTrue(bool(app.cv))
        self.assertEqual(app.comment, "I meet all criteria!")

