#!/usr/bin/env python3
"""
Synthetic legal document generator for local testing.

Creates a configurable number of varied contract- and policy-style
documents so the indexing pipeline has richer content to ingest.
"""
import argparse
import random
import textwrap
from datetime import date, timedelta
from pathlib import Path


def _random_date(start_year: int = 2015, end_year: int = 2026) -> str:
    """Return a random date string between the supplied years."""
    start = date(start_year, 1, 1).toordinal()
    end = date(end_year, 12, 31).toordinal()
    chosen = date.fromordinal(random.randint(start, end))
    return chosen.strftime("%B %d, %Y")


def _random_state() -> str:
    """Select a random US state for jurisdiction examples."""
    states = [
        "California",
        "New York",
        "Delaware",
        "Texas",
        "Illinois",
        "Washington",
        "Florida",
        "Massachusetts",
        "Colorado",
        "Georgia",
    ]
    return random.choice(states)


def _random_city() -> str:
    cities = [
        "San Francisco",
        "New York City",
        "Austin",
        "Chicago",
        "Seattle",
        "Miami",
        "Boston",
        "Denver",
        "Atlanta",
        "Los Angeles",
    ]
    return random.choice(cities)


def _random_company(suffix: str = "LLC") -> str:
    adjectives = [
        "Aurora",
        "Summit",
        "Pioneer",
        "Sterling",
        "Evergreen",
        "Harbor",
        "Mosaic",
        "Blue Ridge",
        "Catalyst",
        "Atlas",
    ]
    nouns = [
        "Consulting",
        "Ventures",
        "Industries",
        "Holdings",
        "Solutions",
        "Enterprises",
        "Capital",
        "Systems",
        "Partners",
        "Laboratories",
    ]
    return f"{random.choice(adjectives)} {random.choice(nouns)} {suffix}"


def _random_currency(amount_min: int = 50_000, amount_max: int = 2_500_000) -> str:
    amount = random.randrange(amount_min, amount_max, 5_000)
    return f"${amount:,}"


def _random_terms(count: int = 6) -> list[str]:
    clauses = [
        "Liability Limitation",
        "Confidentiality",
        "Data Protection",
        "Service Levels",
        "Indemnification",
        "Force Majeure",
        "Termination",
        "Assignment",
        "Governing Law",
        "Dispute Resolution",
        "Audit Rights",
        "Insurance Requirements",
        "Non-Solicitation",
        "Intellectual Property",
        "Change Management",
    ]
    random.shuffle(clauses)
    return clauses[:count]


