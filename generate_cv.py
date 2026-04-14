#!/usr/bin/env python3
"""Generate cv.typ from the website's markdown files using the modern-cv Typst package.

Reads structured data from pages/about.md, pages/research.md, pages/software.md,
pages/teaching.md, pages/talks.md, pages/awards.md, and pages/services.md, then
generates a complete Typst CV file using the modern-cv package for styling.

Usage: python generate_cv.py
Output: cv.typ (compile with: typst compile cv.typ cv.pdf --font-path ./fonts)
"""
import re
from pathlib import Path

# ============================================================================
# Utility functions
# ============================================================================


def read_file(base, filename):
    """Read a markdown file, stripping YAML frontmatter."""
    text = (base / filename).read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            text = text[end + 3 :]
    return text.strip()


def _convert_bold_italic(text):
    """Convert markdown **bold** -> Typst *bold* and *italic* -> _italic_."""
    bolds = []

    def save_bold(m):
        bolds.append(m.group(1))
        return f"\x00B{len(bolds) - 1}\x00"

    text = re.sub(r"\*\*(.+?)\*\*", save_bold, text)
    text = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"_\1_", text)
    for i, b in enumerate(bolds):
        text = text.replace(f"\x00B{i}\x00", f"*{b}*")
    return text


def escape_typst(text):
    """Convert markdown-formatted text to Typst content mode."""
    if not text:
        return ""

    links = []

    def save_bare_url(m):
        url = m.group(1).replace('"', '\\"')
        links.append(f'#link("{url}")')
        return f"\x00L{len(links) - 1}\x00"

    text = re.sub(r"<(https?://[^>]+)>", save_bare_url, text)

    def save_md_link(m):
        lt = m.group(1)
        url = m.group(2).replace('"', '\\"')
        lt = lt.replace("\\", "\\\\")
        lt = lt.replace("#", "\\#")
        lt = lt.replace("@", "\\@")
        lt = lt.replace("$", "\\$")
        lt = _convert_bold_italic(lt)
        links.append(f'#link("{url}")[{lt}]')
        return f"\x00L{len(links) - 1}\x00"

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", save_md_link, text)

    text = text.replace("\\", "\\\\")
    text = text.replace("#", "\\#")
    text = text.replace("@", "\\@")
    text = text.replace("$", "\\$")

    text = _convert_bold_italic(text)

    for i, link in enumerate(links):
        text = text.replace(f"\x00L{i}\x00", link)

    return text


def strip_markdown(text):
    """Remove markdown formatting, returning plain text."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<https?://[^>]+>", "", text)
    return text.strip()


def parse_table(text):
    """Parse a markdown table into a list of row dicts."""
    lines = [l.strip() for l in text.strip().split("\n") if l.strip().startswith("|")]
    if len(lines) < 3:
        return []

    def split_row(line):
        cells = [c.strip() for c in line.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        return cells

    headers = split_row(lines[0])
    rows = []
    for line in lines[2:]:
        cells = split_row(line)
        row = {}
        for i, h in enumerate(headers):
            row[h] = cells[i] if i < len(cells) else ""
        rows.append(row)
    return rows


def extract_section(text, heading):
    """Extract content between a heading and the next heading of same/higher level or ---."""
    escaped = re.escape(heading)
    m = re.search(rf"^{escaped}\s*$", text, re.MULTILINE)
    if not m:
        return ""
    start = m.end()
    level = len(re.match(r"^#+", heading).group())
    end_pat = rf"^(?:#{{{1},{level}}}\s|---\s*$)"
    end_m = re.search(end_pat, text[start:], re.MULTILINE)
    if end_m:
        return text[start : start + end_m.start()].strip()
    return text[start:].strip()


def parse_dropdowns(text):
    """Parse :::{dropdown} blocks into list of (label, content) tuples."""
    results = []
    for m in re.finditer(
        r":::\{dropdown\}\s*(.+?)\n(?::open:\n)?(.*?)\n\s*:::[ \t]*$",
        text,
        re.DOTALL | re.MULTILINE,
    ):
        results.append((m.group(1).strip(), m.group(2).strip()))
    return results


def split_entries(text):
    """Split text into entries separated by blank lines."""
    return [e.strip() for e in re.split(r"\n\s*\n", text.strip()) if e.strip()]


def parse_bullets(text):
    """Parse bullet list items, joining continuation lines."""
    items = []
    current = None
    for line in text.split("\n"):
        m = re.match(r"^[\-\*]\s+(.+)", line)
        if m:
            if current is not None:
                items.append(current)
            current = m.group(1)
        elif current is not None and line.strip():
            current += " " + line.strip()
    if current is not None:
        items.append(current)
    return items


def find_subsections(text):
    """Split text at ### headings, returning list of (title, content)."""
    parts = re.split(r"^###\s+", text, flags=re.MULTILINE)
    results = []
    for part in parts[1:]:
        lines = part.split("\n", 1)
        title = lines[0].strip()
        content = lines[1].strip() if len(lines) > 1 else ""
        results.append((title, content))
    return results


