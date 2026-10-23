import io
import re
import logging
import zipfile
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

# Common skills taxonomy across Tech, Accounting, Engineering, Healthcare, Management, and Sales
SKILL_TAXONOMY = [
    # Software & Tech
    "python", "django", "javascript", "typescript", "react", "vue", "angular", "node.js", "php", "laravel",
    "java", "spring boot", "c#", ".net", "flutter", "react native", "sql", "postgresql", "mysql", "mongodb",
    "redis", "docker", "kubernetes", "aws", "azure", "linux", "git", "rest api", "graphql", "html", "css",
    "bootstrap", "tailwind", "machine learning", "data analysis", "devops", "cybersecurity",
    # Finance, Accounting & Banking
    "accounting", "ifrs", "gaap", "quickbooks", "peachtree", "financial reporting", "auditing", "taxation",
    "tax compliance", "payroll", "budgeting", "financial analysis", "excel", "microfinance", "banking",
    # Engineering & Architecture
    "autocad", "civil 3d", "etabs", "sap2000", "gis", "arcgis", "structural analysis", "site supervision",
    "surveying", "mechanical design", "electrical design", "matlab",
    # Healthcare & Sciences
    "pharmacy", "nursing", "public health", "clinical laboratory", "patient care", "medical diagnosis",
    # Business, HR & Sales
    "project management", "agile", "scrum", "human resources", "recruitment", "talent acquisition",
    "sales negotiation", "digital marketing", "seo", "content writing", "supply chain", "procurement",
    "customer service", "communication", "leadership"
]

# Section header patterns typical of genuine resumes
SECTION_PATTERNS = {
    "Contact Info": [r"\bemail\b", r"\bphone\b", r"\btel\b", r"\baddress\b", r"\bcontact\b", r"\blinkedin\b"],
    "Work Experience": [r"\bexperience\b", r"\bwork history\b", r"\bemployment\b", r"\bprofessional background\b", r"\bresponsibilities\b", r"\bworked at\b"],
    "Education": [r"\beducation\b", r"\bacademic\b", r"\buniversity\b", r"\bcollege\b", r"\bdegree\b", r"\bbachelor\b", r"\bmaster\b", r"\bdiploma\b"],
    "Skills": [r"\bskills\b", r"\bcompetencies\b", r"\btechnologies\b", r"\bproficiencies\b", r"\bexpertise\b", r"\btools\b"],
    "Summary / Profile": [r"\bsummary\b", r"\bprofessional profile\b", r"\bobjective\b", r"\babout me\b", r"\bcareer profile\b"]
}

COMMON_JOB_TITLES = [
    "Software Engineer", "Full Stack Developer", "Python Developer", "Django Developer", "Frontend Developer",
    "Backend Developer", "Mobile App Developer", "DevOps Engineer", "Data Analyst", "Data Scientist",
    "Accountant", "Senior Accountant", "Chief Accountant", "Finance Officer", "Internal Auditor",
    "Civil Engineer", "Electrical Engineer", "Mechanical Engineer", "Architect", "Project Manager",
    "HR Specialist", "HR Manager", "Marketing Officer", "Sales Representative", "Pharmacist", "Nurse"
]


def extract_text_from_file(file_obj, filename=""):
    """
    Extracts text content from PDF, DOCX, TXT, or Markdown documents.
    """
    filename_lower = filename.lower() if filename else getattr(file_obj, "name", "").lower()
    content = ""

    try:
        if hasattr(file_obj, "read"):
            data = file_obj.read()
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
        elif isinstance(file_obj, bytes):
            data = file_obj
        else:
            return ""

        if not data:
            return ""

        # 1. PDF Extraction via pypdf
        if filename_lower.endswith(".pdf") or data[:4] == b"%PDF":
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(data))
                pages = [page.extract_text() for page in reader.pages if page.extract_text()]
                content = "\n".join(pages)
            except Exception as e:
                logger.warning(f"pypdf extraction failed: {e}")

        # 2. DOCX Extraction via standard library zipfile (word/document.xml)
        elif filename_lower.endswith(".docx") or data[:2] == b"PK":
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    xml_content = z.read("word/document.xml")
                    tree = ET.fromstring(xml_content)
                    paragraphs = []
                    # Word XML namespace for text elements is w:t
                    for elem in tree.iter():
                        if elem.tag.endswith("}t") and elem.text:
                            paragraphs.append(elem.text)
                    content = " ".join(paragraphs)
            except Exception as e:
                logger.warning(f"docx xml extraction failed: {e}")

        # 3. Plain text / Markdown fallback
        if not content:
            try:
                content = data.decode("utf-8", errors="ignore")
            except Exception:
                try:
                    content = data.decode("latin-1", errors="ignore")
                except Exception:
                    content = ""

    except Exception as e:
        logger.error(f"Error extracting text from file {filename}: {e}")

    return content.strip()


