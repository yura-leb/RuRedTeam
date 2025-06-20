"""
Dataset creation module that generates attack prompts by applying attacks to base prompts.
Supports regular and model-based attacks with efficient batch processing.
"""

import os
import asyncio
from typing import Dict, List, Any, Optional, Tuple, AsyncGenerator
from tqdm import tqdm

from attacks.base_attack import BaseAttack
from models.base_model import Model
from attacks import ModelAttack

from pipeline.constants import ATTACK_CLASSES

def build_attack_from_config(attack_config, attacker_model=None):
    """
    Construct an attack instance from configuration.
    
    Args:
        attack_config: String attack name or dict with attack configuration
        attacker_model: Model instance for model-based attacks
        
    Returns:
        Configured attack instance
        
    Raises:
        ValueError: If attack name is unknown or model is missing
    """
    if isinstance(attack_config, str):
        attack_name, params = attack_config, {}
        inner_attack_cfg = None
    else:
        attack_name = attack_config.get("name", "")
        params = attack_config.get("params", {})
        inner_attack_cfg = attack_config.get("inner_attack", None)

    if attack_name not in ATTACK_CLASSES:
        raise ValueError(f"Unknown attack '{attack_name}'")
    attack_class = ATTACK_CLASSES[attack_name]["attack_class"]
    if issubclass(attack_class, ModelAttack):
        if not attacker_model:
            raise ValueError(f"Attacker model is required for '{attack_name}'")
        attack = attack_class(model=attacker_model, **params)
    else:
        attack = attack_class(**params)
    if inner_attack_cfg:
        inner_attack = build_attack_from_config(inner_attack_cfg, attacker_model)
        attack = inner_attack | attack
    return attack

def setup_attacks(attack_configs: List[dict], attacker_model: Optional[Model] = None) -> Dict[str, BaseAttack]:
    """
    Initialize attack instances from configuration list.
    
    Args:
        attack_configs: List of attack configurations
        attacker_model: Optional model for model-based attacks
        
    Returns:
        Dictionary of attack name to attack instance mappings
    """
    attacks = {}
    for attack_config in attack_configs:        
        try:
            attack = build_attack_from_config(attack_config, attacker_model)
            attacks[attack.__class__.__name__] = attack
        except Exception as e:
            print(f"Warning: Failed to initialize attack from config {attack_config}: {str(e)}")
    return attacks

def create_prompt(base_prompt: str, system_prompt: Optional[str] = None) -> Any:
    """
    Format a prompt with optional system instructions.
    
    Args:
        base_prompt: The user prompt content
        system_prompt: Optional system instructions
        
    Returns:
        String prompt or list of message dictionaries
    """
    if system_prompt:
        return [
            {"type": "system", "content": system_prompt},
            {"type": "human", "content": base_prompt}
        ]
    return base_prompt

async def generate_attack_prompt(attack: BaseAttack, base_prompt: str, 
                                system_prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Apply an attack to a single prompt.
    
    Args:
        attack: Attack instance to apply
        base_prompt: Original prompt content
        system_prompt: Optional system instructions
        
    Returns:
        Dictionary with attack result and metadata
    """
    prompt = create_prompt(base_prompt, system_prompt)
    attack_name = attack.__class__.__name__
    try:
        attack_prompt = attack.apply(prompt)
        return {
            "base_prompt": base_prompt,
            "prompt": attack_prompt,
            "attack_name": attack_name,
            "attack_type": ATTACK_CLASSES[attack_name]["attack_type"],
            "attack_params": attack.get_params(),
            # "attack_timestamp": get_timestamp(),
            "error": ""
        }
    except Exception as e:
        print(f"Error generating prompt for attack {attack_name}: {str(e)}")
        return {
            "base_prompt": base_prompt,
            "prompt": "",
            "attack_name": attack_name,
            "attack_type": ATTACK_CLASSES[attack_name]["attack_type"],
            "attack_params": attack.get_params(),
            # "attack_timestamp": get_timestamp(),
            "error": str(e)
        }

async def stream_attack(attack: BaseAttack, 
                        base_prompts: List[str], system_prompt: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Apply an attack to multiple prompts in streaming mode.
    
    Args:
        attack: Attack instance to apply
        base_prompts: List of original prompts
        system_prompt: Optional system instructions
        
    Yields:
        Attack result dictionaries with metadata
    """
    # Format all prompts
    formatted_prompts = [create_prompt(prompt, system_prompt) for prompt in base_prompts]
    attack_name = attack.__class__.__name__
    try:
        # Apply the attack to all prompts at once
        i = 0
        async for attack_prompt in attack.stream_abatch(formatted_prompts):
            yield {
                    "base_prompt": base_prompts[i],
                    "prompt": attack_prompt,
                    "attack_name": attack_name,
                    "attack_type": ATTACK_CLASSES[attack_name]["attack_type"],
                    "attack_params": attack.get_params(),
                    # "attack_timestamp": get_timestamp(),
                    "error": ""
                }
            i += 1
    except Exception as e:
        print(f"Error generating prompts for model attack {attack_name}: {str(e)}")
        for base_prompt in base_prompts:
            yield {
                "base_prompt": base_prompt,
                "prompt": "",
                "attack_name": attack_name,
                "attack_type": ATTACK_CLASSES[attack_name]["attack_type"],
                "attack_params": attack.get_params(),
                # "attack_timestamp": get_timestamp(),
                "error": str(e)
            }


async def stream_attack_prompts(attacks: Dict[str, BaseAttack],
                                base_prompts: List[str], system_prompt: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Process all attacks on all base prompts and stream results.
    
    Args:
        attacks: Dictionary of attack instances
        base_prompts: List of original prompts
        system_prompt: Optional system instructions
        
    Yields:
        Attack result dictionaries with metadata
    """
    
    # Initialize result list
    attack_prompts = []
    
    if attacks:
        # Process regular attacks with tqdm for progress tracking
        for i, (name, attack) in tqdm(enumerate(attacks.items()), total=len(attacks), desc="Processing Attacks"):
            async for attack_prompt_data in stream_attack(attack, base_prompts, system_prompt):
                attack_prompts.append(attack_prompt_data)
                yield attack_prompt_data
    