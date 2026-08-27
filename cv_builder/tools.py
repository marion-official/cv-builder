"""Read-only tool definitions exposing the candidate's stored data to Claude.

These tools are intentionally read-only: Claude can look up profile data to
tailor a CV, but cannot write to or modify the database.
"""

from cv_builder import db

TOOL_DEFINITIONS = [
    {
        "name": "get_profile",
        "description": (
            "Get the candidate's contact details, base professional summary, "
            "and career goals (name, email, phone, address, links)."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_experiences",
        "description": (
            "List all of the candidate's work experiences, each with company, "
            "role, location, dates, and the full set of achievement bullets on "
            "record. Use this to pick and rephrase the entries most relevant "
            "to the target role."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_education",
        "description": "List the candidate's education history.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_skills",
        "description": "List the candidate's recorded skills, grouped by category.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

_DISPATCH = {
    "get_profile": lambda conn, _input: db.get_profile(conn),
    "list_experiences": lambda conn, _input: db.list_experiences(conn),
    "list_education": lambda conn, _input: db.list_education(conn),
    "list_skills": lambda conn, _input: db.list_skills(conn),
}


def execute_tool(name: str, tool_input: dict, conn) -> object:
    handler = _DISPATCH.get(name)
    if handler is None:
        raise ValueError(f"Unknown tool: {name}")
    return handler(conn, tool_input)
