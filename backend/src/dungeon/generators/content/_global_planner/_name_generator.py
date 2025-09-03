"""
Dungeon name generation for global planning.
"""

import random

from opentelemetry import trace

from models.dungeon import DungeonGuidelines
from utils import simple_trace


class DungeonNameGenerator:
    """Generates thematic dungeon names based on guidelines."""

    def __init__(self):
        """Initialize the name generator."""
        # Theme-specific name components
        self.theme_prefixes = {
            "temple": [
                "Sacred",
                "Holy",
                "Consecrated",
                "Divine",
                "Blessed",
                "Ancient",
                "Forgotten",
            ],
            "tomb": [
                "Burial",
                "Funerary",
                "Cryptic",
                "Necrotic",
                "Shadowed",
                "Eternal",
                "Silent",
            ],
            "mine": [
                "Abandoned",
                "Forgotten",
                "Deep",
                "Crystal",
                "Mineral",
                "Cavernous",
                "Underground",
            ],
            "fortress": [
                "Military",
                "Defensive",
                "Strategic",
                "Bastion",
                "Citadel",
                "Stronghold",
                "Fortified",
            ],
            "lair": [
                "Beast",
                "Monster",
                "Creature",
                "Predator",
                "Hunting",
                "Territorial",
                "Wild",
            ],
            "abandoned": [
                "Deserted",
                "Forsaken",
                "Decaying",
                "Crumbling",
                "Lost",
                "Forgotten",
                "Silent",
            ],
        }

        self.theme_suffixes = {
            "temple": [
                "Sanctuary",
                "Shrine",
                "Chapel",
                "Cathedral",
                "Monastery",
                "Temple",
                "Altar",
            ],
            "tomb": [
                "Crypt",
                "Mausoleum",
                "Sepulcher",
                "Tomb",
                "Burial Chamber",
                "Necropolis",
                "Catacomb",
            ],
            "mine": ["Mine", "Cavern", "Tunnel", "Shaft", "Excavation", "Dig", "Pit"],
            "fortress": [
                "Fortress",
                "Castle",
                "Keep",
                "Tower",
                "Bastion",
                "Citadel",
                "Stronghold",
            ],
            "lair": ["Den", "Lair", "Cave", "Hollow", "Nest", "Burrow", "Hideout"],
            "abandoned": [
                "Ruins",
                "Remains",
                "Wreckage",
                "Debris",
                "Shell",
                "Husk",
                "Shadow",
            ],
        }

        self.atmosphere_modifiers = {
            "mystical": [
                "Mystical",
                "Enchanted",
                "Magical",
                "Arcane",
                "Ethereal",
                "Otherworldly",
            ],
            "dark": ["Dark", "Shadowed", "Gloomy", "Dreary", "Bleak", "Somber"],
            "dangerous": [
                "Dangerous",
                "Perilous",
                "Hazardous",
                "Treacherous",
                "Deadly",
                "Lethal",
            ],
            "ancient": [
                "Ancient",
                "Antique",
                "Vintage",
                "Historic",
                "Timeworn",
                "Aged",
            ],
            "corrupted": [
                "Corrupted",
                "Tainted",
                "Defiled",
                "Profaned",
                "Desecrated",
                "Polluted",
            ],
        }

        self.difficulty_modifiers = {
            "easy": ["Simple", "Basic", "Minor", "Small", "Humble"],
            "medium": ["Standard", "Common", "Regular", "Typical", "Ordinary"],
            "hard": ["Challenging", "Difficult", "Complex", "Advanced", "Formidable"],
            "deadly": ["Deadly", "Lethal", "Fatal", "Mortal", "Extreme"],
        }

    @simple_trace("DungeonNameGenerator.generate_dungeon_name")
    def generate_dungeon_name(self, guidelines: DungeonGuidelines) -> str:
        """
        Generate a thematic dungeon name based on guidelines.

        Args:
            guidelines: Dungeon generation guidelines

        Returns:
            Generated dungeon name
        """
        # Get theme-specific components
        theme = guidelines.theme.lower()
        atmosphere = guidelines.atmosphere.lower()
        difficulty = guidelines.difficulty.lower()

        # Select appropriate components
        prefixes = self.theme_prefixes.get(theme, self.theme_prefixes["abandoned"])
        suffixes = self.theme_suffixes.get(theme, self.theme_suffixes["abandoned"])
        atmosphere_mods = self.atmosphere_modifiers.get(atmosphere, [])
        difficulty_mods = self.difficulty_modifiers.get(difficulty, [])

        # Build name components
        name_parts = []

        # Add atmosphere modifier (25% chance)
        if atmosphere_mods and random.random() < 0.25:
            name_parts.append(random.choice(atmosphere_mods))

        # Add difficulty modifier (20% chance)
        if difficulty_mods and random.random() < 0.20:
            name_parts.append(random.choice(difficulty_mods))

        # Add theme prefix
        name_parts.append(random.choice(prefixes))

        # Add theme suffix
        name_parts.append(random.choice(suffixes))

        # Combine into final name
        dungeon_name = " ".join(name_parts)

        # Add location descriptor (30% chance)
        if random.random() < 0.30:
            location_descriptors = [
                "of the Lost",
                "Under the Mountain",
                "Beyond the Veil",
                "in the Depths",
                "of Ancient Secrets",
                "Beneath the Surface",
                "of Forgotten Lore",
                "in the Shadows",
                "of the Damned",
                "Beyond the Gate",
            ]
            dungeon_name += f" {random.choice(location_descriptors)}"

        # Add span attributes for name generation
        current_span = trace.get_current_span()
        if current_span:
            current_span.set_attribute("name_generator.theme", guidelines.theme)
            current_span.set_attribute(
                "name_generator.atmosphere", guidelines.atmosphere
            )
            current_span.set_attribute(
                "name_generator.difficulty", guidelines.difficulty
            )
            current_span.set_attribute("name_generator.generated_name", dungeon_name)
            current_span.set_attribute(
                "name_generator.name_components", str(name_parts)
            )

        return dungeon_name

    def generate_alternative_names(
        self, guidelines: DungeonGuidelines, count: int = 3
    ) -> list[str]:
        """
        Generate alternative dungeon names for variety.

        Args:
            guidelines: Dungeon generation guidelines
            count: Number of alternative names to generate

        Returns:
            List of alternative names
        """
        names = []
        for _ in range(count):
            name = self.generate_dungeon_name(guidelines)
            if name not in names:
                names.append(name)

        # Ensure we have the requested number of unique names
        while len(names) < count:
            name = self.generate_dungeon_name(guidelines)
            if name not in names:
                names.append(name)

        return names
