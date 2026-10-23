import logging
import math
import re
from collections import Counter
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

# Standard English Stopwords for text normalization
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can",
    "cannot", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", "himself",
    "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "me", "more", "most", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "she", "should", "so", "some", "such", "than", "that", "the",
    "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this", "those", "through",
    "to", "too", "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself", "yourselves"
}


def tokenize(text):
    """Tokenize and clean text into normalized unigram and bigram tokens."""
    if not text:
        return []
    words = re.findall(r"\b[a-zA-Z0-9+#.-]{2,}\b", text.lower())
    tokens = [w for w in words if w not in STOPWORDS]
    return tokens


class PureTfidfVectorizer:
    """
    Lightweight, high-performance TF-IDF Vectorizer and Cosine Similarity engine.
    Implements sublinear TF scaling (1 + log(tf)) and smooth IDF with L2 normalization.
    Requires no external dependencies, making it 100% reliable across all hosting environments.
    """

    def __init__(self):
        self.vocabulary = {}
        self.idf_ = {}
        self.num_docs = 0

    def fit_transform(self, documents):
        """Fit vocabulary and compute IDF over corpus, returning normalized vectors."""
        self.num_docs = len(documents)
        tokenized_docs = [tokenize(doc) for doc in documents]
        doc_counters = [Counter(toks) for toks in tokenized_docs]

        all_words = set(w for counter in doc_counters for w in counter)
        df = {w: sum(1 for counter in doc_counters if w in counter) for w in all_words}
        # Smooth IDF: log((1 + N) / (1 + df)) + 1.0
        self.idf_ = {w: math.log((1 + self.num_docs) / (1 + df[w])) + 1.0 for w in all_words}

        vectors = []
        for counter in doc_counters:
            vec = {}
            for w, count in counter.items():
                if count > 0:
                    # Sublinear TF scaling
                    vec[w] = (1.0 + math.log(count)) * self.idf_[w]
            norm = math.sqrt(sum(v * v for v in vec.values()))
            vectors.append((vec, norm))
        return vectors

    @staticmethod
    def cosine_similarity(vec_a, norm_a, vec_b, norm_b):
        """Calculates cosine similarity between two sparse vector representations."""
        if norm_a == 0 or norm_b == 0:
            return 0.0
        # Iterate over smaller vector for performance
        if len(vec_a) > len(vec_b):
            vec_a, vec_b = vec_b, vec_a
        dot = sum(val * vec_b[w] for w, val in vec_a.items() if w in vec_b)
        return dot / (norm_a * norm_b)


def build_applicant_profile_text(user, profile=None):
    """
    Builds a rich, consolidated text document representing the applicant's qualifications,
    skills, education, and career experience.
    """
    parts = []

    # 1. Headline / Title
    if not profile and hasattr(user, "applicant_profile"):
        profile = user.applicant_profile
    if profile and profile.title:
        # Repeat title twice to boost weight in TF-IDF
        parts.append(f"{profile.title} {profile.title}")
    if profile and profile.bio:
        parts.append(profile.bio)
    if profile and profile.location:
        parts.append(f"Location: {profile.location}")

    # 2. Skills
    if hasattr(user, "skills"):
        skill_texts = []
        for s in user.skills.all():
            weight = 3 if s.level == "expert" else (2 if s.level == "intermediate" else 1)
            skill_texts.append(" ".join([s.name] * weight))
        if skill_texts:
            parts.append("Skills: " + " ".join(skill_texts))

    # 3. Educations
    if hasattr(user, "educations"):
        edu_texts = []
        for e in user.educations.all():
            edu_texts.append(f"{e.degree} {e.field_of_study or ''} {e.institution}")
        if edu_texts:
            parts.append("Education: " + " ".join(edu_texts))

    # 4. Work Experience
    if hasattr(user, "experiences"):
        exp_texts = []
        for exp in user.experiences.all():
            exp_texts.append(f"{exp.title} at {exp.company}. {exp.description or ''}")
        if exp_texts:
            parts.append("Experience: " + " ".join(exp_texts))

    return " \n ".join(parts).strip()


def build_job_text(job):
    """
    Builds a consolidated textual representation of a job vacancy listing.
    """
    tags_str = ""
    if hasattr(job, "tags"):
        try:
            tags_str = " ".join(t.name for t in job.tags.all())
        except Exception:
            tags_str = ""

    company = getattr(job, "company_name", "") or ""
    exp_level = getattr(job, "experience_level", "") or ""
    work_mode = getattr(job, "work_mode", "") or ""

    # Title is given double representation to reflect primary importance
    return (
        f"{job.title} {job.title} \n "
        f"Category: {job.category or ''} \n "
        f"Tags: {tags_str} {tags_str} \n "
        f"Company: {company} \n "
        f"Location: {job.location} WorkMode: {work_mode} Experience: {exp_level} \n "
        f"{job.description or ''} \n "
        f"{job.company_description or ''}"
    ).strip()


