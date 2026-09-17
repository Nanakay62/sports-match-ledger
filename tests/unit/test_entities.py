from packages.common.entities import default_entity_graph


def test_alias_resolution():
    # Sporting variants
    e1 = default_entity_graph.resolve_alias("Sporting")
    e2 = default_entity_graph.resolve_alias("Sporting Lisbon")
    e3 = default_entity_graph.resolve_alias("Sporting CP")
    assert e1 is not None and e2 is not None and e3 is not None
    assert e1.name == "Sporting CP"
    assert e2.name == "Sporting CP"
    assert e3.name == "Sporting CP"

    # Arsenal variants
    a1 = default_entity_graph.resolve_alias("The Gunners")
    assert a1 is not None and a1.name == "Arsenal"


def test_entity_extraction_from_text():
    text = "Arsenal and Sporting Lisbon have agreed a fee for striker Emeka Osei."
    extracted = default_entity_graph.extract_entities(text)
    names = {e.name for e in extracted}

    assert "Arsenal" in names
    assert "Sporting CP" in names
    assert "Emeka Osei" in names
    assert len(extracted) == 3


def test_unmatched_text_returns_empty():
    text = "A random sentence about non-sports topics."
    extracted = default_entity_graph.extract_entities(text)
    assert len(extracted) == 0


def test_alias_metadata_and_provenance():
    # Test built-in seed alias metadata
    meta_gunners = default_entity_graph.get_alias_metadata("The Gunners")
    assert meta_gunners is not None
    assert meta_gunners.surface_form == "The Gunners"
    assert meta_gunners.confidence == 1.0
    assert meta_gunners.provenance == "seed_data"

    meta_sporting = default_entity_graph.get_alias_metadata("Sporting Lisbon")
    assert meta_sporting is not None
    assert meta_sporting.confidence == 1.0

    # Non-existent alias
    meta_none = default_entity_graph.get_alias_metadata("NonExistentClubXYZ")
    assert meta_none is None
