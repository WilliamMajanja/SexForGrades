"""Self-paced learning framework for students."""
from __future__ import annotations

import json
from pathlib import Path


class LearningPath:
    def __init__(self, root="./learning_paths"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def create_path(self, course, modules, mastery_criteria=None):
        path = {
            "course": course,
            "modules": modules,
            "mastery_criteria": mastery_criteria or {"min_score": 80},
            "progressive": True,
            "self_paced": True,
        }
        out = self.root / f"{course.replace(' ', '_')}.json"
        out.write_text(json.dumps(path, indent=2))
        return path

    def assess_mastery(self, completed_modules, required_modules):
        done = set(completed_modules)
        req = set(required_modules)
        if req.issubset(done):
            return {"mastery": True, "completion": 100.0}
        return {"mastery": False, "completion": len(done & req) / len(req) * 100 if req else 0}
