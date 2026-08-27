"""Drives Claude through a tool-use loop to produce tailored CV content.

Claude only ever sees data through the read-only tools in tools.py, and only
ever hands back content through the `submit_tailored_cv` tool, whose schema
we enforce below. This keeps data retrieval and structured output separate
from PDF layout, which is handled deterministically in pdf.py.
"""

import json
import os

import anthropic

from cv_builder import tools

DEFAULT_MODEL = "claude-sonnet-5"

SUBMIT_TOOL = {
    "name": "submit_tailored_cv",
    "description": (
        "Submit the final tailored CV content once you have gathered the "
        "candidate's data and selected/rephrased the most relevant items "
        "for the target role. Call this exactly once, as the last step."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "contact": {
                "type": "object",
                "properties": {
                    "full_name": {"type": "string"},
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                    "address": {"type": "string"},
                    "linkedin": {"type": "string"},
                    "website": {"type": "string"},
                },
                "required": ["full_name"],
            },
            "summary": {
                "type": "string",
                "description": "A 2-4 sentence professional summary tailored to the target role.",
            },
            "experiences": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "company": {"type": "string"},
                        "role": {"type": "string"},
                        "location": {"type": "string"},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                        "bullets": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["company", "role", "bullets"],
                },
            },
            "education": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "institution": {"type": "string"},
                        "degree": {"type": "string"},
                        "field": {"type": "string"},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                    },
                    "required": ["institution"],
                },
            },
            "skills": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Skills ordered by relevance to the target role.",
            },
            "projects": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "url": {"type": "string"},
                        "bullets": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["name"],
                },
            },
            "certifications": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "issuer": {"type": "string"},
                        "date": {"type": "string"},
                    },
                    "required": ["name"],
                },
            },
        },
        "required": ["contact", "summary", "experiences", "skills"],
    },
}

SYSTEM_PROMPT = """You are a CV tailoring assistant. You have tools to fetch \
a candidate's real, on-file data (profile, experiences, education, skills, \
projects, certifications). You do not know anything about the candidate \
except what those tools return.

Rules:
- Always call the read-only tools first to gather the candidate's actual data. \
Never invent employers, dates, degrees, skills, projects, or certifications \
that were not returned by a tool.
- You may select a subset of experiences/bullets/skills/projects and rephrase \
bullet wording to emphasize relevance to the target role, but do not fabricate \
accomplishments that aren't grounded in the retrieved bullets.
- Only include projects that are relevant to the target role; it's fine to \
submit no projects at all if none of them add value for this application. The \
same applies to certifications: include the ones relevant to the role, and \
omit the rest.
- The candidate's profile may include a base `summary` and `career_goals`. \
Treat these as seed material, not fixed text: rewrite the summary for the \
`submit_tailored_cv` output so it emphasizes the parts of the candidate's \
background and goals most relevant to the target role, rather than copying \
the stored summary verbatim. If no base summary is on file, write one from \
scratch grounded only in the retrieved experiences, education, and skills.
- Once you have enough information, call `submit_tailored_cv` exactly once \
with the final content. That call ends the task.
"""


def generate_tailored_cv(conn, company: str, role: str, job_description: str,
                          model: str = DEFAULT_MODEL) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set")

    client = anthropic.Anthropic(api_key=api_key)

    messages = [
        {
            "role": "user",
            "content": (
                f"Tailor my CV for the role '{role}' at '{company}'.\n\n"
                f"Job description:\n{job_description}"
            ),
        }
    ]

    all_tools = tools.TOOL_DEFINITIONS + [SUBMIT_TOOL]

    for _ in range(10):  # safety bound on tool-use round trips
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=all_tools,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            raise RuntimeError(
                "Claude ended the conversation without submitting a CV "
                f"(stop_reason={response.stop_reason!r})"
            )

        tool_results = []
        submitted = None

        for block in response.content:
            if block.type != "tool_use":
                continue

            if block.name == "submit_tailored_cv":
                submitted = block.input
                # Acknowledge the tool call even though we're about to return,
                # since Anthropic's API requires a result for every tool_use block.
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Received.",
                    }
                )
                continue

            result = tools.execute_tool(block.name, block.input, conn)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                }
            )

        if submitted is not None:
            return submitted

        messages.append({"role": "user", "content": tool_results})

    raise RuntimeError("Exceeded max tool-use round trips without a submitted CV")