def table_to_items(text):
    """Convert markdown table rows to Typst resume-item bullet list."""
    rows = parse_table(text)
    if not rows:
        return ""
    items = []
    for row in rows:
        vals = [escape_typst(v) for v in row.values() if v.strip()]
        if len(vals) >= 2:
            items.append(f"  - {vals[0]}: {', '.join(vals[1:])}")
        elif vals:
            items.append(f"  - {vals[0]}")
    return "#resume-item[\n" + "\n".join(items) + "\n]" if items else ""


# ============================================================================
# Section generators
# ============================================================================


def gen_preamble():
    """Generate Typst preamble with modern-cv import and author config."""
    return """#import "@preview/modern-cv:0.9.0": *

// Use Font Awesome 6 icons and replace "Résumé" with "CV" in footer
#fa-version("6")
#show "Résumé": "CV"

#show: resume.with(
  author: (
    firstname: "Rayhan",
    lastname: "Ahmed",
    email: "rayhan.thkoeln@gmail.com",
    phone: "(+49) 178-6957128",
    homepage: "https://rayhan-th.github.io/my-cv",
    github: "rayhan-th",
    address: "Deutzer Ring 5, 50679 Cologne, Germany",
    positions: (
      "Hydrologist",
      "GIS Specialist",
    ),
    custom: (
      (text: "LinkedIn", icon: "linkedin", link: "https://linkedin.com/in/rayhan95ahmed"),
      (text: "ResearchGate", icon: "researchgate", link: "https://researchgate.net/profile/Rayhan-Ahmed-4"),
    ),
  ),
  profile-picture: none,
  date: datetime.today().display(),
  language: "en",
  paper-size: "a4",
  accent-color: default-accent-color,
  colored-headers: true,
  show-footer: true,
)

// Enable PDF bookmarks for section navigation
#set heading(bookmarked: true)

// Set PDF document title
#set document(title: "Rayhan Ahmed - CV")"""


def gen_education(about):
    """Generate Education section from pages/about.md."""
    section = extract_section(about, "## Education")
    rows = parse_table(section)
    if not rows:
        return ""
    lines = ["= Education\n"]
    for row in rows:
        year = strip_markdown(row.get("Year", ""))
        degree = escape_typst(row.get("Degree", ""))
        institution = escape_typst(row.get("Institution", ""))
        dissertation = escape_typst(row.get("Dissertation/Thesis", ""))
        lines.append(
            f"#resume-entry(\n"
            f"  title: [{degree}],\n"
            f"  location: [{institution}],\n"
            f"  date: [{year}],\n"
            f"  description: [{dissertation}],\n"
            f")"
        )
    return "\n\n".join(lines)


