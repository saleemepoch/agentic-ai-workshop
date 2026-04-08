"""
Regex-based parsers for CVs and job descriptions.

The teaching point of this module: structural extraction does not need an LLM.
CVs and JDs are highly structured documents — sections, bullet lists, common
headings. Regex handles the structure for free in microseconds. Save the LLM
calls for jobs that genuinely need reasoning (semantic consolidation, scoring,
generation).

Interview talking points:
- Why not use an LLM for parsing? Because LLM calls are slow (~700ms) and
  expensive (~$0.005), and a regex does the same job in microseconds for free.
  The teaching principle is "use the right tool". Regex handles structure,
  LLMs handle semantics.
- How robust is regex parsing? For the document types in this workshop (CVs
  and JDs that follow common conventions), it's very robust. For arbitrary
  unstructured text it would not be — that's where LLM-based parsing earns
  its place.

The semantic chunker (`src/documents/chunker.py`) already detects sections.
We reuse those primitives here.
"""

import re

from src.documents.chunker import HEADING_PATTERNS, detect_sections


def _is_heading_line(line: str) -> bool:
    """Check whether a line matches any of the heading patterns."""
    line = line.strip()
    if not line:
        return False
    return any(pattern.match(line) for pattern in HEADING_PATTERNS)


def _heading_of(section: str) -> str:
    """Return the first non-blank line of a section as its heading."""
    for line in section.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def _body_of(section: str) -> str:
    """Return the section content with the heading line stripped."""
    lines = section.splitlines()
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip():
            body_start = i + 1
            break
    return "\n".join(lines[body_start:]).strip()


def _normalise_heading(heading: str) -> str:
    """Normalise a heading to a canonical lowercase key."""
    h = heading.strip().rstrip(":").lower()
    # Strip markdown markers
    h = re.sub(r"^#+\s*", "", h)
    return h


def parse_cv(content: str) -> dict:
    """Parse a CV into structured fields using regex only.

    Returns a dict with:
        - name: best guess at candidate name (first non-heading line)
        - sections: dict mapping normalised heading → body text
        - skills: list of strings if a SKILLS section was found, else []
        - section_count: how many sections were detected

    No LLM calls. Runs in microseconds.
    """
    sections = detect_sections(content)
    parsed_sections: dict[str, str] = {}

    # The candidate's name is the first non-blank line of the document. Many
    # CVs put the name in ALL CAPS, which would otherwise match a heading
    # pattern, so we don't filter heading-shaped lines here.
    name = ""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped:
            name = stripped
            break

    for section in sections:
        heading = _heading_of(section)
        body = _body_of(section)
        if not body:
            # The first "section" might just be the name preamble — skip it.
            continue
        key = _normalise_heading(heading)
        parsed_sections[key] = body

    # Extract skills as a list if there's a skills-like section
    skills: list[str] = []
    for key in ("skills", "technical skills", "core skills"):
        if key in parsed_sections:
            raw = parsed_sections[key]
            # Skills are usually comma-separated, sometimes line-separated
            tokens = re.split(r"[,;\n]", raw)
            skills = [t.strip() for t in tokens if t.strip()]
            break

    return {
        "name": name,
        "sections": parsed_sections,
        "skills": skills,
        "section_count": len(parsed_sections),
    }


def parse_jd_sections(content: str) -> dict:
    """Parse a JD into raw sections using regex only.

    Returns a dict with:
        - title: job title (first non-heading line)
        - sections: dict mapping normalised heading → body text
        - section_count: how many sections were detected

    Note: this returns the *structural* extraction. JDs often scatter
    requirements across multiple sections (responsibilities, requirements,
    nice-to-haves), so an LLM consolidation step is needed downstream to
    produce a clean requirements list. That's the `extract_requirements`
    agent node.
    """
    sections = detect_sections(content)
    parsed_sections: dict[str, str] = {}

    # Job title is the first non-blank line, even if it looks like a heading.
    title = ""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped:
            title = stripped
            break

    for section in sections:
        heading = _heading_of(section)
        body = _body_of(section)
        if not body:
            continue
        key = _normalise_heading(heading)
        parsed_sections[key] = body

    return {
        "title": title,
        "sections": parsed_sections,
        "section_count": len(parsed_sections),
    }
