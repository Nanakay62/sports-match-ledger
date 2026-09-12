import hashlib
import re


def normalize_text(text: str) -> str:
    """Normalizes text by removing punctuation, converting to lowercase, and collapsing whitespace."""
    lower_text = text.lower()
    cleaned = re.sub(r"[^\w\s]", " ", lower_text)
    return re.sub(r"\s+", " ", cleaned).strip()


def compute_content_hash(text: str) -> str:
    """Returns SHA-256 digest of normalized text for exact content matching."""
    norm = normalize_text(text)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def compute_simhash(text: str, hash_bits: int = 64) -> str:
    """Computes a 64-bit SimHash fingerprint as a 16-character hex string."""
    norm = normalize_text(text)
    tokens = norm.split()
    if not tokens:
        return "0" * (hash_bits // 4)

    shingles: list[str] = list(tokens)
    for i in range(len(tokens) - 2):
        shingles.append(f"{tokens[i]} {tokens[i + 1]} {tokens[i + 2]}")

    vector = [0] * hash_bits
    for shingle in shingles:
        digest = hashlib.md5(shingle.encode("utf-8")).digest()
        token_hash = int.from_bytes(digest[:8], byteorder="big")
        for bit_idx in range(hash_bits):
            if (token_hash >> bit_idx) & 1:
                vector[bit_idx] += 1
            else:
                vector[bit_idx] -= 1

    fingerprint = 0
    for bit_idx in range(hash_bits):
        if vector[bit_idx] > 0:
            fingerprint |= 1 << bit_idx

    return f"{fingerprint:016x}"


def simhash_hamming_distance(h1: str | int, h2: str | int) -> int:
    """Calculates the number of differing bits (Hamming distance) between two 64-bit fingerprints."""
    val1 = int(h1, 16) if isinstance(h1, str) else h1
    val2 = int(h2, 16) if isinstance(h2, str) else h2
    return bin(val1 ^ val2).count("1")


def jaccard_similarity(text1: str, text2: str) -> float:
    """Calculates word-level Jaccard set similarity between two texts."""
    words1 = set(normalize_text(text1).split())
    words2 = set(normalize_text(text2).split())
    if not words1 or not words2:
        return 0.0
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    return round(intersection / union, 4) if union > 0 else 0.0


def strip_boilerplate(text: str) -> str:
    """Removes wire datelines, RSS trailing notices, photo credits, and syndication boilerplate."""
    if not text:
        return ""

    import html

    cleaned = html.unescape(text).strip()

    # 1. Strip leading wire datelines/stamps:
    # e.g., "LONDON (Reuters) - ", "ROME (ANSA) - ", "MADRID (EFE) : ", "PARIS (AFP) - "
    cleaned = re.sub(
        r"^[A-Z\s]{2,25}\s*\([A-Za-z\s,\.\-]+\)\s*[-:]\s*",
        "",
        cleaned,
    )
    # e.g., "LONDON - ", "MILAN : ", "MADRID - "
    cleaned = re.sub(
        r"^[A-Z]{3,15}\s*[-:]\s*",
        "",
        cleaned,
    )

    # 2. Strip trailing syndication/RSS notices, social links, and photo credits
    # English trailing patterns
    cleaned = re.sub(
        r"(?i)(?:[\.\n]|\s[-:])\s*(?:read\s+(?:more|the\s+full\s+article|also|on)|continue\s+reading|follow\s+us|subscribe\s+to|click\s+here).*$",
        ".",
        cleaned,
    )
    # Italian trailing patterns
    cleaned = re.sub(
        r"(?i)(?:[\.\n]|\s[-:])\s*(?:per\s+saperne\s+di\s+pi[uù]|segui\s+tutti\s+gli\s+aggiornamenti|tutti\s+i\s+diritti\s+riservati|foto\s+di|guarda\s+anche|leggi\s+anche).*$",
        ".",
        cleaned,
    )
    # Spanish trailing patterns
    cleaned = re.sub(
        r"(?i)(?:[\.\n]|\s[-:])\s*(?:m[aá]s\s+informaci[oó]n|leer\s+m[aá]s|todos\s+los\s+derechos\s+reservados).*$",
        ".",
        cleaned,
    )
    # Generic photo credits / copyright trailers
    cleaned = re.sub(
        r"(?i)(?:[\.\n]|\s[-:])\s*(?:photo\s+credit|image\s+credit|image\s+copyright|all\s+rights\s+reserved).*$",
        ".",
        cleaned,
    )
    # Trailing URLs
    cleaned = re.sub(r"\s*https?://\S+$", "", cleaned)

    # Collapse repeated whitespace
    result = re.sub(r"\s+", " ", cleaned).strip()
    return result if len(result) >= 10 else text.strip()


def lead_paragraph_similarity(text1: str, text2: str, max_words: int = 40) -> float:
    """Calculates word-level Jaccard similarity over the opening sentence or lead window of two texts."""
    sent1 = text1.split(".")[0].strip()
    sent2 = text2.split(".")[0].strip()
    sent_sim = jaccard_similarity(sent1, sent2) if (len(sent1.split()) >= 6 and len(sent2.split()) >= 6) else 0.0

    words1 = " ".join(normalize_text(text1).split()[:max_words])
    words2 = " ".join(normalize_text(text2).split()[:max_words])
    word_sim = jaccard_similarity(words1, words2)

    return max(sent_sim, word_sim)


def is_near_duplicate(
    text1: str,
    text2: str,
    jaccard_threshold: float = 0.80,
    max_hamming_distance: int = 8,
    lead_threshold: float = 0.75,
) -> tuple[bool, float]:
    """Determines whether two texts are near-duplicates using normalized content hash,
    Jaccard similarity, SimHash Hamming distance, and lead text comparison.

    Returns a tuple of (is_match, similarity_score).
    """
    clean1 = strip_boilerplate(text1)
    clean2 = strip_boilerplate(text2)

    hash1 = compute_content_hash(clean1)
    hash2 = compute_content_hash(clean2)
    if hash1 == hash2:
        return True, 1.0

    j_sim = jaccard_similarity(clean1, clean2)
    sh1 = compute_simhash(clean1)
    sh2 = compute_simhash(clean2)
    dist = simhash_hamming_distance(sh1, sh2)
    sh_sim = round(1.0 - (dist / 64.0), 4)

    lead_sim = lead_paragraph_similarity(clean1, clean2)

    # Lead similarity match requires sufficient word count (at least 12 words in each text)
    words1_count = len(normalize_text(clean1).split())
    words2_count = len(normalize_text(clean2).split())
    lead_match = lead_sim >= lead_threshold and words1_count >= 12 and words2_count >= 12

    is_match = j_sim >= jaccard_threshold or dist <= max_hamming_distance or lead_match
    score = max(j_sim, sh_sim, lead_sim if lead_match else 0.0)
    return is_match, score
