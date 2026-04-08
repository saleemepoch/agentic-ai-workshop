"""
Seed the database with realistic fictional CVs and job descriptions.

This script populates the workshop database with 10 CVs and 10 JDs spanning
a range of roles and seniority levels. The data is designed to exercise the
full pipeline: chunking (section headings in ALL CAPS or colon-terminated
for regex detection), embedding, retrieval, and matching.

Usage:
    python -m scripts.seed_data

Interview talking points:
- Why fictional data? Real CVs contain PII. Fictional data lets us demonstrate
  the full pipeline without privacy concerns, and we control the content to
  ensure good coverage of edge cases (varied seniority, overlapping skills,
  cross-functional roles).
- Why 300-600 words per document? This is the sweet spot for producing 3-5
  semantic chunks per document — enough to test retrieval quality without
  overwhelming the demo.
"""

import asyncio

from src.database import async_session_factory, init_db
from src.documents.models import Document, DocumentType

# ---------------------------------------------------------------------------
# CVs — 10 fictional candidates across varied roles and seniority levels
# ---------------------------------------------------------------------------

SEED_CVS: list[dict[str, str]] = [
    # 1. Senior Software Engineer
    {
        "title": "CV - Priya Chakraborty - Senior Software Engineer",
        "doc_type": "cv",
        "content": """PRIYA CHAKRABORTY
Senior Software Engineer

SUMMARY
Software engineer with 8 years of experience designing and building distributed systems at scale. Deep expertise in Python, Go, and cloud-native architectures. Passionate about developer tooling and engineering culture. Led the migration of a monolithic recruitment platform to microservices, reducing deployment times from hours to minutes. Comfortable operating across the full stack but strongest on backend systems and infrastructure.

EXPERIENCE

Senior Software Engineer | Meridian Technologies | 2021 - Present
Lead engineer on the platform team serving 40 internal engineers. Designed and implemented an event-driven architecture using Kafka and Python that processes 2M candidate events per day with 99.95% uptime. Built a custom CI/CD pipeline reducing build times by 60%. Mentored 4 junior engineers through structured pairing and code review. Drove adoption of OpenTelemetry for distributed tracing across 12 microservices.

Software Engineer | Cobalt Systems | 2018 - 2021
Built RESTful APIs in Python (FastAPI) and Go for a talent marketplace serving 500K monthly active users. Implemented a real-time notification system using WebSockets and Redis Pub/Sub. Designed the database schema for a multi-tenant SaaS platform, optimising query performance with PostgreSQL partitioning and indexing. Contributed to open-source libraries for API testing.

Junior Software Engineer | BrightPath Digital | 2016 - 2018
Developed internal tools for recruitment consultants using Django and React. Built automated CV parsing pipelines using regex and early NLP techniques. Wrote comprehensive test suites achieving 85% code coverage across the platform.

EDUCATION
MSc Computer Science | University of Edinburgh | 2016
BSc Mathematics | University of Leeds | 2014

SKILLS
Languages: Python, Go, TypeScript, SQL
Frameworks: FastAPI, Django, React, Next.js
Infrastructure: AWS (ECS, Lambda, RDS), Docker, Kubernetes, Terraform
Data: PostgreSQL, Redis, Kafka, Elasticsearch
Practices: TDD, CI/CD, distributed tracing, event-driven architecture

CERTIFICATIONS
AWS Solutions Architect - Professional
Certified Kubernetes Application Developer (CKAD)
""",
    },
    # 2. Mid-Level Software Engineer
    {
        "title": "CV - James Okonkwo - Software Engineer",
        "doc_type": "cv",
        "content": """JAMES OKONKWO
Software Engineer

SUMMARY
Software engineer with 4 years of experience building web applications and APIs. Strong foundation in Python and TypeScript with a focus on clean, testable code. Experienced in agile teams and comfortable owning features end-to-end from design through deployment. Looking to grow into a technical lead role and deepen my expertise in system design.

EXPERIENCE

Software Engineer | NovaBridge Software | 2022 - Present
Full-stack engineer on a recruitment analytics platform used by 200+ agencies. Build and maintain REST APIs using FastAPI with PostgreSQL, serving 50K requests per day. Implemented a candidate search feature using full-text search with PostgreSQL tsvector, improving search relevance by 35%. Write integration tests for all new endpoints and maintain 90% test coverage. Participate in on-call rotation and incident response.

Software Engineer | Fern & Fable Digital | 2020 - 2022
Developed a React-based dashboard for HR teams to track hiring pipeline metrics. Built backend services in Node.js and Express, integrating with third-party ATS APIs. Implemented OAuth 2.0 authentication flow and role-based access control. Collaborated with product managers to define technical requirements and estimate delivery timelines.

EDUCATION
BSc Computer Science | University of Manchester | 2020

SKILLS
Languages: Python, TypeScript, JavaScript, SQL
Frameworks: FastAPI, React, Next.js, Express
Databases: PostgreSQL, MongoDB, Redis
Tools: Docker, GitHub Actions, Sentry, Datadog
Practices: Agile/Scrum, TDD, code review, pair programming

CERTIFICATIONS
AWS Certified Developer - Associate
""",
    },
    # 3. Senior Data Scientist
    {
        "title": "CV - Dr. Elena Vasquez - Senior Data Scientist",
        "doc_type": "cv",
        "content": """DR. ELENA VASQUEZ
Senior Data Scientist

SUMMARY
Data scientist with 7 years of experience applying machine learning to business problems in recruitment and HR technology. Published researcher in NLP with 3 peer-reviewed papers on semantic matching. Expert in building production ML pipelines from experimentation through deployment and monitoring. Strong communicator who translates complex models into actionable business insights for non-technical stakeholders.

EXPERIENCE

Senior Data Scientist | Talentum AI | 2020 - Present
Lead data scientist on the candidate-job matching team. Designed and deployed a transformer-based semantic matching model that improved match precision by 28% over the previous TF-IDF baseline. Built the ML evaluation framework including golden datasets, A/B testing infrastructure, and automated regression detection. Reduced model inference latency from 800ms to 120ms through ONNX optimisation and batched inference. Collaborate with engineering to productionise models via FastAPI microservices with Kubernetes autoscaling.

Data Scientist | Nexus Analytics | 2017 - 2020
Built predictive models for candidate attrition and hiring funnel conversion using XGBoost and LightGBM. Developed an NLP pipeline for extracting skills and experience from unstructured CVs using spaCy and custom NER models. Created automated reporting dashboards in Python (Streamlit) that replaced 20 hours per week of manual analyst work. Mentored 2 junior data scientists on experiment design and statistical rigour.

Research Assistant | Imperial College London | 2015 - 2017
Conducted research on word embeddings for domain-specific text retrieval. Co-authored 3 papers on semantic similarity in low-resource languages. Developed evaluation benchmarks for embedding quality that were adopted by 2 other research groups.

EDUCATION
PhD Machine Learning | Imperial College London | 2017
MSc Statistics | University of Oxford | 2014
BSc Mathematics & Statistics | UCL | 2012

SKILLS
Languages: Python, R, SQL
ML/AI: PyTorch, scikit-learn, Hugging Face Transformers, spaCy, ONNX
Data: PostgreSQL, BigQuery, Spark, dbt, Airflow
MLOps: MLflow, Weights & Biases, Docker, Kubernetes
Techniques: NLP, semantic search, embeddings, classification, regression, A/B testing

PUBLICATIONS
"Cross-lingual semantic matching for talent acquisition" - ACL 2019
"Efficient skill extraction from unstructured text" - EMNLP 2018
""",
    },
    # 4. Junior Data Scientist
    {
        "title": "CV - Aisha Patel - Junior Data Scientist",
        "doc_type": "cv",
        "content": """AISHA PATEL
Junior Data Scientist

SUMMARY
Recent MSc graduate with a strong foundation in statistics, machine learning, and data analysis. Completed a 6-month internship building NLP models for a recruitment technology company. Experienced with Python data science tooling and comfortable working with large datasets. Eager to apply academic knowledge to real-world problems in a fast-paced environment.

EXPERIENCE

Data Science Intern | Searchlight HR Tech | 2024 (6 months)
Built a text classification model to categorise job descriptions by seniority level, achieving 89% accuracy using fine-tuned BERT. Cleaned and preprocessed a dataset of 50K job descriptions, handling missing values, deduplication, and text normalisation. Created exploratory data analysis notebooks that informed feature engineering decisions. Presented findings to the product team with clear visualisations and actionable recommendations.

Research Project | University of Bristol | 2023 - 2024
MSc dissertation: "Evaluating embedding models for CV-to-job matching." Compared OpenAI, Cohere, and Voyage AI embeddings on a hand-labelled recruitment dataset. Designed evaluation metrics including precision@k, recall@k, and MRR. Found that domain-specific fine-tuning improved retrieval precision by 15% over general-purpose embeddings.

Teaching Assistant | University of Bristol | 2023 - 2024
Supported undergraduate statistics and machine learning modules. Led weekly tutorial sessions for groups of 20 students. Created practice problems and marked assignments on regression, classification, and clustering.

EDUCATION
MSc Data Science | University of Bristol | 2024
BSc Mathematics | University of Warwick | 2023

SKILLS
Languages: Python, R, SQL
ML/AI: scikit-learn, PyTorch, Hugging Face Transformers, spaCy
Data: pandas, NumPy, Matplotlib, Seaborn, Jupyter
Databases: PostgreSQL, SQLite
Tools: Git, Docker (basic), VS Code
Techniques: NLP, text classification, embeddings, statistical analysis, A/B testing
""",
    },
    # 5. Senior Product Manager
    {
        "title": "CV - Michael Thornton - Senior Product Manager",
        "doc_type": "cv",
        "content": """MICHAEL THORNTON
Senior Product Manager

SUMMARY
Product manager with 9 years of experience leading B2B SaaS products in the HR technology space. Track record of taking products from zero-to-one and scaling them to multi-million pound revenue. Deep understanding of AI and machine learning capabilities, enabling effective collaboration with data science teams on AI-powered features. Known for rigorous prioritisation using data-driven frameworks and clear stakeholder communication.

EXPERIENCE

Senior Product Manager | Alchemy Talent | 2020 - Present
Own the product roadmap for the AI matching platform serving 300 enterprise clients. Led the launch of an LLM-powered candidate screening feature that increased recruiter productivity by 40%. Define success metrics and run A/B experiments to validate feature hypotheses. Manage a cross-functional squad of 8 engineers, 2 data scientists, and 1 designer. Conduct quarterly business reviews with C-level stakeholders presenting product metrics, competitive analysis, and strategic direction. Reduced customer churn by 15% through systematic analysis of support tickets and user behaviour data.

Product Manager | Greenfield HR | 2017 - 2020
Led the development of a skills taxonomy platform used by 150 enterprise clients. Defined the product vision, wrote detailed PRDs, and prioritised the backlog using RICE scoring. Conducted 100+ customer discovery interviews to identify unmet needs in competency mapping. Worked closely with engineering to balance technical debt reduction with feature delivery. Launched an API marketplace that generated 20% of total platform revenue within 12 months.

Associate Product Manager | ClearView Analytics | 2015 - 2017
Managed the reporting and analytics module of an applicant tracking system. Gathered requirements through user research and competitive analysis. Wrote user stories and acceptance criteria for a team of 5 engineers. Coordinated with marketing on product launches and go-to-market strategy.

EDUCATION
MBA | London Business School | 2015
BSc Economics | University of Nottingham | 2012

SKILLS
Product: Roadmap strategy, PRDs, RICE/ICE prioritisation, A/B testing, OKRs
Technical: SQL (intermediate), Python (basic), understanding of ML/NLP/LLMs
Research: User interviews, surveys, usability testing, jobs-to-be-done framework
Tools: Jira, Amplitude, Mixpanel, Figma, Notion, Miro
Domain: HR technology, recruitment, talent management, enterprise SaaS
""",
    },
    # 6. Mid-Level Product Manager
    {
        "title": "CV - Sophie Lindqvist - Product Manager",
        "doc_type": "cv",
        "content": """SOPHIE LINDQVIST
Product Manager

SUMMARY
Product manager with 4 years of experience building developer-facing and data platform products. Background in software engineering gives me a strong technical foundation for working with engineering teams. Passionate about developer experience, API design, and making complex technology accessible. Experienced with agile methodologies and data-informed decision-making.

EXPERIENCE

Product Manager | DataBridge Labs | 2022 - Present
Own the developer platform product serving 5,000 monthly active developers. Led the redesign of the API documentation and onboarding flow, reducing time-to-first-API-call from 45 minutes to 8 minutes. Defined and tracked product metrics (activation rate, API call volume, error rates) using Amplitude. Managed integration partnerships with 3 ATS vendors, negotiating technical requirements and timelines. Run weekly sprint planning, backlog grooming, and retrospectives with a team of 6 engineers.

Associate Product Manager | Windmill Software | 2020 - 2022
Managed the data pipeline configuration UI for a recruitment analytics platform. Conducted user research with 30 data analysts to understand workflow pain points. Designed a visual pipeline builder that reduced pipeline setup time from 2 hours to 15 minutes. Wrote technical specifications and API contracts for frontend-backend integration. Collaborated with the data science team to productionise ML models for candidate scoring.

Software Engineer | Windmill Software | 2018 - 2020
Built backend services in Python and PostgreSQL for the analytics platform. Implemented ETL pipelines using Apache Airflow. Transitioned to product management after identifying a passion for understanding user problems and defining solutions.

EDUCATION
BSc Computer Science | KTH Royal Institute of Technology, Stockholm | 2018

SKILLS
Product: User research, sprint planning, roadmap prioritisation, A/B testing
Technical: Python, SQL, REST APIs, system design, data modelling
Tools: Jira, Linear, Amplitude, Figma, Notion
Domain: Developer tools, data platforms, recruitment analytics
""",
    },
    # 7. UX Lead
    {
        "title": "CV - Rebecca Huang - UX Lead",
        "doc_type": "cv",
        "content": """REBECCA HUANG
UX Lead

SUMMARY
UX designer with 8 years of experience leading design for complex B2B SaaS products. Specialise in making data-heavy enterprise tools intuitive and accessible. Led design teams of up to 5 designers. Deep experience with AI-powered products, including designing interfaces that explain model decisions to non-technical users. Advocate for inclusive design practices and accessibility standards.

EXPERIENCE

UX Lead | Luminary Talent | 2021 - Present
Lead a team of 3 designers responsible for the AI recruitment platform UX. Redesigned the candidate matching interface to show match reasoning (why a candidate was ranked highly), increasing recruiter trust scores by 30%. Established the design system (Figma component library) used across 4 product teams. Conduct monthly usability testing sessions with 8-10 participants. Defined the UX strategy for an LLM-powered chat interface for recruiters, including conversation flow design, error state handling, and progressive disclosure of AI confidence levels. Reduced support tickets related to UI confusion by 45% through systematic heuristic evaluation and redesign.

Senior UX Designer | Atlas HR Systems | 2018 - 2021
Designed the end-to-end hiring workflow for an enterprise ATS used by 200+ companies. Created information architecture for a complex permissions system, simplifying 15 configuration screens into 4. Led a design sprint that produced a new onboarding flow, reducing time-to-value from 3 weeks to 3 days. Built and maintained a pattern library ensuring visual consistency across the platform. Mentored 2 junior designers on research methods and interaction design.

UX Designer | FreshMinds Agency | 2016 - 2018
Delivered UX design for client projects across fintech, health tech, and recruitment. Conducted user research including contextual inquiry, card sorting, and tree testing. Produced wireframes, prototypes, and design specifications for development teams. Managed stakeholder expectations across 3-4 concurrent projects.

EDUCATION
MA Interaction Design | Royal College of Art | 2016
BA Graphic Design | University of the Arts London | 2014

SKILLS
Design: Figma, Sketch, Adobe Creative Suite, Framer
Research: Usability testing, user interviews, surveys, A/B testing, heuristic evaluation
Methods: Design thinking, jobs-to-be-done, design sprints, atomic design
Technical: HTML/CSS (prototyping), basic JavaScript, understanding of React component architecture
Accessibility: WCAG 2.1 AA, screen reader testing, inclusive design patterns
""",
    },
    # 8. UI Designer
    {
        "title": "CV - Daniel Osei - UI Designer",
        "doc_type": "cv",
        "content": """DANIEL OSEI
UI Designer

SUMMARY
UI designer with 3 years of experience creating clean, visually polished interfaces for web applications. Strong skills in visual design, design systems, and front-end prototyping. Experienced in translating complex data into clear, scannable layouts. Comfortable working closely with engineers to ensure pixel-perfect implementation. Portfolio at danielosei.design.

EXPERIENCE

UI Designer | Prism Recruitment | 2022 - Present
Design UI for a recruitment CRM used by 5,000 recruiters daily. Created a comprehensive design system with 120+ components in Figma, reducing design-to-development handoff time by 40%. Designed data visualisation dashboards showing hiring pipeline metrics, candidate demographics, and time-to-hire trends. Implemented responsive layouts ensuring usability across desktop, tablet, and mobile. Collaborate daily with frontend engineers on component implementation in React and Tailwind CSS. Conduct weekly design reviews to maintain visual consistency and quality.

Junior UI Designer | Mosaic Digital Agency | 2021 - 2022
Designed landing pages, marketing sites, and web application interfaces for clients in recruitment and education technology. Created icon sets, illustration systems, and brand guidelines for 5 client projects. Prototyped interactive components using Figma and Framer. Participated in client presentations and incorporated feedback into design iterations.

Freelance Designer | Self-Employed | 2020 - 2021
Delivered brand identity and web design projects for small businesses and startups. Designed logos, business cards, and social media templates. Built simple marketing websites using Webflow.

EDUCATION
BA Digital Design | Goldsmiths, University of London | 2020

SKILLS
Design: Figma, Sketch, Adobe Illustrator, Adobe Photoshop, Framer
Prototyping: Figma prototyping, Framer, basic HTML/CSS
Systems: Atomic design, design tokens, component libraries
Specialisms: Data visualisation, responsive design, typography, colour theory
Collaboration: Design handoff (Figma Dev Mode), working with Tailwind CSS utility classes
""",
    },
    # 9. DevOps Engineer
    {
        "title": "CV - Ravi Mehta - DevOps Engineer",
        "doc_type": "cv",
        "content": """RAVI MEHTA
DevOps Engineer

SUMMARY
DevOps engineer with 6 years of experience building and operating cloud infrastructure for SaaS platforms. Expert in AWS, Kubernetes, and infrastructure-as-code. Passionate about developer experience, observability, and reducing the gap between writing code and running it reliably in production. Track record of improving deployment frequency, reducing incident response times, and building self-service platform tooling.

EXPERIENCE

Senior DevOps Engineer | Arcadia Talent Solutions | 2021 - Present
Own the cloud infrastructure for a recruitment SaaS platform handling 10M API requests per day. Migrated from EC2-based deployments to EKS (Kubernetes), reducing infrastructure costs by 35% through autoscaling and right-sizing. Built a GitOps deployment pipeline using ArgoCD and GitHub Actions, enabling 50+ deployments per week (up from 2 per week). Implemented comprehensive observability stack: Prometheus for metrics, Grafana for dashboards, OpenTelemetry for distributed tracing, and PagerDuty for alerting. Reduced mean time to recovery (MTTR) from 4 hours to 25 minutes through automated runbooks and improved alerting. Manage PostgreSQL databases including pgvector for AI feature workloads, handling replication, backups, and performance tuning.

DevOps Engineer | CloudForge Systems | 2018 - 2021
Built and maintained Terraform modules for provisioning AWS infrastructure across 3 environments (dev, staging, production). Implemented Docker-based CI/CD pipelines using Jenkins and later GitHub Actions. Set up centralised logging with the ELK stack (Elasticsearch, Logstash, Kibana). Managed RDS PostgreSQL instances, including query performance optimisation and automated backup verification.

Systems Administrator | BrightWave ISP | 2017 - 2018
Administered Linux servers (Ubuntu, CentOS) hosting web applications and email services. Wrote Bash and Python scripts for server monitoring and automated patching. Managed DNS, load balancers, and SSL certificate deployment.

EDUCATION
BSc Computer Networks | University of Plymouth | 2017

SKILLS
Cloud: AWS (ECS, EKS, RDS, Lambda, S3, CloudFront, IAM), GCP (basic)
Containers: Docker, Kubernetes, Helm, ArgoCD
IaC: Terraform, Ansible, CloudFormation
CI/CD: GitHub Actions, Jenkins, GitOps
Observability: Prometheus, Grafana, OpenTelemetry, ELK, PagerDuty
Databases: PostgreSQL (including pgvector), Redis, Elasticsearch
Scripting: Python, Bash, Go (basic)

CERTIFICATIONS
AWS Solutions Architect - Professional
Certified Kubernetes Administrator (CKA)
HashiCorp Terraform Associate
""",
    },
    # 10. ML Engineer
    {
        "title": "CV - Fatima Al-Rashidi - ML Engineer",
        "doc_type": "cv",
        "content": """FATIMA AL-RASHIDI
ML Engineer

SUMMARY
ML engineer with 5 years of experience bridging the gap between data science experimentation and production ML systems. Expert in building inference pipelines, model serving infrastructure, and evaluation frameworks. Deep hands-on experience with LLMs, RAG systems, and embedding pipelines. Comfortable working across the full ML lifecycle from data preparation through deployment and monitoring.

EXPERIENCE

ML Engineer | Sentinel AI | 2022 - Present
Lead ML engineer on the retrieval-augmented generation (RAG) platform for enterprise knowledge management. Designed and built the embedding pipeline using Voyage AI, processing 500K documents with pgvector for similarity search. Implemented a multi-stage retrieval system: sparse retrieval (BM25) followed by dense retrieval (vector similarity) and cross-encoder reranking, improving top-5 precision from 0.62 to 0.84. Built the LLM orchestration layer using LangGraph for multi-step reasoning workflows with tool use. Integrated Langfuse for end-to-end observability: tracing every LLM call, tracking token costs, and managing prompt versions. Designed the evaluation framework with golden datasets, automated regression testing, and LLM-as-judge scoring for faithfulness and relevance.

ML Engineer | Paragon Data | 2020 - 2022
Built real-time ML serving infrastructure using FastAPI and Docker, serving 10K predictions per minute with p99 latency under 50ms. Implemented A/B testing framework for model comparison, enabling safe rollout of new models with automatic rollback. Developed feature stores using Redis and PostgreSQL for low-latency feature serving. Worked with data scientists to optimise PyTorch models for production: quantisation, ONNX export, and batched inference.

Data Engineer | Paragon Data | 2019 - 2020
Built ETL pipelines using Apache Airflow and dbt for transforming raw recruitment data into ML-ready features. Managed data quality checks and monitoring using Great Expectations. Designed the data warehouse schema in BigQuery for analytics and model training.

EDUCATION
MSc Artificial Intelligence | University of Southampton | 2019
BEng Computer Engineering | University of Birmingham | 2017

SKILLS
Languages: Python, SQL, Go (basic)
ML/AI: PyTorch, Hugging Face Transformers, LangGraph, LangChain, ONNX
LLM Stack: Anthropic Claude API, Voyage AI embeddings, pgvector, Langfuse
Infrastructure: FastAPI, Docker, Kubernetes, AWS (SageMaker, ECS, S3)
Data: PostgreSQL, Redis, BigQuery, Airflow, dbt
MLOps: MLflow, Weights & Biases, model versioning, A/B testing, evaluation frameworks
""",
    },
]


