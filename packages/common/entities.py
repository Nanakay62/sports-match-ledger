import re
from dataclasses import dataclass, field

from .models import EntityType

GLOSSARY_VERSION = "v1"


@dataclass(frozen=True)
class EntityAliasRecord:
    """Metadata tracking alias confidence and origin provenance per Handbook §15."""

    surface_form: str
    confidence: float = 1.0  # 1.0 = verified seed/admin, lower = auto-extracted
    provenance: str = "seed_data"  # "seed_data", "wikidata", "admin_override"
    language: str | None = None


@dataclass(frozen=True)
class CanonicalEntity:
    id: str
    name: str
    type: EntityType
    sport: str = "Football"
    aliases: list[str] = field(default_factory=list)
    alias_records: list[EntityAliasRecord] = field(default_factory=list)
    localized_names: dict[str, str] = field(default_factory=dict)


# Core multilingual entity seed graph with canonical localized translations
SEED_ENTITIES: list[CanonicalEntity] = [
    CanonicalEntity(
        id="ent-club-arsenal",
        name="Arsenal",
        type=EntityType.CLUB,
        aliases=["Arsenal FC", "The Gunners", "Arsenal Football Club"],
        localized_names={
            "en": "Arsenal",
            "it": "Arsenal",
            "es": "Arsenal",
            "de": "Arsenal",
            "fr": "Arsenal",
        },
    ),
    CanonicalEntity(
        id="ent-club-sporting",
        name="Sporting CP",
        type=EntityType.CLUB,
        aliases=["Sporting", "Sporting Lisbon", "Sporting Clube de Portugal"],
        localized_names={
            "en": "Sporting CP",
            "pt": "Sporting CP",
            "es": "Sporting de Portugal",
            "it": "Sporting Lisbona",
            "de": "Sporting Lissabon",
            "fr": "Sporting Portugal",
        },
    ),
    CanonicalEntity(
        id="ent-club-real-madrid",
        name="Real Madrid",
        type=EntityType.CLUB,
        aliases=["Real Madrid CF", "Madrid", "Los Blancos"],
        localized_names={
            "en": "Real Madrid",
            "es": "Real Madrid",
            "it": "Real Madrid",
            "de": "Real Madrid",
            "fr": "Real Madrid",
        },
    ),
    CanonicalEntity(
        id="ent-club-chelsea",
        name="Chelsea",
        type=EntityType.CLUB,
        aliases=["Chelsea FC", "The Blues"],
        localized_names={
            "en": "Chelsea",
            "it": "Chelsea",
            "es": "Chelsea",
            "de": "Chelsea",
            "fr": "Chelsea",
        },
    ),
    CanonicalEntity(
        id="ent-club-bayern",
        name="Bayern München",
        type=EntityType.CLUB,
        aliases=["Bayern Munich", "FC Bayern", "Bayern", "FC Bayern München"],
        localized_names={
            "en": "Bayern Munich",
            "de": "FC Bayern München",
            "it": "Bayern Monaco",
            "es": "Bayern Múnich",
            "fr": "Bayern Munich",
        },
    ),
    CanonicalEntity(
        id="ent-club-barcelona",
        name="Barcelona",
        type=EntityType.CLUB,
        aliases=["FC Barcelona", "Barca", "Barça", "Blaugrana"],
        localized_names={
            "en": "Barcelona",
            "es": "Barcelona",
            "it": "Barcellona",
            "de": "FC Barcelona",
            "fr": "Barcelone",
        },
    ),
    CanonicalEntity(
        id="ent-club-milan",
        name="AC Milan",
        type=EntityType.CLUB,
        aliases=["Milan", "Rossoneri", "A.C. Milan"],
        localized_names={
            "it": "Milan",
            "en": "AC Milan",
            "es": "AC Milan",
            "de": "AC Mailand",
            "fr": "AC Milan",
        },
    ),
    CanonicalEntity(
        id="ent-club-inter",
        name="Inter Milan",
        type=EntityType.CLUB,
        aliases=["Inter", "Internazionale", "Nerazzurri", "FC Internazionale"],
        localized_names={
            "it": "Inter",
            "en": "Inter Milan",
            "es": "Inter de Milán",
            "de": "Inter Mailand",
            "fr": "Inter Milan",
        },
    ),
    CanonicalEntity(
        id="ent-club-napoli",
        name="Napoli",
        type=EntityType.CLUB,
        aliases=["SSC Napoli", "Partenopei"],
        localized_names={
            "it": "Napoli",
            "en": "Napoli",
            "es": "Nápoles",
            "de": "SSC Neapel",
            "fr": "Naples",
        },
    ),
    CanonicalEntity(
        id="ent-club-juventus",
        name="Juventus",
        type=EntityType.CLUB,
        aliases=["Juve", "Bianconeri", "Juventus FC"],
        localized_names={
            "it": "Juventus",
            "en": "Juventus",
            "es": "Juventus",
            "de": "Juventus Turin",
            "fr": "Juventus",
        },
    ),
    CanonicalEntity(
        id="ent-club-psg",
        name="Paris Saint-Germain",
        type=EntityType.CLUB,
        aliases=["PSG", "Paris SG", "Paris"],
        localized_names={
            "fr": "Paris Saint-Germain",
            "en": "Paris Saint-Germain",
            "es": "París Saint-Germain",
            "de": "Paris Saint-Germain",
            "it": "Paris Saint-Germain",
        },
    ),
    CanonicalEntity(
        id="ent-club-west-ham",
        name="West Ham United",
        type=EntityType.CLUB,
        aliases=["West Ham", "The Hammers"],
        localized_names={
            "en": "West Ham United",
            "it": "West Ham",
            "es": "West Ham",
            "de": "West Ham United",
            "fr": "West Ham",
        },
    ),
    CanonicalEntity(
        id="ent-club-liverpool",
        name="Liverpool",
        type=EntityType.CLUB,
        aliases=["Liverpool FC", "The Reds"],
        localized_names={
            "en": "Liverpool",
            "it": "Liverpool",
            "es": "Liverpool",
            "de": "FC Liverpool",
            "fr": "Liverpool",
        },
    ),
    CanonicalEntity(
        id="ent-club-man-city",
        name="Manchester City",
        type=EntityType.CLUB,
        aliases=["Man City", "City", "MCFC"],
        localized_names={
            "en": "Manchester City",
            "it": "Manchester City",
            "es": "Manchester City",
            "de": "Manchester City",
            "fr": "Manchester City",
        },
    ),
    CanonicalEntity(
        id="ent-club-girona",
        name="Girona",
        type=EntityType.CLUB,
        aliases=["Girona FC"],
        localized_names={
            "es": "Girona",
            "en": "Girona",
            "it": "Girona",
            "de": "FC Girona",
            "fr": "Gérone",
        },
    ),
    CanonicalEntity(
        id="ent-club-al-nassr",
        name="Al-Nassr",
        type=EntityType.CLUB,
        aliases=["Al Nassr FC", "Al-Nassr Club"],
        localized_names={
            "en": "Al-Nassr",
            "ar": "النصر",
            "it": "Al-Nassr",
            "es": "Al-Nassr",
            "de": "Al-Nassr FC",
        },
    ),
    CanonicalEntity(
        id="ent-club-brighton",
        name="Brighton & Hove Albion",
        type=EntityType.CLUB,
        aliases=["Brighton", "The Seagulls"],
        localized_names={
            "en": "Brighton & Hove Albion",
            "it": "Brighton",
            "es": "Brighton",
            "de": "Brighton & Hove Albion",
            "fr": "Brighton",
        },
    ),
    CanonicalEntity(
        id="ent-club-newcastle",
        name="Newcastle United",
        type=EntityType.CLUB,
        aliases=["Newcastle", "The Magpies", "NUFC"],
        localized_names={
            "en": "Newcastle United",
            "it": "Newcastle",
            "es": "Newcastle",
            "de": "Newcastle United",
            "fr": "Newcastle",
        },
    ),
    # Players
    CanonicalEntity(
        id="ent-player-osei",
        name="Emeka Osei",
        type=EntityType.PLAYER,
        aliases=["Osei"],
        localized_names={
            "en": "Emeka Osei",
            "it": "Emeka Osei",
            "es": "Emeka Osei",
            "de": "Emeka Osei",
            "fr": "Emeka Osei",
        },
    ),
    CanonicalEntity(
        id="ent-player-mbappe",
        name="Kylian Mbappé",
        type=EntityType.PLAYER,
        aliases=["Mbappé", "Mbappe", "Kylian Mbappe"],
        localized_names={
            "en": "Kylian Mbappé",
            "fr": "Kylian Mbappé",
            "es": "Kylian Mbappé",
            "it": "Kylian Mbappé",
            "de": "Kylian Mbappé",
        },
    ),
    CanonicalEntity(
        id="ent-player-lindqvist",
        name="Jonas Lindqvist",
        type=EntityType.PLAYER,
        aliases=["Lindqvist"],
    ),
    CanonicalEntity(
        id="ent-player-duarte",
        name="Rafael Duarte",
        type=EntityType.PLAYER,
        aliases=["Duarte"],
    ),
    CanonicalEntity(
        id="ent-player-mori",
        name="Kaito Mori",
        type=EntityType.PLAYER,
        aliases=["Mori"],
    ),
    CanonicalEntity(
        id="ent-player-barski",
        name="Viktor Barski",
        type=EntityType.PLAYER,
        aliases=["Barski"],
    ),
    CanonicalEntity(
        id="ent-player-cifuentes",
        name="Andrés Cifuentes",
        type=EntityType.PLAYER,
        aliases=["Cifuentes", "Andres Cifuentes"],
    ),
    CanonicalEntity(
        id="ent-player-novak",
        name="Karel Novák",
        type=EntityType.PLAYER,
        aliases=["Novak", "Karel Novak"],
    ),
    CanonicalEntity(
        id="ent-player-ferraz",
        name="Thiago Ferraz",
        type=EntityType.PLAYER,
        aliases=["Ferraz"],
    ),
    CanonicalEntity(
        id="ent-player-sy",
        name="Amadou Sy",
        type=EntityType.PLAYER,
        aliases=["Sy"],
    ),
    CanonicalEntity(
        id="ent-player-brandt",
        name="Luca Brandt",
        type=EntityType.PLAYER,
        aliases=["Brandt"],
    ),
]


