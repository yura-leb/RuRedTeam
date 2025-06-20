"""
Attack types module that organizes various attack implementations by category.
Each submodule contains specific attack types that use different strategies to generate adversarial prompts.
"""

# Import all attack types for easy access
from attacks.types.simple_instructions import *
from attacks.types.roleplay import *
from attacks.types.persuasion import *
from attacks.types.output_formatting import *
from attacks.types.context_switching import *
from attacks.types.token_smuggling import *
from attacks.types.text_structure_modification import *
from attacks.types.task_deflection import *
from attacks.types.irrelevant_information import *
from attacks.types.in_context_learning import *

# Import __all__ from each module
from attacks.types.simple_instructions import __all__ as simple_instructions_all
from attacks.types.roleplay import __all__ as roleplay_all
from attacks.types.persuasion import __all__ as persuasion_all
from attacks.types.output_formatting import __all__ as output_formatting_all
from attacks.types.context_switching import __all__ as context_switching_all
from attacks.types.token_smuggling import __all__ as token_smuggling_all
from attacks.types.text_structure_modification import __all__ as text_structure_modification_all
from attacks.types.task_deflection import __all__ as task_deflection_all
from attacks.types.irrelevant_information import __all__ as irrelevant_information_all
from attacks.types.in_context_learning import __all__ as in_context_learning_all

# Extend __all__ with all attack types
__all__ = []
__all__.extend(simple_instructions_all)
__all__.extend(roleplay_all)
__all__.extend(persuasion_all)
__all__.extend(output_formatting_all)
__all__.extend(context_switching_all)
__all__.extend(token_smuggling_all)
__all__.extend(text_structure_modification_all)
__all__.extend(task_deflection_all)
__all__.extend(irrelevant_information_all)
__all__.extend(in_context_learning_all) 