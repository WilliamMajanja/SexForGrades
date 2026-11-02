"""Curate public domain CS textbooks."""
PUBLIC_DOMAIN_CS = [
    {"title": "Structure and Interpretation of Computer Programs", "author": "Abelson & Sussman", "note": "MIT OpenCourseWare/public domain context varies - prefer verified PD sources"},
    {"title": "The Art of Computer Programming (volumes)", "author": "Knuth", "note": "Check license per edition"},
    {"title": "Computer Networks", "author": "Tanenbaum (older editions may vary)", "note": "Verify PD status"},
    {"title": "Introduction to Algorithms", "author": "CLRS", "note": "Usually copyrighted - prefer PD alternatives"},
    {"title": "Operating Systems: Three Easy Pieces", "author": "Arpaci-Dusseau", "note": "Free online, check license"},
    {"title": "Dive into Systems", "author": "Various", "note": "Open educational resources"},
]


def get_recommended_pd():
    return PUBLIC_DOMAIN_CS