def _document_templates() -> dict[str, str]:
    """Return mapping of template names to format strings."""
    return {
        "commercial_lease": textwrap.dedent(
            """
            COMMERCIAL LEASE AGREEMENT
            Effective Date: {effective_date}

            This Commercial Lease Agreement ("Agreement") is entered into between
            Landlord: {landlord}
            Tenant: {tenant}

            Premises:
              Address: {city}, {_state}
              Suite: {suite}
              Square Footage: {square_feet} rentable square feet

            1. TERM
               The initial term commences on {term_start} and continues for {term_months} months.
               Tenant holds two renewal options of {renewal_months} months each with written notice.

            2. BASE RENT
               Monthly base rent is {base_rent}, escalating {rent_escalation}% annually.
               Additional rent includes operating expenses, property taxes, and insurance.

            3. PERMITTED USE
               Tenant shall operate a {permitted_use} and comply with all applicable regulations.

            4. MAINTENANCE AND REPAIRS
               Landlord maintains structural components; Tenant handles interior maintenance.

            5. INSURANCE
               Tenant maintains commercial general liability insurance with limits of {insurance_limit}.

            6. DEFAULT AND REMEDIES
               Failure to pay rent within {grace_period} days constitutes default subject to legal remedies.

            7. GOVERNING LAW
               This Agreement is governed by the laws of the State of {_state}.

            EXHIBIT A - OPERATING EXPENSES
               {expense_breakdown}
            """
        ),
        "employment_agreement": textwrap.dedent(
            """
            EXECUTIVE EMPLOYMENT AGREEMENT
            Effective Date: {effective_date}

            Employer: {employer}
            Executive: {executive}

            POSITION:
              Title: {title}
              Location: {city}, {_state}

            COMPENSATION:
              Base Salary: {base_salary} payable in accordance with Employer payroll practices.
              Annual Bonus: Target {bonus_target}% of base salary subject to performance metrics.
              Equity: {equity_grant} incentive units vesting over four years.

            DUTIES:
              Executive agrees to devote full working time to Employer and comply with policies.

            CONFIDENTIALITY AND IP:
              Executive acknowledges proprietary rights over inventions created during employment.

            RESTRICTIVE COVENANTS:
              Non-competition period of {noncompete_months} months within {_state}.
              Non-solicitation of employees and customers for {nonsolicit_months} months.

            TERMINATION:
              Cause definition includes material breach or gross misconduct.
              Upon termination without cause, Executive receives {severance} severance and COBRA coverage.

            GOVERNING LAW:
              This Agreement shall be construed under the laws of {_state}.
            """
        ),
        "mutual_nda": textwrap.dedent(
            """
            MUTUAL NON-DISCLOSURE AGREEMENT
            Effective Date: {effective_date}

            Parties:
              Disclosing Party: {party_a}
              Receiving Party: {party_b}

            PURPOSE:
              Exploratory discussions regarding {evaluation_focus}.

            DEFINITION OF CONFIDENTIAL INFORMATION:
              Includes all technical, business, financial, product roadmaps, pricing, and customer data.

            OBLIGATIONS:
              The Receiving Party shall:
                - Maintain confidentiality with a standard of care no less than reasonable industry practice.
                - Use information solely for the Purpose.
                - Restrict disclosure to employees with a need to know bound by similar obligations.

            EXCLUSIONS:
              Information already public, independently developed, or rightfully received remains outside scope.

            TERM:
              Confidentiality obligations survive for {survival_years} years after termination.

            GOVERNING LAW:
              This Agreement is governed by the laws of the State of {_state}.
            """
        ),
        "msa": textwrap.dedent(
            """
            MASTER SERVICES AGREEMENT
            Effective Date: {effective_date}

            Provider: {provider}
            Client: {client}

            SERVICES:
              Provider delivers {service_description} in accordance with attached Statements of Work.

            SERVICE LEVELS:
              Uptime commitment of {uptime}% measured monthly with service credits for breaches.

            FEES:
              Fixed monthly fee of {monthly_fee} plus pass-through expenses approved by Client.

            CHANGE MANAGEMENT:
              Parties follow a documented change order process with mutual approvals.

            DATA SECURITY:
              Provider maintains SOC 2 controls, conducts annual penetration tests, and encrypts data in transit.

            TERM AND TERMINATION:
              Initial term of {term_years} years, renewing annually unless notice provided {notice_days} days prior.
              Either party may terminate for cause with {cure_period}-day cure period.

            LIABILITY:
              Aggregate liability caps at {liability_cap} excluding indemnification for third-party claims.

            GOVERNING LAW:
              This Agreement shall be governed by the laws of {_state}.
            """
        ),
        "privacy_policy": textwrap.dedent(
            """
            GLOBAL PRIVACY NOTICE
            Version Date: {effective_date}

            INTRODUCTION
            {company} ("Company") describes practices for processing personal data of customers and partners.

            DATA COLLECTION
              Categories include identification data, contact details, usage analytics, and payment information.
              Sources include direct submissions, automated collection, and third-party integrations.

            LEGAL BASIS
              Processing relies on legitimate interests, contract performance, consent, and compliance obligations.

            DATA SUBJECT RIGHTS
              Individuals may access, rectify, delete, or port data by contacting {privacy_contact}.

            SECURITY
              Company implements layered controls, encryption, access reviews, and incident response plans.

            INTERNATIONAL TRANSFERS
              Cross-border transfers rely on SCCs and undergo transfer impact assessments.

            RETENTION
              Data retained for {retention_years} years unless longer retention required by law.

            CONTACT
              Questions may be directed to {privacy_contact}.
            """
        ),
        "loan_agreement": textwrap.dedent(
            """
            TERM LOAN AGREEMENT
            Date: {effective_date}

            Lender: {lender}
            Borrower: {borrower}

            PRINCIPAL AMOUNT: {principal}
            INTEREST RATE: {interest_rate}% per annum, adjusted quarterly.

            USE OF PROCEEDS:
              Borrower shall apply proceeds toward {use_of_proceeds}.

            REPAYMENT:
              Amortized over {amortization_years} years with payments due on the first business day monthly.
              Optional prepayment permitted without penalty upon ten days written notice.

            COVENANTS:
              Borrower maintains minimum EBITDA of {ebitda} and debt-service coverage ratio of {dscr}:1.
              Restrictions on additional indebtedness and asset dispositions apply.

            EVENTS OF DEFAULT:
              Include failure to pay, insolvency events, or breach of covenants with {cure_period}-day cure period.

            GOVERNING LAW:
              This Agreement governed by the laws of the State of {_state}.
            """
        ),
        "policy_manual": textwrap.dedent(
            """
            CORPORATE COMPLIANCE MANUAL
            Effective {effective_date}

            SCOPE
              Applies to all directors, officers, employees, contractors, and temporary workers.

            CODE OF CONDUCT
              Employees uphold integrity, avoid conflicts of interest, and report suspected violations.

            ANTI-CORRUPTION
              Adheres to FCPA and UK Bribery Act with mandatory training every {training_cycle} months.

            DATA GOVERNANCE
              Implements records classification, retention schedules, and breach notification procedures.

            INVESTIGATIONS
              Compliance office initiates investigations within {investigation_timeline} days of a report.

            DISCIPLINARY ACTION
              Violations may result in counseling, suspension, or termination subject to local law.

            WHISTLEBLOWER PROTECTIONS
              Anonymous hotline provided; retaliation strictly prohibited.
            """
        ),
        "software_license": textwrap.dedent(
            """
            SOFTWARE LICENSE AGREEMENT
            Effective Date: {effective_date}

            Licensor: {Licensor}
            Licensee: {Licensee}

            LICENSE GRANT:
              Non-exclusive, non-transferable right to use {product_name} for internal business purposes.

            RESTRICTIONS:
              No reverse engineering, sublicensing, or competitive analysis without consent.

            SUPPORT SERVICES:
              Includes updates, patches, and support response within {support_sla} hours.

            FEES:
              Annual subscription fee of {subscription_fee} with auto-renewal unless cancelled {notice_days} days prior.

            CONFIDENTIALITY:
              Both parties protect trade secrets and proprietary information.

            WARRANTY:
              Software performs materially per documentation; remedies limited to re-performance.

            GOVERNING LAW:
              This Agreement governed by the laws of {_state}.
            """
        ),
    }


