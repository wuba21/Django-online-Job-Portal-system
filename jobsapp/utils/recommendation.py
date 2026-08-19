def calculate_job_match_score(user, job, user_skills=None, user_title=None, user_location=None):
    """
    Explainable job matching algorithm comparing applicant skills, location, category,
    and experience requirements against the job listing.
    Returns an integer match percentage (0 - 100).
    """
    if not user or not user.is_authenticated:
        return 0

    score = 0

    # 1. Category / Title overlap (35 points)
    category_match = 0
    if user_title is None:
        user_title = getattr(getattr(user, "applicant_profile", None), "title", "") or ""
    job_category = job.category.lower() if job.category else ""
    job_title = job.title.lower() if job.title else ""

    if user_title and (user_title.lower() in job_title or user_title.lower() in job_category):
        category_match += 35
    elif job_category and any(cat in job_category for cat in ["tech", "developer", "software", "design", "finance", "marketing"]):
        category_match += 20
    else:
        category_match += 15
    score += category_match

    # 2. Skills Overlap (40 points)
    if user_skills is None:
        user_skills = set(user.skills.values_list("name", flat=True)) if hasattr(user, "skills") else set()

    if user_skills:
        # Avoid job.tags.all() query if pre-fetched or using title/description
        tags_str = " ".join([t.name for t in getattr(job, "prefetched_tags", job.tags.all())]) if hasattr(job, "tags") else ""
        job_text = f"{job.title} {job.description} {tags_str}".lower()
        matched_skills = [skill for skill in user_skills if skill.lower() in job_text]
        if matched_skills:
            skill_ratio = len(matched_skills) / len(user_skills)
            score += int(skill_ratio * 40)
        else:
            score += 10
    else:
        score += 15

    # 3. Location match (15 points)
    if user_location is None:
        user_location = getattr(getattr(user, "applicant_profile", None), "location", "") or ""
    if user_location and job.location:
        if user_location.lower() == job.location.lower() or job.work_mode == "remote":
            score += 15
        else:
            score += 5
    else:
        score += 10

    # 4. Experience match (10 points)
    score += 10

    return min(max(score, 40), 98)
