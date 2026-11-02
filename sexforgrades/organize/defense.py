"""Repression defence - safety, documentation, legal referrals."""
SAFETY_CHECKLIST = [
    "Assess immediate risk of arrest/violence",
    "Have emergency contacts and legal aid numbers ready",
    "Document incidents with time/location/witnesses (facts only)",
    "Use secure devices; consider offline documentation",
    "Know KNCHR, FIDA Kenya, Kituo Cha Sheria contacts",
    "Share location/trusted contact if going to high-risk action",
]
LEGAL_REFERRALS = {
    "fida_kenya": {"name": "FIDA Kenya", "focus": "gender-based violence, sexual harassment"},
    "kituo_cha_sheria": {"name": "Kituo Cha Sheria", "focus": "legal aid, constitutional rights"},
    "knchr": {"name": "Kenya National Commission on Human Rights", "focus": "human rights violations, repression"},
    "icj_kenya": {"name": "ICJ Kenya", "focus": "rule of law, public interest litigation"},
}


def get_safety_checklist():
    return SAFETY_CHECKLIST


def get_legal_referrals():
    return LEGAL_REFERRALS
