import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from cv_builder import db
from cv_builder.agent import generate_tailored_cv
from cv_builder.pdf import render_cv

load_dotenv(Path(__file__).resolve().parent / ".env")


def cmd_set_profile(args):
    conn = db.get_connection()
    db.set_profile(
        conn,
        full_name=args.name,
        email=args.email,
        phone=args.phone,
        address=args.address,
        linkedin=args.linkedin,
        website=args.website,
        summary=args.summary,
    )
    print("Profile saved.")


def cmd_add_experience(args):
    conn = db.get_connection()
    exp_id = db.add_experience(
        conn,
        company=args.company,
        role=args.role,
        location=args.location,
        start_date=args.start,
        end_date=args.end,
        bullets=args.bullet or [],
    )
    print(f"Experience #{exp_id} added.")


def cmd_add_education(args):
    conn = db.get_connection()
    edu_id = db.add_education(
        conn,
        institution=args.institution,
        degree=args.degree,
        field=args.field,
        start_date=args.start,
        end_date=args.end,
        details=args.details,
    )
    print(f"Education #{edu_id} added.")


def cmd_add_skill(args):
    conn = db.get_connection()
    for name in args.name:
        db.add_skill(conn, name=name, category=args.category)
    print(f"Added {len(args.name)} skill(s).")


def cmd_list(args):
    conn = db.get_connection()
    print("Profile:", db.get_profile(conn))
    print("\nExperiences:")
    for exp in db.list_experiences(conn):
        print(" -", exp)
    print("\nEducation:")
    for edu in db.list_education(conn):
        print(" -", edu)
    print("\nSkills:")
    for skill in db.list_skills(conn):
        print(" -", skill)


def cmd_generate(args):
    conn = db.get_connection()

    if args.jd_file:
        with open(args.jd_file, "r") as f:
            job_description = f.read()
    else:
        job_description = args.jd or ""

    content = generate_tailored_cv(
        conn,
        company=args.company,
        role=args.role,
        job_description=job_description,
        model=args.model,
    )
    output_path = render_cv(content, args.output)
    print(f"Tailored CV written to {output_path}")


def build_parser():
    parser = argparse.ArgumentParser(description="CV builder with Claude-tailored output.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("set-profile", help="Set your contact details and summary.")
    p.add_argument("--name", required=True)
    p.add_argument("--email")
    p.add_argument("--phone")
    p.add_argument("--address")
    p.add_argument("--linkedin")
    p.add_argument("--website")
    p.add_argument("--summary")
    p.set_defaults(func=cmd_set_profile)

    p = sub.add_parser("add-experience", help="Add a work experience entry.")
    p.add_argument("--company", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--location")
    p.add_argument("--start")
    p.add_argument("--end")
    p.add_argument("--bullet", action="append", help="Repeatable: one achievement bullet per flag.")
    p.set_defaults(func=cmd_add_experience)

    p = sub.add_parser("add-education", help="Add an education entry.")
    p.add_argument("--institution", required=True)
    p.add_argument("--degree")
    p.add_argument("--field")
    p.add_argument("--start")
    p.add_argument("--end")
    p.add_argument("--details")
    p.set_defaults(func=cmd_add_education)

    p = sub.add_parser("add-skill", help="Add one or more skills.")
    p.add_argument("--name", required=True, nargs="+")
    p.add_argument("--category")
    p.set_defaults(func=cmd_add_skill)

    p = sub.add_parser("list", help="Show everything currently on file.")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("generate", help="Generate a CV tailored to a specific job.")
    p.add_argument("--company", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--jd", help="Job description text inline.")
    p.add_argument("--jd-file", help="Path to a file containing the job description.")
    p.add_argument("--output", default="cv.pdf")
    p.add_argument("--model", default="claude-sonnet-5")
    p.set_defaults(func=cmd_generate)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
