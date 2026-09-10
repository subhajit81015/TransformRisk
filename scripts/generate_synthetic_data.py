from pathlib import Path
from datetime import date, timedelta
import numpy as np
import pandas as pd


SEED = 42
rng = np.random.default_rng(SEED)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "synthetic"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Reference dimensions
# ============================================================

BUSINESS_UNITS = [
    "Finance",
    "Operations",
    "Sales",
    "Customer Service",
    "Technology",
    "Supply Chain",
    "Human Resources",
]

TRANSFORMATION_TYPES = [
    "Cloud Migration",
    "ERP Modernization",
    "CRM Transformation",
    "Data Platform Modernization",
    "AI Process Automation",
    "Legacy Application Replacement",
    "Cybersecurity Modernization",
]

TRANSFORMATION_STATUSES = [
    "Planning",
    "Assessment",
    "In Progress",
    "At Risk",
    "On Hold",
    "Completed",
]

CRITICALITIES = [
    "Low",
    "Medium",
    "High",
    "Critical",
]

STRATEGIC_PRIORITIES = [
    "Low",
    "Medium",
    "High",
    "Strategic",
]

RISK_DOMAINS = [
    "Technology",
    "Data",
    "Cybersecurity",
    "Operational",
    "Financial",
    "Compliance",
    "People & Change",
    "Vendor & Dependency",
]

RISK_STATUSES = [
    "Open",
    "Monitoring",
    "Mitigated",
    "Accepted",
]

CONTROL_TYPES = [
    "Preventive",
    "Detective",
    "Corrective",
]

CONTROL_FREQUENCIES = [
    "Per Transaction",
    "Daily",
    "Weekly",
    "Monthly",
    "Quarterly",
]

CONTROL_STATUSES = [
    "Effective",
    "Needs Improvement",
    "Weak",
]

ACTION_PRIORITIES = [
    "Low",
    "Medium",
    "High",
    "Critical",
]

ACTION_STATUSES = [
    "Open",
    "In Progress",
    "Completed",
    "Blocked",
]


# ============================================================
# 1. Transformation initiatives
# ============================================================

