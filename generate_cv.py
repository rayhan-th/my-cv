#!/usr/bin/env python3
"""Generate cv.typ from the website's markdown files using the modern-cv Typst package."""

import re
from pathlib import Path


def read_file(base, filename):
    """Read a markdown file, stripping YAML frontmatter."""
    text = (base / filename).read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            text = text[end + 3:]
    return text.strip()


def _convert_bold_italic(text):
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
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<https?://[^>]+>", "", text)
    return text.strip()


def parse_table(text):
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
    escaped = re.escape(heading)
    m = re.search(rf"^{escaped}\s*$", text, re.MULTILINE)
    if not m:
        return ""
    start = m.end()
    level = len(re.match(r"^#+", heading).group())
    end_pat = rf"^(?:#{{{1},{level}}}\s|---\s*$)"
    end_m = re.search(end_pat, text[start:], re.MULTILINE)
    if end_m:
        return text[start: start + end_m.start()].strip()
    return text[start:].strip()


def parse_dropdowns(text):
    results = []
    for m in re.finditer(
        r":::\{dropdown\}\s*(.+?)\n(?::open:\n)?(.*?)\n\s*:::[ \t]*$",
        text, re.DOTALL | re.MULTILINE,
    ):
        results.append((m.group(1).strip(), m.group(2).strip()))
    return results


def split_entries(text):
    return [e.strip() for e in re.split(r"\n\s*\n", text.strip()) if e.strip()]


def parse_bullets(text):
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
    parts = re.split(r"^###\s+", text, flags=re.MULTILINE)
    results = []
    for part in parts[1:]:
        lines = part.split("\n", 1)
        title = lines[0].strip()
        content = lines[1].strip() if len(lines) > 1 else ""
        results.append((title, content))
    return results


def parse_cards(text):
    results = []
    for m in re.finditer(
        r":::\{card\}[ \t]+([^\n]+?)\n:link:\s*(.+?)\n(.*?)\n:::(?![:\{])",
        text, re.DOTALL,
    ):
        name = m.group(1).strip()
        link = m.group(2).strip()
        desc = m.group(3).strip()
        desc = re.sub(r"```\{image\}.*?```", "", desc, flags=re.DOTALL)
        desc = re.sub(r"\n+", " ", desc).strip()
        if name:
            results.append((name, link, desc))
    return results


def table_to_items(text):
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


def content_with_table(text):
    table_match = re.search(r"^\|", text, re.MULTILINE)
    parts = []
    if table_match:
        before = text[: table_match.start()].strip()
        if before:
            parts.append(escape_typst(before))
        result = table_to_items(text[table_match.start():])
        if result:
            parts.append(result)
    elif text.strip():
        parts.append(escape_typst(text.strip()))
    return "\n\n".join(parts)


def gen_preamble():
    return (
        '#import "@preview/modern-cv:0.9.0": *\n'
        '\n'
        '#fa-version("6")\n'
        '#show "Résumé": "CV"\n'
        '\n'
        '#show: resume.with(\n'
        '  author: (\n'
        '    firstname: "Rayhan",\n'
        '    lastname: "Ahmed",\n'
        '    email: "rayhan.thkoeln@gmail.com",\n'
        '    phone: "(+49) 178-6957128",\n'
        '    homepage: "https://rayhan-th.github.io/my-cv",\n'
        '    github: "rayhan-th",\n'
        '    address: "Deutzer Ring 5, 50679 Cologne, Germany",\n'
        '    positions: (\n'
        '      "Hydrologist",\n'
        '      "GIS Specialist",\n'
        '    ),\n'
        '    custom: (\n'
        '      (text: "LinkedIn", icon: "linkedin", link: "https://linkedin.com/in/rayhan95ahmed"),\n'
        '      (text: "ResearchGate", icon: "researchgate", link: "https://researchgate.net/profile/Rayhan-Ahmed"),\n'
        '    ),\n'
        '  ),\n'
        '  profile-picture: none,\n'
        '  date: datetime.today().display(),\n'
        '  language: "en",\n'
        '  paper-size: "a4",\n'
        '  accent-color: default-accent-color,\n'
        '  colored-headers: true,\n'
        '  show-footer: true,\n'
        ')\n'
        '\n'
        '#set heading(bookmarked: true)\n'
        '#set document(title: "Rayhan Ahmed - CV")'
    )


def gen_education(about):
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


def gen_appointments(about):
    section = extract_section(about, "## Appointments")
    rows = parse_table(section)
    if not rows:
        return ""
    lines = ["= Professional Experience\n"]
    items = []
    for row in rows:
        period = escape_typst(row.get("Period", ""))
        position = escape_typst(row.get("Position", ""))
        items.append(f"  - {period}: {position}")
    lines.append("#resume-item[\n" + "\n".join(items) + "\n]")
    return "\n\n".join(lines)


def gen_research_areas(research):
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