def gen_experience(experience):
    """Generate Professional Experience section from pages/experience.md."""
    lines = ["= Professional Experience\n"]

    # Parse ### headings as job entries
    entries = re.split(r"^### ", experience, flags=re.MULTILINE)
    for entry in entries[1:]:
        entry_lines = entry.strip().split("\n")
        title_line = entry_lines[0].strip()

        # Extract date from title line e.g. "Job Title *(date)*"
        date_match = re.search(r"\*\((.+?)\)\*", title_line)
        date = date_match.group(1) if date_match else ""
        title = re.sub(r"\s*\*\(.+?\)\*", "", title_line).strip()

        # Extract organisation (bold line after title)
        org = ""
        description = ""
        bullets = []
        for line in entry_lines[1:]:
            line = line.strip()
            if line.startswith("**") and not org:
                org = strip_markdown(line)
            elif line.startswith("- "):
                bullets.append(line[2:].strip())
            elif line.startswith("> "):
                bullets.append(line[2:].strip())

        lines.append(
            f"#resume-entry(\n"
            f"  title: [{escape_typst(title)}],\n"
            f"  location: [{escape_typst(org)}],\n"
            f"  date: [{escape_typst(date)}],\n"
            f"  description: [],\n"
            f")"
        )
        if bullets:
            items = [f"  - {escape_typst(b)}" for b in bullets if b]
            lines.append("#resume-item[\n" + "\n".join(items) + "\n]")

    return "\n\n".join(lines)


def gen_skills(skills):
    """Generate Technical Skills section from pages/skills.md."""
    lines = ["= Technical Skills\n"]

    # Find all tables with their preceding ### heading
    subsections = find_subsections(skills)
    for title, content in subsections:
        rows = parse_table(content)
        if not rows:
            continue
        # Collect all values from Tool/Skill column
        skill_vals = []
        for row in rows:
            tool = row.get("Tool / Skill", row.get("Tool", row.get("Language", "")))
            if tool:
                skill_vals.append(f'"{escape_typst(tool)}"')
        if skill_vals:
            lines.append(
                f"#resume-skill-item(\n"
                f'  "{escape_typst(title)}",\n'
                f"  ({', '.join(skill_vals)}),\n"
                f")"
            )

    return "\n\n".join(lines)


def gen_research_areas(research):
    """Generate Research Areas section from pages/research.md."""
    section = extract_section(research, "## Research Areas")
    if not section:
        return ""
    bullets = parse_bullets(section)
    if not bullets:
        return ""
    items = tuple(f'"{b}"' for b in bullets)
    return (
        "= Research Areas\n\n"
        "#resume-skill-item(\n"
        '  "Research Focus",\n'
        f"  ({', '.join(items)}),\n"
        ")"
    )


def gen_publications(research):
    """Generate Refereed Publications section from pages/research.md."""
    section = extract_section(research, "## Refereed Publications")
    if not section:
        return ""

    summary = ""
    m = re.search(r"\*\*Published\*\*.*$", section, re.MULTILINE)
    if m:
        summary = escape_typst(m.group())

    dropdowns = parse_dropdowns(section)
    lines = [f"= Refereed Publications\n\n{summary}"]

    for label, content in dropdowns:
        entries = split_entries(content)
        items = [f"  - {escape_typst(e)}" for e in entries if e]
        if items:
            lines.append(f"\n== {label}\n")
            lines.append("#resume-item[\n" + "\n\n".join(items) + "\n]")

    # Conference paper
    conf = extract_section(research, "## Conference Papers")
    if conf:
        bullets = parse_bullets(conf)
        if bullets:
            lines.append("\n== Conference Papers\n")
            items = [f"  - {escape_typst(b)}" for b in bullets]
            lines.append("#resume-item[\n" + "\n\n".join(items) + "\n]")

    # Master thesis
    thesis = extract_section(research, "## Master Thesis")
    if not thesis:
        thesis = extract_section(research, "## Master Thesis *(ongoing)*")
    if thesis:
        lines.append("\n== Master Thesis (ongoing)\n")
        lines.append(f"#resume-item[\n  - {escape_typst(thesis[:300])}\n]")

    return "\n".join(lines)