def calculate_job_match_score(user, job, user_skills=None, user_title=None, user_location=None, tfidf_sim=None):
    """
    Multi-signal, explainable content-based recommendation scoring function:
    1. TF-IDF Cosine Similarity (Semantic & content match) : 40%
    2. Explicit Skill Match (Proficiency-weighted)         : 35%
    3. Category & Title Alignment                         : 15%
    4. Location & Work Mode Compatibility                  : 10%
    Total normalized score: 0 - 100%.
    """
    if not user or not user.is_authenticated:
        return 0

    reasons = []
    matched_skills = []

    # 1. TF-IDF Content Similarity (40 Points Max)
    content_points = 0
    if tfidf_sim is not None:
        # Cosine similarity scaled smoothly (similarity of 0.5+ indicates high relevance)
        content_points = min(40, int(tfidf_sim * 80))
    else:
        # Fallback single-pair calculation if precomputed matrix not supplied
        applicant_text = build_applicant_profile_text(user)
        job_text = build_job_text(job)
        vectorizer = PureTfidfVectorizer()
        vecs = vectorizer.fit_transform([applicant_text, job_text])
        if len(vecs) == 2:
            sim = PureTfidfVectorizer.cosine_similarity(vecs[0][0], vecs[0][1], vecs[1][0], vecs[1][1])
            content_points = min(40, int(sim * 80))

    if content_points >= 25:
        reasons.append("High profile description & background alignment")

    # 2. Explicit Skill Match (35 Points Max)
    skill_points = 0
    skills_qs = getattr(user, "skills", None)
    if skills_qs and skills_qs.exists():
        job_tags = set()
        if hasattr(job, "tags"):
            try:
                job_tags = set(t.name.lower() for t in job.tags.all())
            except Exception:
                job_tags = set()

        job_full_text = f"{job.title} {job.description} {' '.join(job_tags)}".lower()

        total_weight = 0.0
        earned_weight = 0.0

        for skill in skills_qs.all():
            w = 1.3 if skill.level == "expert" else (1.0 if skill.level == "intermediate" else 0.7)
            total_weight += w

            s_name = skill.name.strip().lower()
            pattern = r"\b" + re.escape(s_name) + r"\b"
            if re.search(pattern, job_full_text) or s_name in job_tags:
                earned_weight += w
                matched_skills.append(skill.name)

        if total_weight > 0:
            ratio = earned_weight / total_weight
            skill_points = int(ratio * 35)
            if matched_skills:
                reasons.append(f"Matches {len(matched_skills)} of your listed skills")
        else:
            skill_points = 10
    else:
        # Candidate hasn't listed skills yet
        skill_points = 10

    # 3. Category & Job Title Alignment (15 Points Max)
    category_points = 0
    if user_title is None:
        user_title = getattr(getattr(user, "applicant_profile", None), "title", "") or ""
    user_title_lower = user_title.lower().strip()
    job_title_lower = (job.title or "").lower().strip()
    job_cat_lower = (job.category or "").lower().strip()

    if user_title_lower:
        if user_title_lower in job_title_lower or job_title_lower in user_title_lower:
            category_points = 15
            reasons.append(f"Direct role title match: {job.title}")
        elif user_title_lower in job_cat_lower or any(word in job_title_lower for word in user_title_lower.split() if len(word) > 3):
            category_points = 12
            reasons.append("Related career discipline")
        elif job_cat_lower and any(c in job_cat_lower for c in ["tech", "developer", "software", "engineering", "finance", "health"]):
            category_points = 8
        else:
            category_points = 5
    else:
        category_points = 8

    # 4. Location & Work Mode Compatibility (10 Points Max)
    location_points = 0
    if user_location is None:
        user_location = getattr(getattr(user, "applicant_profile", None), "location", "") or ""
    user_loc_clean = user_location.lower().strip()
    job_loc_clean = (job.location or "").lower().strip()
    job_work_mode = getattr(job, "work_mode", "on-site")

    if job_work_mode == "remote" or job_loc_clean == "remote":
        location_points = 10
        reasons.append("Remote job (work from anywhere)")
    elif user_loc_clean and job_loc_clean and (user_loc_clean == job_loc_clean or user_loc_clean in job_loc_clean or job_loc_clean in user_loc_clean):
        location_points = 10
        reasons.append(f"Located in your preferred city ({job.location})")
    elif not user_loc_clean:
        location_points = 6
    else:
        location_points = 3

    total_score = content_points + skill_points + category_points + location_points
    # Ensure sane normalized bounds
    final_score = max(5, min(99, total_score))

    return final_score