class EntityGraph:
    """Multilingual entity lookup and alias resolution graph with localized glossaries."""

    def __init__(self, entities: list[CanonicalEntity] | None = None):
        self._entities_by_id: dict[str, CanonicalEntity] = {}
        self._alias_map: dict[str, CanonicalEntity] = {}
        self._alias_meta_map: dict[str, EntityAliasRecord] = {}
        for entity in entities or SEED_ENTITIES:
            self.register_entity(entity)

    def register_entity(self, entity: CanonicalEntity) -> None:
        self._entities_by_id[entity.id] = entity
        self._alias_map[entity.name.lower()] = entity
        self._alias_meta_map[entity.name.lower()] = EntityAliasRecord(
            surface_form=entity.name,
            confidence=1.0,
            provenance="canonical",
        )
        for alias in entity.aliases:
            self._alias_map[alias.lower()] = entity
            self._alias_meta_map[alias.lower()] = EntityAliasRecord(
                surface_form=alias,
                confidence=1.0,
                provenance="seed_data",
            )
        for rec in entity.alias_records:
            self._alias_map[rec.surface_form.lower()] = entity
            self._alias_meta_map[rec.surface_form.lower()] = rec

    def get_entity_by_id(self, entity_id: str) -> CanonicalEntity | None:
        """Retrieves canonical entity by ID."""
        return self._entities_by_id.get(entity_id)

    def resolve_alias(self, name_or_alias: str) -> CanonicalEntity | None:
        return self._alias_map.get(name_or_alias.strip().lower())

    def get_alias_metadata(self, name_or_alias: str) -> EntityAliasRecord | None:
        """Retrieves confidence score and provenance origin for an entity alias."""
        return self._alias_meta_map.get(name_or_alias.strip().lower())

    def get_localized_glossary(self, entity_ids: list[str], target_lang: str) -> dict[str, str]:
        """Returns mapping from source entity names and aliases to the target language canonical term.

        Ensures translation preserves exact football terminology per Handbook §15.4.
        """
        glossary: dict[str, str] = {}
        for eid in entity_ids:
            entity = self._entities_by_id.get(eid)
            if not entity:
                # Also try lookup by name
                entity = self.resolve_alias(eid)
            if not entity:
                continue

            target_name = entity.localized_names.get(target_lang, entity.name)
            glossary[entity.name] = target_name
            for alias in entity.aliases:
                glossary[alias] = target_name

        return glossary

    def extract_entities(self, text: str) -> list[CanonicalEntity]:
        """Scans raw text and returns unique canonical entities matched."""
        matched: dict[str, CanonicalEntity] = {}
        # Sort alias keys by length descending to match longer multi-word phrases first
        sorted_aliases = sorted(self._alias_map.keys(), key=len, reverse=True)

        lower_text = text.lower()
        for alias in sorted_aliases:
            # Word boundary regex search
            pattern = r"\b" + re.escape(alias) + r"\b"
            if re.search(pattern, lower_text):
                canonical = self._alias_map[alias]
                if canonical.id not in matched:
                    matched[canonical.id] = canonical

        return list(matched.values())


default_entity_graph = EntityGraph()
