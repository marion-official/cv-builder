"""MCP server exposing full read/write access to the CV builder's data.

Unlike cv_builder/tools.py (deliberately read-only, used by the internal
tailoring agent), this wraps cv_builder.db directly so an MCP client such as
Claude Desktop can manage the candidate's data through chat: adding
experience, education, skills, projects, and certifications, and rendering
tailored content to a PDF.

Run with: pipenv run python mcp_server.py
"""

from pathlib import Path

from mcp.server.mcpserver import MCPServer

from cv_builder import db, pdf

REPO_ROOT = Path(__file__).resolve().parent

server = MCPServer("cv-builder")


def _conn():
    return db.get_connection()


def _resolve_output_path(output_path: str) -> str:
    path = Path(output_path).expanduser()
    if not path.is_absolute():
        path = REPO_ROOT / path
    return str(path)


@server.tool()
def get_profile() -> dict | None:
    """Get the candidate's contact details, professional summary, and career goals."""
    return db.get_profile(_conn())


@server.tool()
def set_profile(
    full_name: str,
    email: str | None = None,
    phone: str | None = None,
    address: str | None = None,
    linkedin: str | None = None,
    website: str | None = None,
    summary: str | None = None,
    career_goals: str | None = None,
) -> str:
    """Create or update the candidate's profile.

    full_name always overwrites; every other field only overwrites the
    stored value if a non-null value is passed.
    """
    db.set_profile(
        _conn(), full_name, email=email, phone=phone, address=address,
        linkedin=linkedin, website=website, summary=summary,
        career_goals=career_goals,
    )
    return "Profile saved."


@server.tool()
def list_experiences() -> list[dict]:
    """List all of the candidate's work experiences, most recent first."""
    return db.list_experiences(_conn())


@server.tool()
def add_experience(
    company: str,
    role: str,
    location: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    bullets: list[str] | None = None,
) -> str:
    """Add a work experience entry."""
    exp_id = db.add_experience(
        _conn(), company, role, location=location, start_date=start_date,
        end_date=end_date, bullets=bullets,
    )
    return f"Experience #{exp_id} added."


@server.tool()
def list_education() -> list[dict]:
    """List the candidate's education history, most recent first."""
    return db.list_education(_conn())


@server.tool()
def add_education(
    institution: str,
    degree: str | None = None,
    field: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    details: str | None = None,
) -> str:
    """Add an education entry."""
    edu_id = db.add_education(
        _conn(), institution, degree=degree, field=field,
        start_date=start_date, end_date=end_date, details=details,
    )
    return f"Education #{edu_id} added."


@server.tool()
def list_skills() -> list[dict]:
    """List the candidate's recorded skills, grouped by category."""
    return db.list_skills(_conn())


@server.tool()
def add_skills(names: list[str], category: str | None = None) -> str:
    """Add one or more skills under the same category."""
    conn = _conn()
    for name in names:
        db.add_skill(conn, name, category=category)
    return f"Added {len(names)} skill(s)."


@server.tool()
def list_projects() -> list[dict]:
    """List the candidate's side projects, open-source contributions, and technical writing."""
    return db.list_projects(_conn())


@server.tool()
def add_project(
    name: str,
    url: str | None = None,
    bullets: list[str] | None = None,
) -> str:
    """Add a project or piece of technical writing."""
    project_id = db.add_project(_conn(), name, url=url, bullets=bullets)
    return f"Project #{project_id} added."


@server.tool()
def list_certifications() -> list[dict]:
    """List the candidate's certifications, most recent first."""
    return db.list_certifications(_conn())


@server.tool()
def add_certification(
    name: str,
    issuer: str | None = None,
    date: str | None = None,
) -> str:
    """Add a certification."""
    cert_id = db.add_certification(_conn(), name, issuer=issuer, date=date)
    return f"Certification #{cert_id} added."


@server.tool()
def render_cv(content: dict, output_path: str = "cv.pdf") -> str:
    """Render tailored CV content to a PDF and return the file path.

    `content` must have a `contact` object (at least `full_name`), plus
    optional `summary`, `experiences`, `education`, `skills`, `projects`,
    and `certifications` arrays, matching the shape of the data returned by
    the list_* tools above. Select and rephrase the candidate's real,
    on-file data for the target role yourself before calling this — it only
    renders the PDF, it does not fetch or tailor anything.
    """
    resolved_path = _resolve_output_path(output_path)
    return pdf.render_cv(content, resolved_path)


if __name__ == "__main__":
    server.run()
