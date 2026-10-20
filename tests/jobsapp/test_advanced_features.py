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