def gen_awards(awards_text):
    """Generate Awards & Scholarships section from pages/awards.md."""
    lines = ["= Awards and Scholarships\n"]
    items = []

    # Try table format first
    rows = parse_table(awards_text)
    if rows:
        for row in rows:
            year = strip_markdown(row.get("Year", ""))
            award = escape_typst(row.get("Award", ""))
            items.append(f"  - {year}: {award}")
    else:
        # Parse ### heading format
        subsections = find_subsections(awards_text)
        for title, content in subsections:
            # Extract year from title e.g. "DAAD Scholarship *(2023–2025)*"
            date_match = re.search(r"\*\((.+?)\)\*", title)
            date = date_match.group(1) if date_match else ""
            clean_title = re.sub(r"\s*\*\(.+?\)\*", "", title).strip()
            # Get institution from first line of content
            first_line = content.split("\n")[0].strip() if content else ""
            institution = strip_markdown(first_line)
            if date:
                items.append(f"  - *{date}*: {escape_typst(clean_title)} -- {escape_typst(institution)}")
            else:
                items.append(f"  - {escape_typst(clean_title)} -- {escape_typst(institution)}")

    if items:
        lines.append("#resume-item[\n" + "\n".join(items) + "\n]")
    return "\n\n".join(lines)


def gen_languages(about):
    """Generate Languages section from pages/about.md."""
    section = extract_section(about, "## Languages")
    rows = parse_table(section)
    if not rows:
        return ""
    lines = ["= Languages\n"]
    items = []
    for row in rows:
        lang = escape_typst(row.get("Language", ""))
        level = escape_typst(row.get("Level", ""))
        items.append(f"  - *{lang}*: {level}")
    lines.append("#resume-item[\n" + "\n".join(items) + "\n]")
    return "\n\n".join(lines)


def gen_teaching(teaching):
    """Generate Training & Certifications section from pages/teaching.md."""
    lines = ["= Training and Certifications"]
    online = extract_section(teaching, "## Self-Paced Online Courses")
    if online:
        rows = parse_table(online)
        if rows:
            items = []
            for row in rows:
                course = escape_typst(row.get("Course", ""))
                title = escape_typst(row.get("Title", ""))
                website = escape_typst(row.get("Website", ""))
                entry = f"{course}: {title}"
                if website:
                    entry += f" ({website})"
                items.append(f"  - {entry}")
            lines.append("\n#resume-item[\n" + "\n".join(items) + "\n]")
    return "\n".join(lines)


def gen_services(services):
    """Generate Professional Services section from pages/services.md."""
    parts = []
    prof = extract_section(services, "## Professional Services")
    if prof:
        parts.append("= Professional Services\n")
        result = table_to_items(prof)
        if result:
            parts.append(result)
    return "\n\n".join(p for p in parts if p)


# ============================================================================
# Main
# ============================================================================


def main():
    """Read website markdown files and generate cv.typ."""
    base = Path(__file__).parent
    pages = base / "pages"

    about = read_file(pages, "about.md")
    research = read_file(pages, "research.md")
    skills = read_file(pages, "skills.md")
    experience = read_file(pages, "experience.md")
    teaching = read_file(pages, "teaching.md")
    talks = read_file(pages, "talks.md")
    awards = read_file(pages, "awards.md")
    services = read_file(pages, "services.md")

    sections = [
        gen_preamble(),
        gen_education(about),
        gen_experience(experience),
        gen_skills(skills),
        gen_research_areas(research),
        gen_publications(research),
        gen_awards(awards),
        gen_languages(about),
        gen_teaching(teaching),
        gen_services(services),
    ]

    output = "\n\n".join(s for s in sections if s)
    out_path = base / "cv.typ"
    out_path.write_text(output, encoding="utf-8")
    print(f"Generated {out_path} ({len(output):,} bytes)")


if __name__ == "__main__":
    main()
