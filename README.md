# CV Builder

**CV Builder** turns a local SQLite database of your career history into a
job-tailored CV. Add your profile, experience, education, skills, projects,
and certifications once — then hand Claude a company, role, and job
description, and it fetches your real data through read-only tools, picks
and rephrases the most relevant parts, and hands back a clean PDF. No
fabricated experience, no copy-pasting into a template by hand.

Claude never sees your data hardcoded into a prompt. Instead, it is given a
set of read-only tools to look up your profile, experiences, education,
skills, projects, and certifications from the database, then selects and
rephrases the most relevant material for the target role. The result is
rendered deterministically to PDF — Claude controls the content, not the
page layout.

## How it works

1. You store your data once via the CLI (`set-profile`, `add-experience`,
   `add-education`, `add-skill`, `add-project`, `add-certification`).
2. When you run `generate`, Claude is given a company, role, and job
   description, plus six read-only tools:
   - `get_profile`
   - `list_experiences`
   - `list_education`
   - `list_skills`
   - `list_projects`
   - `list_certifications`
3. Claude calls these tools to fetch your real data, selects/rephrases the
   most relevant experiences and skills for the job, and returns everything
   through a `submit_tailored_cv` tool call with a fixed JSON schema.
4. That JSON is rendered into a PDF using a fixed ReportLab layout (no LLM
   involvement in formatting), written to disk.

## Install

Requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

You'll also need an Anthropic API key with access to Claude. Either export it
directly:

```bash
export ANTHROPIC_API_KEY=sk-...
```

or copy `.env.example` to `.env` and fill it in — it's loaded automatically
and is already gitignored, so your key never gets committed:

```bash
cp .env.example .env
# then edit .env and set ANTHROPIC_API_KEY=sk-...
```

## Usage

### 1. Add your data

Set your contact details, summary, and career goals:

```bash
python main.py set-profile \
  --name "Jane Doe" \
  --email jane@example.com \
  --phone "+44 000 000000" \
  --address "London, UK" \
  --linkedin "linkedin.com/in/janedoe" \
  --summary "Backend engineer with 6 years of experience in distributed systems." \
  --career-goals "Looking to move into a staff-level platform engineering role."
```

`--summary` and `--career-goals` are optional seed material: when generating a
tailored CV, Claude rewrites the summary for the target role rather than
copying it verbatim, using your career goals to steer emphasis.

Add a work experience (repeat `--bullet` for each achievement):

```bash
python main.py add-experience \
  --company "Acme Corp" \
  --role "Senior Software Engineer" \
  --location "London" \
  --start "2022" --end "Present" \
  --bullet "Built a distributed monitoring platform handling 10k events/sec." \
  --bullet "Led a team of 4 engineers across two time zones."
```

Add education:

```bash
python main.py add-education \
  --institution "University of Somewhere" \
  --degree "BSc" --field "Computer Science" \
  --start 2015 --end 2018
```

Add skills (space-separated, one `--category` per call):

```bash
python main.py add-skill --name Python SQL Kubernetes --category "Technical"
```

Add a project or piece of technical writing (repeat `--bullet` for each
description point):

```bash
python main.py add-project \
  --name "Open-source monitoring CLI" \
  --url "https://github.com/janedoe/monitoring-cli" \
  --bullet "Built a Python CLI for programmatic alert and configuration management."
```

Add a certification:

```bash
python main.py add-certification \
  --name "Certified Kubernetes Administrator" \
  --issuer "CNCF" \
  --date "2024"
```

Review everything on file at any time:

```bash
python main.py list
```

All data lives in `cv_data.db` (SQLite), created automatically in the
project directory on first use.

### 2. Generate a tailored CV

From an inline job description:

```bash
python main.py generate \
  --company "Acme Corp" \
  --role "Senior Backend Engineer" \
  --jd "We're looking for someone with strong distributed systems experience..." \
  --output acme_cv.pdf
```

Or from a job description file:

```bash
python main.py generate \
  --company "Acme Corp" \
  --role "Senior Backend Engineer" \
  --jd-file jd.txt \
  --output acme_cv.pdf
```

Optional: pick a different model with `--model` (defaults to
`claude-sonnet-5`).

### 3. Use it from Claude Desktop (MCP)

`mcp_server.py` exposes the same data through the Model Context Protocol, so
you can manage your CV directly in a Claude Desktop chat instead of the CLI.
Unlike the read-only tools used by `generate`, this server is read/write:
add/update your profile, experiences, education, skills, projects, and
certifications, and render a tailored PDF, all from chat. Claude Desktop
does the tailoring reasoning itself (it's already a model), so this server
doesn't call the Anthropic API on its own — no `ANTHROPIC_API_KEY` needed to
run it.

Add it to Claude Desktop's config
(`~/Library/Application Support/Claude/claude_desktop_config.json` on
macOS):

```json
{
  "mcpServers": {
    "cv-builder": {
      "command": "/absolute/path/to/cv-builder/.venv/bin/python",
      "args": ["/absolute/path/to/cv-builder/mcp_server.py"]
    }
  }
}
```

Restart Claude Desktop, and the `cv-builder` tools (`get_profile`,
`set_profile`, `list_experiences`, `add_experience`, `list_education`,
`add_education`, `list_skills`, `add_skills`, `list_projects`,
`add_project`, `list_certifications`, `add_certification`, `render_cv`)
become available in chat. Verify what a chat session changed with
`python main.py list` or by asking the `cv-builder` MCP tools themselves —
both read the same `cv_data.db`.

## Project layout

```
main.py                 CLI entry point
mcp_server.py            MCP server: read/write access to your data from an MCP client (e.g. Claude Desktop)
cv_builder/db.py         SQLite schema and read/write functions
cv_builder/tools.py       Read-only tool definitions Claude uses to fetch your data during `generate`
cv_builder/agent.py       Tool-use loop that drives Claude to produce tailored CV content
cv_builder/pdf.py         Deterministic PDF rendering (ReportLab)
```

## Notes

- Claude is instructed not to fabricate employers, dates, degrees, or
  skills — only to select and rephrase from what the tools return — but
  this is prompt-level guidance, not an enforced guarantee. Review generated
  CVs before sending them out.
- The `generate` CLI command's tools are read-only by design: Claude can
  look up your data but cannot modify it there. `mcp_server.py` is the
  exception — it's read/write on purpose, since it's meant for you to
  manage your own data through chat.