def invalidate_recommendation_cache(user_id):
    """
    Invalidates cached job recommendations for a specific applicant.
    Called when the user updates profile, adds/removes skills, education, experience,
    or applies to a job.
    """
    try:
        ver_key = f"user_rec_version_{user_id}"
        current_version = cache.get(ver_key, 1)
        cache.set(ver_key, current_version + 1, timeout=86400 * 30)
    except Exception as e:
        logger.warning(f"Failed to bump recommendation cache version: {e}")


def get_recommended_jobs_for_user(user, limit=12, min_score=25):
    """
    Intelligent recommendation engine returning personalized job vacancies for an applicant.
    - Only retrieves published, approved, unfilled, unexpired jobs.
    - Excludes jobs the applicant has already applied to.
    - Uses TF-IDF vectorization and cosine similarity over the entire candidate pool.
    - Uses per-user caching with safe instant invalidation.
    """
    from jobsapp.models import Applicant, Job

    if not user or not user.is_authenticated or getattr(user, "role", "") != "employee":
        return []

    # Check cache version
    ver_key = f"user_rec_version_{user.id}"
    cache_version = cache.get(ver_key, 1)
    cache_key = f"job_recs_v{cache_version}_u{user.id}_lim{limit}_min{min_score}"

    cached_results = cache.get(cache_key)
    if cached_results is not None:
        return cached_results

    # 1. Fetch applied job IDs to exclude
    applied_job_ids = set(Applicant.objects.filter(user=user).values_list("job_id", flat=True))

    # 2. Query active, approved, unexpired jobs
    now = timezone.now()
    active_jobs = (
        Job.objects.filter(status="approved", filled=False, last_date__gte=now)
        .exclude(id__in=applied_job_ids)
        .select_related("user", "company")
        .prefetch_related("tags")
        .order_by("-created_at")[:120]  # candidate pool of latest 120 jobs
    )

    jobs_list = list(active_jobs)
    if not jobs_list:
        return []

    # 3. Build candidate profile document
    profile = getattr(user, "applicant_profile", None)
    applicant_doc = build_applicant_profile_text(user, profile=profile)
    job_docs = [build_job_text(j) for j in jobs_list]

    # 4. Compute TF-IDF matrix
    corpus = [applicant_doc] + job_docs
    vectorizer = PureTfidfVectorizer()
    all_vectors = vectorizer.fit_transform(corpus)

    applicant_vec, applicant_norm = all_vectors[0]

    user_skills = set(user.skills.values_list("name", flat=True)) if hasattr(user, "skills") else set()
    user_title = getattr(profile, "title", "") or ""
    user_location = getattr(profile, "location", "") or ""

    # 5. Score all candidate jobs
    scored_items = []
    for idx, job in enumerate(jobs_list):
        job_vec, job_norm = all_vectors[idx + 1]
        sim = PureTfidfVectorizer.cosine_similarity(applicant_vec, applicant_norm, job_vec, job_norm)

        score = calculate_job_match_score(
            user=user,
            job=job,
            user_skills=user_skills,
            user_title=user_title,
            user_location=user_location,
            tfidf_sim=sim,
        )

        # Matched skills for UI display chips
        job_tags_names = [t.name for t in job.tags.all()] if hasattr(job, "tags") else []
        job_text_lower = f"{job.title} {job.description} {' '.join(job_tags_names)}".lower()
        matched = [s for s in user_skills if s.lower() in job_text_lower]

        if score >= min_score:
            scored_items.append({
                "job": job,
                "match_score": score,
                "matched_skills": matched[:4],
                "tfidf_similarity": round(sim * 100, 1),
            })

    # 6. Rank by match score descending, then by recency
    scored_items.sort(key=lambda x: (x["match_score"], x["job"].created_at), reverse=True)
    final_recommendations = scored_items[:limit]

    # Cache for 15 minutes
    try:
        cache.set(cache_key, final_recommendations, timeout=900)
    except Exception as e:
        logger.warning(f"Could not cache job recommendations: {e}")

    return final_recommendations