# ---------------------------------------------------------------------------
# Job Descriptions — 10 fictional roles designed to match the CV candidates
# ---------------------------------------------------------------------------

SEED_JDS: list[dict[str, str]] = [
    # 1. Senior Software Engineer
    {
        "title": "JD - Senior Software Engineer - Vertex Recruitment",
        "doc_type": "jd",
        "content": """JOB TITLE
Senior Software Engineer

COMPANY
Vertex Recruitment is a fast-growing HR technology company building the next generation of AI-powered recruitment tools. Our platform helps enterprise clients find, screen, and hire top talent using machine learning and natural language processing. We serve 400 enterprise clients and process millions of candidate applications per year. Our engineering team values clean code, thoughtful architecture, and continuous improvement.

RESPONSIBILITIES
- Design and build scalable backend services in Python, supporting high-throughput data pipelines and real-time APIs.
- Own the architecture of core platform components, making decisions about data models, API contracts, and system boundaries.
- Mentor mid-level and junior engineers through code review, pairing, and technical guidance.
- Collaborate with product managers and data scientists to translate business requirements into technical solutions.
- Drive engineering best practices: testing, observability, CI/CD, and documentation.
- Participate in on-call rotation and lead incident response for backend services.
- Contribute to technical strategy and roadmap planning.

REQUIREMENTS
- 6+ years of professional software engineering experience.
- Strong proficiency in Python with experience building production APIs (FastAPI or Django preferred).
- Deep understanding of PostgreSQL, including query optimisation and schema design.
- Experience with event-driven architectures (Kafka, RabbitMQ, or similar).
- Track record of mentoring engineers and raising team capabilities.
- Comfortable with containerised deployments (Docker, Kubernetes).
- Excellent communication skills for cross-functional collaboration.

NICE TO HAVE
- Experience with Go or TypeScript as a secondary language.
- Familiarity with ML/AI concepts (embeddings, vector databases, LLMs).
- Open-source contributions.
- AWS Solutions Architect or similar cloud certification.
""",
    },
    # 2. Software Engineer
    {
        "title": "JD - Software Engineer - BrightLoop Tech",
        "doc_type": "jd",
        "content": """JOB TITLE
Software Engineer

COMPANY
BrightLoop Tech builds recruitment analytics tools that help hiring teams make data-driven decisions. We are a team of 25 engineers working in small, autonomous squads. Our stack is Python and TypeScript, and we value engineers who can work across the full stack. We are looking for a mid-level engineer who writes clean code, cares about testing, and wants to grow into a technical leadership role.

RESPONSIBILITIES
- Build and maintain REST APIs and web application features across the full stack.
- Write clean, well-tested code with comprehensive unit and integration tests.
- Collaborate with product managers to estimate work, define technical approach, and deliver features iteratively.
- Participate in code reviews, giving and receiving constructive feedback.
- Contribute to frontend development using React and Next.js.
- Debug production issues and participate in on-call rotation.
- Propose and implement improvements to development workflows and tooling.

REQUIREMENTS
- 3-5 years of professional software engineering experience.
- Proficiency in Python and TypeScript.
- Experience building REST APIs (FastAPI, Django, or Express).
- Solid understanding of relational databases (PostgreSQL preferred).
- Experience with React or Next.js for frontend development.
- Familiarity with Docker and CI/CD pipelines (GitHub Actions preferred).
- Strong testing habits: unit tests, integration tests, and a focus on code quality.

NICE TO HAVE
- Experience with recruitment or HR technology domain.
- Familiarity with data pipelines or analytics platforms.
- AWS or similar cloud platform experience.
- Interest in AI/ML and willingness to learn about embedding models and LLMs.
""",
    },
    # 3. Senior Data Scientist
    {
        "title": "JD - Senior Data Scientist - Nexera AI",
        "doc_type": "jd",
        "content": """JOB TITLE
Senior Data Scientist

COMPANY
Nexera AI is building intelligent matching technology for the global talent market. Our models process millions of CVs and job descriptions, predicting candidate-job fit with state-of-the-art accuracy. We are a research-informed engineering team that values both academic rigour and production readiness. We are looking for a senior data scientist who can lead ML projects from research through deployment.

RESPONSIBILITIES
- Lead the development of NLP and machine learning models for candidate-job matching, from problem definition through production deployment.
- Design and maintain evaluation frameworks including golden datasets, retrieval metrics, and LLM-as-judge scoring.
- Collaborate with ML engineers to productionise models, ensuring low-latency inference and reliable serving.
- Conduct experiments with embedding models, fine-tuning strategies, and retrieval architectures, reporting results with statistical rigour.
- Mentor junior data scientists on experiment design, model evaluation, and best practices.
- Communicate model performance and business impact to non-technical stakeholders through clear visualisations and presentations.
- Stay current with developments in NLP, LLMs, and information retrieval.

REQUIREMENTS
- 5+ years of professional data science experience with a focus on NLP and text matching.
- PhD or MSc in machine learning, statistics, NLP, or a related quantitative field.
- Strong proficiency in Python and ML frameworks (PyTorch, Hugging Face Transformers).
- Experience with embedding models and semantic similarity (vector databases, cosine similarity, reranking).
- Track record of deploying ML models to production, not just notebooks.
- Experience designing evaluation frameworks with quantitative metrics.
- Excellent communication skills for presenting to both technical and business audiences.

NICE TO HAVE
- Published research in NLP, information retrieval, or ML.
- Experience with LLMs (prompt engineering, RAG, fine-tuning).
- Familiarity with MLOps tools (MLflow, Weights & Biases, Langfuse).
- Experience in recruitment, HR tech, or talent marketplace domain.
""",
    },
    # 4. Junior Data Scientist
    {
        "title": "JD - Junior Data Scientist - Mosaic Analytics",
        "doc_type": "jd",
        "content": """JOB TITLE
Junior Data Scientist

COMPANY
Mosaic Analytics provides data science solutions for HR departments and recruitment agencies. We help our clients understand their hiring data, predict candidate success, and reduce bias in recruitment processes. Our team is small but growing, and we invest heavily in developing our junior team members. This is an ideal role for a recent graduate with strong analytical skills and a passion for applied machine learning.

RESPONSIBILITIES
- Build and evaluate machine learning models for text classification, candidate scoring, and matching tasks.
- Clean, preprocess, and analyse large datasets, ensuring data quality and consistency.
- Create exploratory data analysis notebooks and present findings to the team.
- Assist senior data scientists with experiment design, feature engineering, and model evaluation.
- Write well-documented Python code for data pipelines and model training.
- Contribute to the team's evaluation framework, including maintaining golden datasets and tracking metrics.
- Stay current with NLP and ML research, sharing relevant papers and techniques with the team.

REQUIREMENTS
- MSc or BSc in data science, statistics, computer science, or a related quantitative field.
- Strong foundation in statistics and machine learning fundamentals.
- Proficiency in Python with experience using pandas, scikit-learn, and Jupyter notebooks.
- Familiarity with NLP techniques: text classification, embeddings, named entity recognition.
- Experience with SQL for data querying and analysis.
- Good communication skills and ability to present findings clearly.
- Portfolio of projects (academic or personal) demonstrating analytical thinking.

NICE TO HAVE
- Experience with PyTorch or Hugging Face Transformers.
- Familiarity with version control (Git) and collaborative development.
- Previous internship or work experience in a data science role.
- Interest in recruitment, HR analytics, or people data.
""",
    },
    # 5. Senior Product Manager
    {
        "title": "JD - Senior Product Manager, AI Platform - Helix Talent",
        "doc_type": "jd",
        "content": """JOB TITLE
Senior Product Manager, AI Platform

COMPANY
Helix Talent is a leading recruitment technology company whose AI-powered platform is used by 500+ enterprise clients worldwide. We are at an inflection point: integrating large language models into our core matching and screening workflows. We need a senior product manager who understands AI capabilities and limitations, can work closely with data science and engineering teams, and has a track record of shipping complex B2B products.

RESPONSIBILITIES
- Own the product strategy and roadmap for the AI platform, including matching, screening, and candidate outreach features.
- Define success metrics and run experiments to validate product hypotheses.
- Work closely with data scientists and ML engineers to translate AI capabilities into user-facing features.
- Conduct customer discovery interviews and competitive analysis to identify market opportunities.
- Write detailed product requirements documents (PRDs) and user stories.
- Present product strategy, metrics, and competitive landscape to senior leadership.
- Manage a cross-functional squad of engineers, data scientists, and designers.
- Balance technical debt reduction with new feature delivery.

REQUIREMENTS
- 7+ years of product management experience in B2B SaaS.
- Experience working on AI/ML-powered products with data science teams.
- Strong understanding of machine learning concepts (enough to evaluate feasibility and trade-offs, not to build models).
- Demonstrated ability to take products from concept to launch and scale.
- Data-driven decision making: comfortable with SQL, analytics tools, and A/B testing.
- Excellent stakeholder communication: able to present to C-level executives.
- Experience with prioritisation frameworks (RICE, ICE, or similar).

NICE TO HAVE
- Experience in recruitment, HR technology, or talent management.
- MBA or equivalent business education.
- Technical background (former engineer or computer science degree).
- Familiarity with LLMs, RAG, and prompt engineering concepts.
""",
    },
    # 6. Product Manager
    {
        "title": "JD - Product Manager, Developer Platform - Optera Software",
        "doc_type": "jd",
        "content": """JOB TITLE
Product Manager, Developer Platform

COMPANY
Optera Software builds integration tools for the recruitment industry, enabling ATS vendors, job boards, and HR platforms to connect seamlessly. Our developer platform serves 3,000 active developers building on our APIs. We need a product manager who is passionate about developer experience, understands APIs and technical products, and can drive platform adoption through great documentation, tooling, and onboarding.

RESPONSIBILITIES
- Own the product roadmap for the developer platform, including APIs, SDKs, documentation, and developer onboarding.
- Define and track key metrics: developer activation rate, API call volume, time-to-first-call, error rates.
- Conduct user research with developers to understand pain points and prioritise improvements.
- Collaborate with engineering to define API contracts, manage deprecation, and ensure backward compatibility.
- Work with partnerships team to onboard new integration partners, defining technical requirements and success criteria.
- Run sprint ceremonies (planning, grooming, retrospectives) with the platform engineering team.
- Improve developer documentation and self-service tooling to reduce support burden.

REQUIREMENTS
- 3-5 years of product management experience, preferably with developer-facing or technical products.
- Technical background: ability to read API documentation, understand REST/GraphQL, and discuss system design with engineers.
- Experience with developer experience metrics and onboarding funnel optimisation.
- Strong user research skills: ability to conduct interviews, synthesise findings, and translate into product decisions.
- Familiarity with agile methodologies and sprint-based delivery.
- Excellent written communication for documentation and technical specifications.

NICE TO HAVE
- Previous software engineering experience.
- Experience with recruitment technology or HR platforms.
- Familiarity with data platforms, ETL, or analytics tools.
- Experience managing integration partnerships.
""",
    },
    # 7. UX Design Lead
    {
        "title": "JD - UX Design Lead - Cascade HR",
        "doc_type": "jd",
        "content": """JOB TITLE
UX Design Lead

COMPANY
Cascade HR builds enterprise workforce management software used by 350 companies across Europe. Our product spans hiring, onboarding, performance management, and workforce planning. As we integrate AI features (automated screening, predictive analytics, LLM-powered assistants), we need a UX design lead who can make complex AI-powered tools feel intuitive and trustworthy.

RESPONSIBILITIES
- Lead a design team of 3-4 designers, setting quality standards and providing mentorship.
- Define the UX strategy for AI-powered features, ensuring transparency and explainability in model-driven decisions.
- Establish and maintain the product design system (Figma component library, design tokens, usage guidelines).
- Conduct and oversee user research: usability testing, interviews, heuristic evaluations, and accessibility audits.
- Collaborate with product managers and engineers to define interaction patterns, information architecture, and user flows.
- Advocate for accessibility (WCAG 2.1 AA compliance) and inclusive design across all product surfaces.
- Present design rationale and research findings to senior leadership and cross-functional stakeholders.

REQUIREMENTS
- 7+ years of UX design experience, with at least 2 years leading a design team.
- Strong portfolio demonstrating complex B2B SaaS product design.
- Experience designing for AI-powered or data-heavy products, including explainability and trust patterns.
- Proficiency in Figma and experience building and scaling design systems.
- Solid user research skills: ability to plan, conduct, and synthesise qualitative and quantitative research.
- Understanding of accessibility standards and inclusive design principles.
- Excellent communication and presentation skills.

NICE TO HAVE
- Experience in HR technology, recruitment, or enterprise workforce tools.
- Familiarity with design for LLM-powered interfaces (chat, generative content).
- Front-end prototyping skills (HTML/CSS, Framer).
- Experience with design sprint facilitation.
""",
    },
    # 8. UI Designer
    {
        "title": "JD - UI Designer - TalentGrid",
        "doc_type": "jd",
        "content": """JOB TITLE
UI Designer

COMPANY
TalentGrid is a recruitment CRM that helps agencies manage candidate relationships and hiring pipelines. Our product is used daily by 8,000 recruiters who rely on fast, scannable interfaces to manage high volumes of candidates. We need a UI designer who can create polished, consistent interfaces and build a robust design system that scales with our product.

RESPONSIBILITIES
- Design user interfaces for web application features, ensuring visual consistency and usability.
- Build and maintain the design system: reusable components, design tokens, and usage documentation in Figma.
- Design data visualisation dashboards for recruitment metrics (time-to-hire, pipeline conversion, candidate demographics).
- Create responsive layouts that work across desktop and tablet devices.
- Collaborate with frontend engineers on component implementation, ensuring design fidelity in code.
- Participate in design reviews and provide feedback on visual quality and consistency.
- Produce design specifications and assets for development handoff.

REQUIREMENTS
- 2-4 years of UI design experience for web applications.
- Strong proficiency in Figma, including component libraries and auto-layout.
- Excellent visual design skills: typography, colour theory, spacing, and layout.
- Experience designing data visualisation dashboards or information-dense interfaces.
- Understanding of responsive design principles.
- Familiarity with design handoff workflows and working with frontend developers.
- Portfolio demonstrating clean, polished interface design.

NICE TO HAVE
- Experience with design systems at scale (design tokens, multi-brand theming).
- Familiarity with Tailwind CSS or CSS frameworks used by engineering teams.
- Prototyping skills in Figma or Framer.
- Experience in recruitment, CRM, or enterprise SaaS products.
""",
    },
    # 9. DevOps Engineer
    {
        "title": "JD - DevOps Engineer - Horizon Staffing Tech",
        "doc_type": "jd",
        "content": """JOB TITLE
DevOps Engineer

COMPANY
Horizon Staffing Tech operates a high-availability recruitment platform processing 15M API requests daily. Our infrastructure spans AWS with Kubernetes orchestration, and we are expanding our AI capabilities (vector databases, LLM inference, embedding pipelines). We need a DevOps engineer who can build reliable infrastructure for both traditional web services and emerging AI workloads.

RESPONSIBILITIES
- Design, build, and operate cloud infrastructure on AWS, with a focus on Kubernetes-based deployments.
- Implement and maintain CI/CD pipelines for 20+ microservices, enabling multiple daily deployments.
- Build and maintain observability infrastructure: metrics, logging, tracing, and alerting.
- Manage PostgreSQL databases including pgvector for vector similarity search workloads.
- Implement infrastructure-as-code using Terraform, ensuring reproducible and version-controlled environments.
- Improve developer experience through self-service tooling, documentation, and automation.
- Participate in incident response and drive post-incident reviews to improve system reliability.
- Optimise infrastructure costs through right-sizing, autoscaling, and reserved capacity planning.

REQUIREMENTS
- 5+ years of DevOps or infrastructure engineering experience.
- Strong proficiency with AWS (ECS/EKS, RDS, Lambda, S3, IAM).
- Hands-on experience with Kubernetes in production (deployment, autoscaling, networking, troubleshooting).
- Experience with Terraform or equivalent infrastructure-as-code tools.
- Proficiency in CI/CD pipeline design (GitHub Actions, Jenkins, or ArgoCD).
- Strong Linux systems administration skills.
- Experience with observability tools (Prometheus, Grafana, OpenTelemetry, or similar).
- Scripting skills in Python and Bash.

NICE TO HAVE
- Experience managing PostgreSQL with pgvector or other vector database workloads.
- Familiarity with ML serving infrastructure (model deployment, GPU instances, inference optimisation).
- CKA, AWS Solutions Architect, or equivalent certifications.
- Experience with GitOps deployment patterns.
""",
    },
    # 10. ML Engineer
    {
        "title": "JD - ML Engineer - Athena Intelligence",
        "doc_type": "jd",
        "content": """JOB TITLE
ML Engineer

COMPANY
Athena Intelligence builds AI-powered tools for enterprise recruitment, combining large language models with structured data to automate candidate screening, matching, and outreach. Our ML engineering team sits at the intersection of research and production, turning cutting-edge AI techniques into reliable, scalable systems. We are looking for an ML engineer who can build production-grade RAG pipelines, evaluation frameworks, and LLM orchestration systems.

RESPONSIBILITIES
- Design and build production RAG (retrieval-augmented generation) pipelines: document processing, embedding, retrieval, reranking, and generation.
- Implement LLM orchestration workflows using LangGraph or similar frameworks, including tool use and conditional routing.
- Build evaluation frameworks with golden datasets, retrieval metrics (precision@k, MRR), and LLM-as-judge scoring.
- Integrate observability tooling (Langfuse) for tracing LLM calls, tracking token costs, and managing prompt versions.
- Optimise inference pipelines for latency and cost: batching, caching, model selection.
- Collaborate with data scientists on model experimentation and with backend engineers on API design.
- Implement guardrails for LLM outputs: PII detection, faithfulness checking, and output validation.
- Design and maintain vector storage infrastructure using pgvector.

REQUIREMENTS
- 4+ years of experience in ML engineering or a related role (data engineering, backend engineering with ML focus).
- Strong proficiency in Python with production API experience (FastAPI preferred).
- Hands-on experience with LLMs: API integration (Anthropic, OpenAI), prompt engineering, and output parsing.
- Experience with embedding models and vector databases (pgvector, Pinecone, or Weaviate).
- Understanding of retrieval systems: sparse retrieval, dense retrieval, and reranking.
- Experience building evaluation and testing frameworks for ML systems.
- Comfortable with Docker, CI/CD, and cloud deployment (AWS preferred).

NICE TO HAVE
- Experience with LangGraph, LangChain, or similar LLM orchestration frameworks.
- Familiarity with Langfuse or similar observability tools for LLM applications.
- Experience with structured outputs from LLMs (Pydantic validation, retry strategies).
- Background in NLP or information retrieval research.
- Experience in recruitment or HR technology domain.
""",
    },
]


