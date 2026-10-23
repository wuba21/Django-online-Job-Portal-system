from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from categories.models import Category
from jobsapp.models import (
    Applicant, ApplicantProfile, CandidateSkill, Company, Conversation, ChatMessage,
    Education, Job, Tag, WorkExperience
)
from django.core.cache import cache
from jobsapp.utils.recommendation import (
    calculate_job_match_score, get_recommended_jobs_for_user, invalidate_recommendation_cache,
    PureTfidfVectorizer
)

User = get_user_model()


class AIJobRecommendationTestCase(TestCase):
    def setUp(self):
        cache.clear()
        # 1. Create Employer User & Company
        self.employer_user = User.objects.create_user(
            email="employer@example.com",
            password="StrongPassword123!#",
            first_name="Tech",
            last_name="Employer",
            role="employer"
        )
        self.company = Company.objects.create(
            user=self.employer_user,
            name="Alpha Tech Solutions",
            description="Leading software engineering firm in Addis Ababa"
        )

        # 2. Create Candidate A (Software Engineer)
        self.candidate_a = User.objects.create_user(
            email="candidate.a@example.com",
            password="StrongPassword123!#",
            first_name="Abebe",
            last_name="Kebede",
            role="employee"
        )
        self.profile_a = ApplicantProfile.objects.create(
            user=self.candidate_a,
            title="Senior Python Django Developer",
            bio="Experienced full stack engineer specializing in Python, Django, PostgreSQL and REST APIs.",
            location="Addis Ababa"
        )
        CandidateSkill.objects.create(user=self.candidate_a, name="Python", level="expert")
        CandidateSkill.objects.create(user=self.candidate_a, name="Django", level="expert")
        CandidateSkill.objects.create(user=self.candidate_a, name="PostgreSQL", level="intermediate")
        Education.objects.create(
            user=self.candidate_a,
            institution="Addis Ababa University",
            degree="BSc Computer Science",
            field_of_study="Software Engineering"
        )
        WorkExperience.objects.create(
            user=self.candidate_a,
            title="Software Developer",
            company="Ethio Fintech",
            description="Developed backend microservices using Python and Django."
        )

        # 3. Create Candidate B (Accountant)
        self.candidate_b = User.objects.create_user(
            email="candidate.b@example.com",
            password="StrongPassword123!#",
            first_name="Chaltu",
            last_name="Tadesse",
            role="employee"
        )
        self.profile_b = ApplicantProfile.objects.create(
            user=self.candidate_b,
            title="Senior Accountant",
            bio="Certified accountant with expertise in financial reporting, tax preparation and auditing.",
            location="Addis Ababa"
        )
        CandidateSkill.objects.create(user=self.candidate_b, name="Accounting", level="expert")
        CandidateSkill.objects.create(user=self.candidate_b, name="Auditing", level="expert")
        CandidateSkill.objects.create(user=self.candidate_b, name="Tax Preparation", level="intermediate")

        # 4. Create Tags & Categories
        self.cat_tech = Category.objects.create(name="Software Engineering")
        self.cat_finance = Category.objects.create(name="Accounting & Finance")

        self.tag_python = Tag.objects.create(name="Python")
        self.tag_django = Tag.objects.create(name="Django")
        self.tag_finance = Tag.objects.create(name="Accounting")

        # 5. Create Active Jobs
        self.job_python = Job.objects.create(
            user=self.employer_user,
            company=self.company,
            title="Full Stack Python Django Engineer",
            category=self.cat_tech.name,
            location="Addis Ababa",
            salary=45000,
            status="approved",
            filled=False,
            work_mode="on-site",
            description="We are seeking an experienced Python Django engineer to build enterprise cloud applications.",
            last_date=timezone.now() + timedelta(days=20)
        )
        self.job_python.tags.add(self.tag_python, self.tag_django)

        self.job_accounting = Job.objects.create(
            user=self.employer_user,
            company=self.company,
            title="Senior Financial Accountant",
            category=self.cat_finance.name,
            location="Addis Ababa",
            salary=35000,
            status="approved",
            filled=False,
            work_mode="on-site",
            description="Seeking a dedicated accountant to lead financial audit, payroll and tax reporting.",
            last_date=timezone.now() + timedelta(days=20)
        )
        self.job_accounting.tags.add(self.tag_finance)

        # 6. Create Expired Job
        self.job_expired = Job.objects.create(
            user=self.employer_user,
            company=self.company,
            title="Expired Python Job",
            category=self.cat_tech.name,
            location="Addis Ababa",
            status="approved",
            filled=False,
            description="Expired position",
            last_date=timezone.now() - timedelta(days=5)
        )

        # 7. Create Filled Job
        self.job_filled = Job.objects.create(
            user=self.employer_user,
            company=self.company,
            title="Filled Python Position",
            category=self.cat_tech.name,
            location="Addis Ababa",
            status="approved",
            filled=True,
            description="Already filled",
            last_date=timezone.now() + timedelta(days=10)
        )

    def test_pure_tfidf_vectorizer_similarity(self):
        """Test the pure TF-IDF vectorizer and cosine similarity calculation."""
        doc1 = "python django developer web postgresql backend"
        doc2 = "senior backend engineer python django rest api"
        doc3 = "accounting finance auditor tax payroll balance sheet"

        vectorizer = PureTfidfVectorizer()
        vecs = vectorizer.fit_transform([doc1, doc2, doc3])
        self.assertEqual(len(vecs), 3)

        sim_tech = PureTfidfVectorizer.cosine_similarity(vecs[0][0], vecs[0][1], vecs[1][0], vecs[1][1])
        sim_diff = PureTfidfVectorizer.cosine_similarity(vecs[0][0], vecs[0][1], vecs[2][0], vecs[2][1])

        self.assertGreater(sim_tech, sim_diff)
        self.assertGreater(sim_tech, 0.25)
        self.assertAlmostEqual(sim_diff, 0.0, places=2)

    def test_recommendation_ranking_and_personalization(self):
        """Test that candidate A receives the Python job ranked highest, while candidate B receives Accounting job."""
        recs_a = get_recommended_jobs_for_user(self.candidate_a, limit=10)
        self.assertTrue(len(recs_a) >= 1)
        top_job_a = recs_a[0]["job"]
        self.assertEqual(top_job_a.id, self.job_python.id)
        self.assertGreaterEqual(recs_a[0]["match_score"], 65)

        recs_b = get_recommended_jobs_for_user(self.candidate_b, limit=10)
        self.assertTrue(len(recs_b) >= 1)
        top_job_b = recs_b[0]["job"]
        self.assertEqual(top_job_b.id, self.job_accounting.id)
        self.assertGreaterEqual(recs_b[0]["match_score"], 65)

    def test_expired_and_filled_jobs_excluded(self):
        """Test that expired and filled jobs are never recommended to applicants."""
        recs = get_recommended_jobs_for_user(self.candidate_a, limit=20)
        rec_job_ids = [r["job"].id for r in recs]
        self.assertNotIn(self.job_expired.id, rec_job_ids)
        self.assertNotIn(self.job_filled.id, rec_job_ids)

    def test_already_applied_jobs_excluded(self):
        """Test that once an applicant applies for a job, it disappears from their recommendations."""
        # Initial check: job_python is in recommendations
        recs_initial = get_recommended_jobs_for_user(self.candidate_a, limit=10)
        initial_job_ids = [r["job"].id for r in recs_initial]
        self.assertIn(self.job_python.id, initial_job_ids)

        # Candidate applies to job_python
        Applicant.objects.create(user=self.candidate_a, job=self.job_python)
        invalidate_recommendation_cache(self.candidate_a.id)

        # New recommendations must NOT include job_python
        recs_after = get_recommended_jobs_for_user(self.candidate_a, limit=10)
        after_job_ids = [r["job"].id for r in recs_after]
        self.assertNotIn(self.job_python.id, after_job_ids)

    def test_missing_profile_handled_gracefully(self):
        """Test that an applicant with no profile or skills receives recommendations without errors."""
        empty_candidate = User.objects.create_user(
            email="empty.candidate@example.com",
            password="StrongPassword123!#",
            first_name="New",
            last_name="User",
            role="employee"
        )
        recs = get_recommended_jobs_for_user(empty_candidate, limit=10)
        self.assertIsInstance(recs, list)

    def test_recommended_jobs_list_view(self):
        """Test accessing the /recommended/ page as an authenticated employee."""
        self.client.login(email="candidate.a@example.com", password="StrongPassword123!#")
        response = self.client.get(reverse("jobs:recommended-jobs"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recommended Jobs For You")
        self.assertContains(response, self.job_python.title)

    def test_real_time_messages_poll_endpoint(self):
        """Test the real-time messages polling endpoint."""
        conv = Conversation.objects.create(
            employer=self.employer_user,
            candidate=self.candidate_a,
            job=self.job_python
        )
        msg1 = ChatMessage.objects.create(
            conversation=conv,
            sender=self.employer_user,
            message="Hello Abebe, we received your application."
        )

        self.client.login(email="candidate.a@example.com", password="StrongPassword123!#")
        poll_url = reverse("jobs:poll-messages", kwargs={"conversation_id": conv.id})

        # Fetch messages after id 0
        response = self.client.get(f"{poll_url}?last_id=0")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["messages"]), 1)
        self.assertEqual(data["messages"][0]["message"], msg1.message)

        # Fetch messages after msg1.id -> should return 0
        response_empty = self.client.get(f"{poll_url}?last_id={msg1.id}")
        self.assertEqual(response_empty.status_code, 200)
        self.assertEqual(len(response_empty.json()["messages"]), 0)