def generate_initiatives(n=100):
    rows = []

    start_date = date(2026, 1, 1)

    for i in range(1, n + 1):
        initiative_id = f"TR-{i:04d}"

        transformation_type = rng.choice(TRANSFORMATION_TYPES)
        business_unit = rng.choice(BUSINESS_UNITS)

        criticality = rng.choice(
            CRITICALITIES,
            p=[0.10, 0.35, 0.40, 0.15],
        )

        strategic_priority = rng.choice(
            STRATEGIC_PRIORITIES,
            p=[0.10, 0.30, 0.40, 0.20],
        )

        status = rng.choice(
            TRANSFORMATION_STATUSES,
            p=[0.15, 0.20, 0.30, 0.15, 0.05, 0.15],
        )

        budget = round(
            rng.uniform(250_000, 15_000_000),
            2,
        )

        target_date = start_date + timedelta(
            days=int(rng.integers(90, 720))
        )

        rows.append(
            {
                "initiative_id": initiative_id,
                "initiative_name": (
                    f"{transformation_type} Program "
                    f"{i:03d}"
                ),
                "transformation_type": transformation_type,
                "business_unit": business_unit,
                "owner": f"Transformation Lead {rng.integers(1, 21):02d}",
                "current_state": (
                    f"Legacy {rng.choice(['platform', 'process', 'application'])}"
                ),
                "target_state": (
                    f"Modern {rng.choice(['cloud platform', 'digital process', 'technology stack'])}"
                ),
                "strategic_priority": strategic_priority,
                "criticality": criticality,
                "budget": budget,
                "target_completion_date": target_date,
                "status": status,
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# 2. Transformation risks
# ============================================================

def generate_risks(initiatives):
    rows = []
    risk_counter = 1

    for _, initiative in initiatives.iterrows():

        # Every initiative gets 5-8 risks.
        # There are exactly 8 unique risk domains.
        risk_count = int(
            rng.integers(
                5,
                len(RISK_DOMAINS) + 1,
            )
        )

        selected_domains = rng.choice(
            RISK_DOMAINS,
            size=risk_count,
            replace=False,
        )

        for domain in selected_domains:

            likelihood = int(
                rng.choice(
                    [1, 2, 3, 4, 5],
                    p=[0.05, 0.15, 0.35, 0.30, 0.15],
                )
            )

            impact = int(
                rng.choice(
                    [1, 2, 3, 4, 5],
                    p=[0.05, 0.15, 0.30, 0.30, 0.20],
                )
            )

            control_effectiveness = round(
                rng.uniform(25, 90),
                2,
            )

            status = rng.choice(
                RISK_STATUSES,
                p=[0.55, 0.25, 0.15, 0.05],
            )

            rows.append(
                {
                    "risk_id": f"RSK-{risk_counter:05d}",

                    "initiative_id": initiative[
                        "initiative_id"
                    ],

                    "risk_name": (
                        f"{domain} risk for "
                        f"{initiative['initiative_name']}"
                    ),

                    "risk_domain": domain,

                    "description": (
                        f"Potential {domain.lower()} risk "
                        f"associated with the transformation."
                    ),

                    "likelihood": likelihood,

                    "impact": impact,

                    "control_effectiveness":
                        control_effectiveness,

                    "status": status,
                }
            )

            risk_counter += 1

    return pd.DataFrame(rows)

# ============================================================
# 3. Risk controls
# ============================================================

def generate_controls(risks):
    rows = []
    counter = 1

    for _, risk in risks.iterrows():

        control_count = int(rng.integers(0, 3))

        for _ in range(control_count):

            effectiveness = round(
                rng.uniform(30, 95),
                2,
            )

            rows.append(
                {
                    "control_id": f"CTRL-{counter:05d}",
                    "risk_id": risk["risk_id"],
                    "control_name": (
                        f"{risk['risk_domain']} "
                        f"Control {counter:03d}"
                    ),
                    "control_type": rng.choice(CONTROL_TYPES),
                    "control_owner": (
                        f"Control Owner {rng.integers(1, 31):02d}"
                    ),
                    "control_frequency": rng.choice(
                        CONTROL_FREQUENCIES
                    ),
                    "effectiveness_score": effectiveness,
                    "control_status": rng.choice(
                        CONTROL_STATUSES,
                        p=[0.45, 0.40, 0.15],
                    ),
                    "description": (
                        "Management control designed to reduce "
                        "transformation risk."
                    ),
                }
            )

            counter += 1

    return pd.DataFrame(rows)


# ============================================================
# 4. Mitigation actions
# ============================================================

def generate_actions(risks):
    rows = []
    counter = 1

    for _, risk in risks.iterrows():

        # Higher-risk records receive more actions
        inherent_score = (
            risk["likelihood"] * risk["impact"]
        )

        action_probability = (
            0.80 if inherent_score >= 15
            else 0.50 if inherent_score >= 9
            else 0.25
        )

        if rng.random() > action_probability:
            continue

        action_names = {
            "Technology": "Perform architecture review",
            "Data": "Complete migration reconciliation",
            "Cybersecurity": "Perform security assessment",
            "Operational": "Complete business continuity test",
            "Financial": "Validate transformation cost controls",
            "Compliance": "Complete regulatory control review",
            "People & Change": "Execute user adoption program",
            "Vendor & Dependency": "Review vendor SLA and dependency risk",
        }

        rows.append(
            {
                "action_id": f"ACT-{counter:05d}",
                "risk_id": risk["risk_id"],
                "action_name": action_names[
                    risk["risk_domain"]
                ],
                "action_owner": (
                    f"Action Owner {rng.integers(1, 31):02d}"
                ),
                "priority": (
                    "Critical"
                    if inherent_score >= 20
                    else "High"
                    if inherent_score >= 15
                    else "Medium"
                ),
                "status": rng.choice(
                    ACTION_STATUSES,
                    p=[0.35, 0.35, 0.20, 0.10],
                ),
                "due_date": (
                    date(2026, 9, 1)
                    + timedelta(
                        days=int(rng.integers(5, 120))
                    )
                ),
                "completion_percentage": int(
                    rng.integers(0, 101)
                ),
                "expected_risk_reduction": round(
                    rng.uniform(5, 45),
                    2,
                ),
            }
        )

        counter += 1

    return pd.DataFrame(rows)


# ============================================================
# 5. Readiness assessments
# ============================================================

def generate_readiness(initiatives):
    rows = []

    dimensions = [
        "Technology",
        "Data",
        "Process",
        "People",
        "Governance",
    ]

    counter = 1

    for _, initiative in initiatives.iterrows():

        for dimension in dimensions:

            score = int(
                rng.integers(35, 96)
            )

            rows.append(
                {
                    "readiness_id": f"RDY-{counter:05d}",
                    "initiative_id": initiative["initiative_id"],
                    "readiness_dimension": dimension,
                    "readiness_score": score,
                    "assessment_status": (
                        "Ready"
                        if score >= 80
                        else "Ready with Conditions"
                        if score >= 65
                        else "Remediation Required"
                        if score >= 50
                        else "Not Ready"
                    ),
                    "assessment_note": (
                        f"{dimension} readiness assessment "
                        f"for transformation initiative."
                    ),
                }
            )

            counter += 1

    return pd.DataFrame(rows)


# ============================================================
# Save datasets
# ============================================================

def main():
    print("Generating TransformRisk synthetic dataset...")

    initiatives = generate_initiatives()
    risks = generate_risks(initiatives)
    controls = generate_controls(risks)
    actions = generate_actions(risks)
    readiness = generate_readiness(initiatives)

    datasets = {
        "transformation_initiatives.csv": initiatives,
        "transformation_risks.csv": risks,
        "risk_controls.csv": controls,
        "mitigation_actions.csv": actions,
        "readiness_assessments.csv": readiness,
    }

    for filename, dataframe in datasets.items():
        path = OUTPUT_DIR / filename
        dataframe.to_csv(path, index=False)

        print(
            f"{filename}: "
            f"{len(dataframe):,} rows"
        )

    print("\nGeneration complete.")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
