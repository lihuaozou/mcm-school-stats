from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "awards.json"
TEAM_PATTERN = r"26[0-3]\d{4}"


def load_payload() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def pdf_team_ids(pdf_name: str) -> set[str]:
    reader = PdfReader(str(ROOT / pdf_name))
    text = "\n".join((page.extract_text() or "") for page in reader.pages[1:])
    return set(re.findall(TEAM_PATTERN, text))


def main() -> None:
    payload = load_payload()
    rows = payload["records"]
    summary = payload["summary"]

    by_pdf: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        by_pdf[row["source_pdf"]].add(row["team"])

    pdf_id_checks = {}
    for pdf_name, parsed_ids in sorted(by_pdf.items()):
        ids = pdf_team_ids(pdf_name)
        pdf_id_checks[pdf_name] = {
            "pdf_team_ids": len(ids),
            "parsed_team_ids": len(parsed_ids),
            "missing_from_json": sorted(ids - parsed_ids),
            "extra_in_json": sorted(parsed_ids - ids),
        }

    official_count_diffs = {}
    for problem in summary["problem_order"]:
        parsed = Counter(row["designation"] for row in rows if row["problem"] == problem)
        expected = summary["expected"][problem]
        official_count_diffs[problem] = {
            designation: parsed.get(designation, 0) - expected.get(designation, 0)
            for designation in sorted(set(parsed) | set(expected))
        }

    duplicate_teams = {team: count for team, count in Counter(row["team"] for row in rows).items() if count > 1}
    blank_institution = [row for row in rows if not row["institution"]]
    raw_institution_suppressed = [
        row
        for row in rows
        if row.get("institution_raw") and row.get("institution_raw") != row.get("institution")
    ]

    report = {
        "record_count": len(rows),
        "unique_team_count": len(set(row["team"] for row in rows)),
        "institution_count": summary["institution_count"],
        "duplicate_team_count": len(duplicate_teams),
        "duplicate_teams": duplicate_teams,
        "invalid_team_id_count": sum(1 for row in rows if not re.fullmatch(TEAM_PATTERN, row["team"])),
        "problem_mismatch_count": sum(1 for row in rows if row["problem"] != row["expected_problem"]),
        "blank_institution_count": len(blank_institution),
        "raw_institution_suppressed_count": len(raw_institution_suppressed),
        "blank_country_count": sum(1 for row in rows if not row["country"]),
        "country_text_in_special_award_count": sum(
            1
            for row in rows
            if re.fullmatch(
                r"(?i)china|usa|australia|canada|malaysia|singapore|bangladesh|south africa|hungary|kazakhstan",
                row.get("special_award", "").strip(),
            )
        ),
        "special_award_count": sum(1 for row in rows if row.get("special_award")),
        "pdf_team_id_checks": pdf_id_checks,
        "official_count_diffs": official_count_diffs,
        "notes": [
            "Problem A has one more Successful Participant in the detailed team list than in the PDF front-page summary.",
            "Blank institution rows are preserved as blank because neither line text nor coordinate text contains an institution for those teams.",
        ],
    }

    out_dir = ROOT / "data"
    (out_dir / "audit_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    with (out_dir / "blank_institution_rows.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "team",
                "contest",
                "problem",
                "designation",
                "country",
                "advisor",
                "institution_raw",
                "special_award",
                "source_pdf",
                "page",
            ],
        )
        writer.writeheader()
        for row in blank_institution:
            writer.writerow({field: row.get(field, "") for field in writer.fieldnames})

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
