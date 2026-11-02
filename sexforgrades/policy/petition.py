"""Policy-based petition templates."""
from __future__ import annotations


class PetitionGenerator:
    @staticmethod
    def generate_education_funding_petition(recipient="National Assembly of Kenya", target_min_increase_percent=15):
        return f"""PETITION TO {recipient}

Subject: Prioritize Funding for Public Universities, Polytechnics and the Sciences

We, the undersigned students of Kenyan institutions of higher learning, petition that:

1. Budgetary allocations to public universities and national polytechnics be increased by at least {target_min_increase_percent}% to address lecturer shortages, missing marks crises, and deteriorating infrastructure.
2. Funding for pure sciences (Mathematics, Physics, Chemistry, Biology, Computer Science) be ring-fenced and increased, reversing decades of science suppression.
3. The Ministry of Education and universities implement transparent, time-bound mechanisms to clear all missing marks with penalties for unjustified delays.
4. All appointments to tenured professorships be made based on verifiable merit, peer-reviewed publications, and transparent CUE-compliant processes.
5. Strengthen student complaint mechanisms with independent oversight and protection from victimization.

Sincerely,
[Student Union Name]
[Date]
[Signatures/Support List]
"""

    @staticmethod
    def generate_missing_marks_petition(institution):
        return f"""PETITION REGARDING MISSING MARKS AT {institution}

We demand:
1. Immediate publication of a consolidated missing marks register with unit codes, lecturers, and resolution timelines.
2. Independent audit of results processing for the last 5 academic years.
3. Protection for students who report missing marks from victimization or retaliation.
4. Sanctions for officers who deliberately withhold or lose marks.
5. Quarterly public progress reports to the student body.

Date: [YYYY-MM-DD]
Signed: [Student Representatives]
"""
