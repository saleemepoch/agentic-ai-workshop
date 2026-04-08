"""
Golden dataset: hand-labelled CV/JD pairs with expected outcomes.

Each test case defines:
- A CV and JD to match
- Expected retrieval: which chunks should appear in top-k
- Expected match quality: score range and key expectations
- Scenario description: what this case is testing

Interview talking points:
- Why only 4–5 cases? Quality over quantity. Each case is intentionally
  designed to test a specific scenario (clear match, clear mismatch,
  edge cases). A random 100-case dataset might miss the overqualified
  edge case entirely.
- Why include expected retrieval? So we can measure precision@k and
  recall@k. Without knowing which chunks *should* be retrieved, we
  can only measure generation quality — not whether the retrieval
  step is doing its job.
"""

from dataclasses import dataclass


@dataclass
class GoldenCase:
    """A single test case in the golden dataset."""

    id: str
    scenario: str
    description: str
    cv_text: str
    jd_text: str
    expected_match_range: tuple[float, float]  # (min, max) expected score
    expected_keywords: list[str]  # Keywords that should appear in retrieval
    expected_outcome: str  # "strong_match", "partial_match", "no_match"


GOLDEN_DATASET: list[GoldenCase] = [
    GoldenCase(
        id="clear_match",
        scenario="Clear Match",
        description="Senior Python backend engineer CV against a matching backend role. Should produce a strong match with high retrieval quality.",
        cv_text="""SUMMARY
Senior software engineer with 8 years of experience building scalable backend systems in Python. Specialist in distributed systems, API design, and cloud infrastructure.

EXPERIENCE
Senior Engineer at CloudScale Inc, 2020-2024. Led the migration from monolith to microservices architecture, reducing deployment time by 70%. Designed event-driven processing pipeline handling 500K events per second using Kafka and Python. Mentored team of 4 junior engineers.

Software Engineer at DataFlow Ltd, 2016-2020. Built REST APIs serving 2M daily active users using Django and FastAPI. Implemented Redis caching layer that reduced database load by 60%. Designed and maintained CI/CD pipelines using GitHub Actions.

EDUCATION
BSc Computer Science, University of Edinburgh, 2016. First Class Honours.

SKILLS
Python, Go, FastAPI, Django, Kubernetes, PostgreSQL, Kafka, Redis, Docker, AWS, Terraform, gRPC, GitHub Actions.""",
        jd_text="""JOB TITLE
Senior Backend Engineer

COMPANY
TechVentures is a Series B startup building the next generation of developer tools. Engineering team of 25.

RESPONSIBILITIES
Design and implement scalable backend services. Lead technical architecture decisions for new features. Mentor junior engineers and conduct code reviews. Collaborate with product team on roadmap planning.

REQUIREMENTS
5+ years of backend development experience. Strong Python skills with production experience. Experience with distributed systems and microservices. Familiarity with cloud infrastructure (AWS or GCP). Experience with containerisation (Docker, Kubernetes).

NICE TO HAVE
Experience with event-driven architecture. Open source contributions. Prior startup experience.""",
        expected_match_range=(0.7, 1.0),
        expected_keywords=["Python", "microservices", "backend", "Kubernetes", "AWS"],
        expected_outcome="strong_match",
    ),
    GoldenCase(
        id="clear_mismatch",
        scenario="Clear Non-Match",
        description="Marketing coordinator CV against a backend engineering role. Should produce a very low match score with poor retrieval.",
        cv_text="""SUMMARY
Creative marketing coordinator with 2 years of experience in digital marketing and social media management. Passionate about brand storytelling and audience engagement.

EXPERIENCE
Marketing Coordinator at BrandCo Ltd, 2022-2024. Managed Instagram and TikTok accounts growing following by 40%. Created monthly content calendars and campaign briefs. Coordinated with design team on visual assets.

Marketing Intern at StartupHub, 2021-2022. Assisted with email marketing campaigns. Wrote blog posts and social media copy. Analysed campaign performance metrics using Google Analytics.

EDUCATION
BA Communications, University of Leeds, 2021.

SKILLS
Social media management, Canva, content writing, Google Analytics, Mailchimp, basic HTML, copywriting, brand strategy.""",
        jd_text="""JOB TITLE
Senior Backend Engineer

COMPANY
TechVentures is a Series B startup building the next generation of developer tools.

RESPONSIBILITIES
Design and implement scalable backend services. Lead technical architecture decisions. Mentor junior engineers.

REQUIREMENTS
5+ years of backend development experience. Strong Python skills. Experience with distributed systems. Cloud infrastructure experience (AWS/GCP).

NICE TO HAVE
Kubernetes experience. Open source contributions.""",
        expected_match_range=(0.0, 0.3),
        expected_keywords=[],
        expected_outcome="no_match",
    ),
    GoldenCase(
        id="overqualified",
        scenario="Overqualified Candidate",
        description="Staff-level engineer with 15 years experience against a junior role. Technical skills are strong but the seniority mismatch is dramatic — a staff engineer is not going to be happy in a junior role under guidance, and the JD's '0-2 years' requirement is hard-violated. Expected to land in the low-mid range: technical fundamentals lift the score above zero, but the experience mismatch dominates.",
        cv_text="""SUMMARY
Staff engineer with 15 years leading platform engineering at FAANG companies. Architect of systems serving 100M+ users. Published author on distributed systems.

EXPERIENCE
Staff Engineer at Google, 2018-2024. Architected the next-generation serving infrastructure for Google Maps. Led a team of 12 engineers. Published 3 papers on distributed caching strategies.

Senior Engineer at Amazon, 2012-2018. Designed the recommendation engine for Prime Video. Built ML pipelines processing 50TB daily. Promoted twice in 6 years.

Software Engineer at Microsoft, 2009-2012. Core contributor to Azure Storage. Implemented erasure coding for data durability.

EDUCATION
MSc Computer Science, Stanford University, 2009.
BSc Computer Science, MIT, 2007.

SKILLS
Python, Java, C++, Go, Kubernetes, Terraform, distributed systems, ML pipelines, system architecture, technical leadership, public speaking.""",
        jd_text="""JOB TITLE
Junior Software Developer

COMPANY
LocalTech is a small software consultancy based in Manchester. Team of 8.

RESPONSIBILITIES
Write clean, tested code under guidance of senior developers. Fix bugs and implement small features. Participate in code reviews and team standups.

REQUIREMENTS
0-2 years of development experience. Basic knowledge of Python or JavaScript. Understanding of version control (Git). Eagerness to learn and grow.

NICE TO HAVE
Computer science degree. Any side projects or portfolio work.""",
        expected_match_range=(0.10, 0.35),
        expected_keywords=["Python"],
        expected_outcome="no_match",
    ),
    GoldenCase(
        id="transferable_skills",
        scenario="Transferable Skills",
        description="Data scientist with strong Python skills against a backend engineering role. Partial overlap — has the language but not the domain.",
        cv_text="""SUMMARY
Data scientist with 5 years of experience in NLP and recommendation systems. Strong Python skills with production ML pipeline experience.

EXPERIENCE
Senior Data Scientist at DataCorp, 2021-2024. Built NLP pipeline for document classification processing 10M records daily. Developed recommendation engine using collaborative filtering. Deployed models to production using FastAPI and Docker.

Data Scientist at AnalyticsPro, 2019-2021. Built predictive models for customer churn. Created data pipelines using Python, Pandas, and Airflow. Collaborated with engineering team on model serving infrastructure.

EDUCATION
MSc Machine Learning, UCL, 2019.
BSc Mathematics, University of Warwick, 2017.

SKILLS
Python, PyTorch, TensorFlow, FastAPI, Docker, PostgreSQL, Pandas, Spark, Airflow, scikit-learn, NLP, statistics.""",
        jd_text="""JOB TITLE
Senior Backend Engineer

COMPANY
TechVentures — Series B startup building developer tools.

RESPONSIBILITIES
Design and implement scalable backend services. Lead technical architecture decisions. Mentor junior engineers.

REQUIREMENTS
5+ years of backend development experience. Strong Python skills. Experience with distributed systems. Cloud infrastructure experience.

NICE TO HAVE
Experience with Kubernetes. Open source contributions.""",
        expected_match_range=(0.40, 0.65),
        expected_keywords=["Python", "FastAPI", "Docker", "PostgreSQL"],
        expected_outcome="partial_match",
    ),
    GoldenCase(
        id="seniority_gap",
        scenario="Seniority Gap",
        description="Junior developer with 1 year experience against a staff engineer role. Experience gap is the primary issue.",
        cv_text="""SUMMARY
Enthusiastic junior developer with 1 year of professional experience. Keen to learn and grow in a fast-paced environment.

EXPERIENCE
Junior Developer at WebAgency, 2023-2024. Built responsive web pages using React and TypeScript. Fixed bugs in Python backend services. Participated in agile ceremonies and code reviews.

EDUCATION
BSc Computer Science, University of Bristol, 2023.

Bootcamp Graduate, CodeAcademy Pro, 2022. Full-stack web development: React, Node.js, Python, PostgreSQL.

SKILLS
Python, JavaScript, TypeScript, React, Node.js, PostgreSQL, Git, HTML, CSS, basic Docker.""",
        jd_text="""JOB TITLE
Staff Engineer — Platform

COMPANY
FinanceCloud is a Series D fintech building cloud banking infrastructure. Engineering team of 200.

RESPONSIBILITIES
Define technical vision and architecture for the platform team. Drive cross-team technical initiatives. Mentor senior engineers. Make build-vs-buy decisions for core infrastructure. Represent engineering in executive leadership meetings.

REQUIREMENTS
10+ years of software engineering experience. Proven track record of leading large-scale distributed systems. Experience with financial systems or regulated industries. Strong communication and leadership skills. Previous staff or principal engineer experience.

NICE TO HAVE
Experience with Kubernetes at scale. Published technical writing or conference talks. Open source maintainer experience.""",
        expected_match_range=(0.0, 0.3),
        expected_keywords=[],
        expected_outcome="no_match",
    ),
]