def gen_awards(awards_text):
    rows = parse_table(awards_text)
    if not rows:
        return ""
    lines = ["= Awards and Scholarships\n"]
    items = []
    for row in rows:
        year = strip_markdown(row.get("Year", ""))
        award = escape_typst(row.get("Award", ""))
        items.append(f"  - {year}: {award}")
    lines.append("#resume-item[\n" + "\n".join(items) + "\n]")
    return "\n\n".join(lines)


def gen_books(research):
    section = extract_section(research, "## Books")
    if not section:
        return ""
    bullets = parse_bullets(section)
    if not bullets:
        return ""
    items = [f"  - {escape_typst(b)}" for b in bullets]
    return "= Books\n\n#resume-item[\n" + "\n\n".join(items) + "\n]"


def gen_publications(research):
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
    return "\n".join(lines)


def gen_grants(research):
    grants = extract_section(research, "## Grants")
    if not grants:
        return ""
    lines = ["= Grants"]
    funded = extract_section(grants, "### Funded")
    if funded:
        lines.append("\n== Funded")
        for label, content in parse_dropdowns(funded):
            entries = split_entries(content)
            items = [f"  - {escape_typst(e)}" for e in entries if e]
            if items:
                lines.append(f"\n=== {label}\n")
                lines.append("#resume-item[\n" + "\n\n".join(items) + "\n]")
    pending = extract_section(grants, "### Pending")
    if pending:
        lines.append("\n== Pending")
        entries = split_entries(pending)
        items = [f"  - {escape_typst(e)}" for e in entries if e]
        if items:
            lines.append("\n#resume-item[\n" + "\n\n".join(items) + "\n]")
    return "\n".join(lines)


def gen_software(software):
    cards = parse_cards(software)
    if not cards:
        return ""
    lines = ["= Technical Skills", ""]
    items = []
    for name, link, desc in cards:
        escaped_name = escape_typst(name)
        if desc:
            items.append(f"  - *{escaped_name}*: {escape_typst(desc)}")
        else:
            items.append(f"  - *{escaped_name}*")
    lines.append("#resume-item[\n" + "\n".join(items) + "\n]")
    return "\n".join(lines)


def gen_teaching(teaching):
    lines = ["= Training and Certifications"]
    online = extract_section(teaching, "## Self-Paced Online Courses")
    if online:
        rows = parse_table(online)
        if rows:
            lines.append("\n")
            items = []
            for row in rows:
                course = escape_typst(row.get("Course", ""))
                title = escape_typst(row.get("Title", ""))
                website = escape_typst(row.get("Website", ""))
                parts = [f"{course}: {title}"]
                if website:
                    parts.append(website)
                items.append(f"  - {', '.join(parts)}")
            lines.append("#resume-item[\n" + "\n".join(items) + "\n]")
    return "\n".join(lines)


def gen_mentoring(teaching):
    return ""


def _gen_talks_section(talks, heading, cv_title, include_summary=False):
    section = extract_section(talks, heading)
    if not section:
        return ""
    lines = [f"= {cv_title}"]
    if include_summary:
        m = re.search(r"^\(.+\)$", section, re.MULTILINE)
        if m:
            lines.append(f"\n{escape_typst(m.group())}")
    dropdowns = parse_dropdowns(section)
    for label, content in dropdowns:
        bullets = parse_bullets(content)
        if bullets:
            items = [f"  - {escape_typst(b)}" for b in bullets]
            lines.append(f"\n== {label}\n")
            lines.append("#resume-item[\n" + "\n".join(items) + "\n]")
    return "\n".join(lines)


def gen_workshops(talks):
    return _gen_talks_section(talks, "## Workshop Host", "Workshops")


def gen_invited_talks(talks):
    return _gen_talks_section(talks, "## Invited Talks", "Invited Talks", include_summary=True)


def gen_conf_proceedings(talks):
    section = extract_section(talks, "## Conference Proceedings")
    if not section:
        return ""
    entries = split_entries(section)
    items = [f"  - {escape_typst(e)}" for e in entries if e]
    if not items:
        return ""
    return "= Conference Proceedings\n\n#resume-item[\n" + "\n".join(items) + "\n]"


def gen_conf_presentations(talks):
    return _gen_talks_section(talks, "## Conference Presentations", "Conference Presentations")


def gen_services(services):
    parts = []
    prof = extract_section(services, "## Professional Services")
    if prof:
        parts.append("= Professional Services\n")
        result = table_to_items(prof)
        if result:
            parts.append(result)
    return "\n\n".join(p for p in parts if p)


def gen_languages(about):
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


def main():
    base = Path(__file__).parent
    pages = base / "pages"

    about = read_file(pages, "about.md")
    research = read_file(pages, "research.md")
    software = read_file(pages, "software.md")
    teaching = read_file(pages, "teaching.md")
    talks = read_file(pages, "talks.md")
    awards = read_file(pages, "awards.md")
    services = read_file(pages, "services.md")

    sections = [
        gen_preamble(),
        gen_education(about),
        gen_appointments(about),
        gen_software(software),
        gen_research_areas(research),
        gen_publications(research),
        gen_conf_presentations(talks),
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