async def main() -> None:
    """Connect to the database, create tables, and seed all documents."""
    print("Initialising database (creating tables if needed)...")
    await init_db()

    all_documents = SEED_CVS + SEED_JDS

    async with async_session_factory() as session:
        # Check for existing data to avoid duplicates on re-run
        from sqlalchemy import select, func as sa_func

        result = await session.execute(
            select(sa_func.count()).select_from(Document)
        )
        existing_count = result.scalar_one()

        if existing_count > 0:
            print(
                f"Database already contains {existing_count} documents. "
                "Skipping seed to avoid duplicates."
            )
            print("To re-seed, delete existing documents first.")
            return

        print(f"Seeding {len(all_documents)} documents ({len(SEED_CVS)} CVs + {len(SEED_JDS)} JDs)...")

        for i, doc_data in enumerate(all_documents, start=1):
            doc = Document(
                title=doc_data["title"],
                content=doc_data["content"].strip(),
                doc_type=DocumentType(doc_data["doc_type"]),
            )
            session.add(doc)
            doc_type_label = "CV" if doc_data["doc_type"] == "cv" else "JD"
            print(f"  [{i}/{len(all_documents)}] {doc_type_label}: {doc_data['title']}")

        await session.commit()
        print(f"\nDone. Seeded {len(all_documents)} documents successfully.")


if __name__ == "__main__":
    asyncio.run(main())
