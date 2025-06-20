"""
Irrelevant information attacks that add noise, distractions, and unrelated content.
"""

from attacks.types.irrelevant_information.distractors_attack import DistractorsAttack
from attacks.types.irrelevant_information.distractors_negated_attack import DistractorsNegatedAttack
from attacks.types.irrelevant_information.irrelevant_information_attack import IrrelevantInformationAttack

# For now, the Combination attacks are missing, but we are importing DistractorsAttack from task_deflection
__all__ = [
    "DistractorsAttack",
    "DistractorsNegatedAttack",
    "IrrelevantInformationAttack"
] 