def analyze_resume_authenticity(text, filename=""):
    """
    AI Resume & CV Authenticity Analyzer:
    Analyzes document text structure, verifies presence of essential career sections,
    extracts entities (contact, skills, education, experience), and produces an
    Authenticity & Quality Confidence Score (0 - 100).
    """
    if not text:
        return {
            "is_valid": False,
            "score": 0,
            "status": "empty",
            "message": "The uploaded file is empty or unreadable. Please upload a clear PDF or DOCX Resume/CV.",
            "detected_sections": [],
            "extracted_skills": [],
            "extracted_phone": None,
            "extracted_email": None,
            "extracted_title": None,
            "word_count": 0,
        }

    words = re.findall(r"\b[a-zA-Z0-9+#.-]{2,}\b", text)
    word_count = len(words)
    lower_text = text.lower()

    # Rule 1: Minimum word count threshold for legitimate resumes (>= 35 words)
    if word_count < 35:
        return {
            "is_valid": False,
            "score": max(5, int(word_count * 0.8)),
            "status": "too_short",
            "message": f"Document contains only {word_count} words. A legitimate Resume/CV must contain detailed education, work experience, and skills.",
            "detected_sections": [],
            "extracted_skills": [],
            "extracted_phone": None,
            "extracted_email": None,
            "extracted_title": None,
            "word_count": word_count,
        }

    detected_sections = []
    section_score = 0
    for section_name, patterns in SECTION_PATTERNS.items():
        found = False
        for pat in patterns:
            if re.search(pat, lower_text):
                found = True
                break
        if found:
            detected_sections.append(section_name)
            section_score += 15

    # Contact Details Extraction
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w{2,}", text)
    extracted_email = email_match.group(0) if email_match else None

    phone_match = re.search(r"(\+251[\s\-]?[0-9]{9}|09[0-9]{8}|07[0-9]{8}|\+?[0-9]{10,14})", text)
    extracted_phone = phone_match.group(1).replace(" ", "").replace("-", "") if phone_match else None

    # Skills Extraction
    extracted_skills = []
    for skill in SKILL_TAXONOMY:
        if re.search(r"\b" + re.escape(skill) + r"\b", lower_text):
            extracted_skills.append(skill.title())
            if len(extracted_skills) >= 12:
                break

    # Title Extraction
    extracted_title = None
    for title in COMMON_JOB_TITLES:
        if title.lower() in lower_text:
            extracted_title = title
            break

    # Calculate AI Authenticity Confidence Score (0 - 100)
    score = 0
    # Length / depth: up to 25 pts
    if word_count >= 150:
        score += 25
    elif word_count >= 80:
        score += 18
    else:
        score += 10

    # Sections detected: up to 45 pts (each section ~10 pts)
    score += min(45, len(detected_sections) * 11)

    # Skills detected: up to 15 pts
    if len(extracted_skills) >= 4:
        score += 15
    elif len(extracted_skills) >= 1:
        score += 10

    # Contact details: up to 15 pts
    if extracted_email:
        score += 8
    if extracted_phone:
        score += 7

    score = min(100, score)

    # Legitimacy decision criteria:
    # Must have at least 2 distinct sections (e.g. Education + Experience or Skills + Contact)
    # AND score >= 45
    is_valid = (len(detected_sections) >= 2) and (score >= 45) and (len(extracted_skills) > 0 or "Education" in detected_sections or "Work Experience" in detected_sections)

    if not is_valid:
        status = "invalid"
        message = (
            f"❌ AI Resume Inspection Failed (Score: {score}%): The document lacks essential resume sections "
            f"(such as Work Experience, Education, or Skills). Please attach a genuine, complete CV."
        )
    else:
        status = "verified"
        message = (
            f"✅ AI Verified Resume (Authenticity Score: {score}%): Detected {len(detected_sections)} sections "
            f"({', '.join(detected_sections[:3])}) and {len(extracted_skills)} professional skills."
        )

    return {
        "is_valid": is_valid,
        "score": score,
        "status": status,
        "message": message,
        "detected_sections": detected_sections,
        "extracted_skills": extracted_skills,
        "extracted_phone": extracted_phone,
        "extracted_email": extracted_email,
        "extracted_title": extracted_title,
        "word_count": word_count,
    }