def build_document(doc_type: str) -> str:
    """Fill the template identified by doc_type with randomized values."""
    templates = _document_templates()
    if doc_type not in templates:
        raise ValueError(f"Unknown document type: {doc_type}")

    # Shared random values
    landlord = _random_company("Properties LLC")
    tenant = _random_company("Cafe Inc.")

    populated = templates[doc_type].format(
        effective_date=_random_date(),
        landlord=landlord,
        tenant=tenant,
        suite=f"Suite {random.randint(100, 999)}",
        square_feet=random.randint(1800, 12000),
        term_start=_random_date(),
        term_months=random.choice([36, 48, 60, 84]),
        renewal_months=random.choice([12, 24, 36]),
        base_rent=_random_currency(45_000, 180_000),
        rent_escalation=random.choice([2, 3, 4, 5]),
        permitted_use=random.choice(
            [
                "specialty retail operation",
                "professional services office",
                "culinary training facility",
                "coworking lounge",
            ]
        ),
        insurance_limit=f"${random.randint(1, 5)},000,000 per occurrence",
        grace_period=random.choice([5, 7, 10]),
        expense_breakdown="\n               ".join(
            f"- {item}: {value}"
            for item, value in [
                ("Common Area Maintenance", _random_currency(12_000, 60_000)),
                ("Utilities", _random_currency(15_000, 45_000)),
                ("Property Tax Allocation", _random_currency(20_000, 80_000)),
            ]
        ),
        employer=_random_company("Holdings Inc."),
        executive=random.choice(
            ["Jordan Lee", "Avery Morgan", "Dakota Quinn", "Reese Parker", "Taylor Rivers"]
        ),
        title=random.choice(
            ["Chief Operating Officer", "General Counsel", "Chief Product Officer", "Head of Compliance"]
        ),
        base_salary=_random_currency(180_000, 420_000),
        bonus_target=random.choice([25, 35, 40]),
        equity_grant=random.choice(["25,000 RSUs", "1.5% profit interest", "35,000 stock options"]),
        noncompete_months=random.choice([6, 9, 12]),
        nonsolicit_months=random.choice([12, 18, 24]),
        severance=_random_currency(150_000, 350_000),
        party_a=_random_company("Innovations LLC"),
        party_b=_random_company("Technologies Inc."),
        evaluation_focus=random.choice(
            [
                "joint product development opportunities",
                "strategic financing transactions",
                "cloud infrastructure migration services",
                "enterprise software distribution",
            ]
        ),
        survival_years=random.choice([3, 4, 5]),
        provider=_random_company("Services LLC"),
        client=_random_company("Global Corp."),
        service_description=random.choice(
            [
                "managed security operations",
                "regulatory compliance assessments",
                "contract lifecycle management",
                "cloud infrastructure optimization",
            ]
        ),
        uptime=random.choice([99.5, 99.7, 99.9]),
        monthly_fee=_random_currency(35_000, 120_000),
        term_years=random.choice([2, 3, 5]),
        notice_days=random.choice([30, 45, 60]),
        cure_period=random.choice([15, 30]),
        liability_cap=_random_currency(500_000, 2_000_000),
        company=_random_company("Group Ltd."),
        privacy_contact=f"privacy@{_random_company('').replace(' ', '').lower()}.com",
        retention_years=random.choice([3, 5, 7]),
        lender=_random_company("Capital Partners"),
        borrower=_random_company("Manufacturing Co."),
        principal=_random_currency(250_000, 5_000_000),
        interest_rate=random.choice([4.5, 5.25, 6.0, 6.5]),
        use_of_proceeds=random.choice(
            [
                "facility expansion and equipment purchases",
                "working capital and research initiatives",
                "acquisition integration costs",
                "debt refinancing and capital improvements",
            ]
        ),
        amortization_years=random.choice([3, 5, 7]),
        ebitda=_random_currency(2_000_000, 6_000_000),
        dscr=random.choice([1.2, 1.35, 1.5]),
        training_cycle=random.choice([12, 18, 24]),
        investigation_timeline=random.choice([5, 10, 15]),
        Licensor=_random_company("Software Ltd."),
        Licensee=_random_company("Analytics Corp."),
        product_name=random.choice(
            ["LexisIQ Platform", "Compliance Navigator", "CaseInsight Suite", "ContractSphere Cloud"]
        ),
        support_sla=random.choice([4, 8, 12]),
        subscription_fee=_random_currency(80_000, 220_000),
        _state=_random_state(),
        city=_random_city(),
        clauses="\n".join(f"{i+1}. {clause}" for i, clause in enumerate(_random_terms())),
    )

    return textwrap.dedent(populated).strip() + "\n"


def generate_documents(output_dir: Path, count: int) -> list[Path]:
    """Generate synthetic legal documents in the output directory."""
    random.seed(2024)
    output_dir.mkdir(parents=True, exist_ok=True)

    doc_types = list(_document_templates().keys())
    created_files: list[Path] = []

    for index in range(count):
        doc_type = doc_types[index % len(doc_types)]
        content = build_document(doc_type)
        filename = f"{index + 1:02d}_{doc_type.replace('_', '-')}.txt"
        file_path = output_dir / filename
        file_path.write_text(content, encoding="utf-8")
        created_files.append(file_path)

    return created_files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic legal documents for testing the knowledge indexer."
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data") / "sample_docs",
        help="Directory where documents will be written (default: data/sample_docs)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="Number of documents to generate (default: 20)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    created = generate_documents(args.out_dir, args.count)
    print(f"✓ Generated {len(created)} synthetic documents in {args.out_dir.resolve()}")
    for path in created[:5]:
        print(f"  - {path.name}")
    if len(created) > 5:
        print("  ...")


if __name__ == "__main__":
    main()
