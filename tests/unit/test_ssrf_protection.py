import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from packages.database.models import Base, QuarantinedDocumentModel, SourceRegistryModel
from workers.pipeline.feed_poller import FeedPoller, is_safe_public_url


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_is_safe_public_url_blocks_loopback_and_private_ips():
    """Verifies that loopback, RFC1918 private subnets, and metadata IPs are rejected."""
    # Loopback
    safe, msg = is_safe_public_url("http://127.0.0.1:8000/feed.rss")
    assert safe is False
    assert "Blocked private/reserved IP" in msg

    safe, msg = is_safe_public_url("http://localhost:3000/feed")
    assert safe is False
    assert "Blocked localhost" in msg

    # Private IP networks
    safe, msg = is_safe_public_url("http://10.0.0.1/feed.xml")
    assert safe is False
    assert "Blocked private/reserved IP" in msg

    safe, msg = is_safe_public_url("http://192.168.1.100/rss")
    assert safe is False
    assert "Blocked private/reserved IP" in msg

    safe, msg = is_safe_public_url("http://172.16.5.20/feed")
    assert safe is False
    assert "Blocked private/reserved IP" in msg

    # Cloud Instance Metadata IP (AWS, Azure, GCP)
    safe, msg = is_safe_public_url("http://169.254.169.254/latest/meta-data/")
    assert safe is False
    assert "Blocked private/reserved IP" in msg


def test_is_safe_public_url_blocks_non_http_schemes():
    """Verifies that non-HTTP/HTTPS schemes (file://, ftp://, gopher://) are rejected."""
    safe, msg = is_safe_public_url("file:///etc/passwd")
    assert safe is False
    assert "Unsupported scheme" in msg

    safe, msg = is_safe_public_url("ftp://ftp.example.com/feed.xml")
    assert safe is False
    assert "Unsupported scheme" in msg


def test_is_safe_public_url_allows_public_urls():
    """Verifies that standard public hostnames pass validation."""
    # Test well-known public domain (DNS resolution test)
    safe, msg = is_safe_public_url("https://www.bbc.com/sport/football/rss.xml")
    assert safe is True
    assert msg == "valid"


def test_fetch_feed_content_raises_permission_error_on_ssrf():
    """Verifies fetch_feed_content refuses to open sockets to internal/private targets."""
    with pytest.raises(PermissionError) as exc_info:
        FeedPoller.fetch_feed_content("http://127.0.0.1:8080/internal-secrets")
    assert "SSRF Protection" in str(exc_info.value)


def test_feed_poller_routes_ssrf_attempt_to_quarantine(db_session):
    """Verifies that an approved source pointing to a private IP is quarantined upon polling."""
    # Register source pointing to loopback
    malicious_src = SourceRegistryModel(
        id="src-ssrf-test",
        source_name="Rogue Source",
        feed_url="http://127.0.0.1:9000/feed.xml",
        feed_format="rss2",
        language="en",
        status="approved",
    )
    db_session.add(malicious_src)
    db_session.commit()

    poller = FeedPoller(session_factory=lambda: db_session)
    result = poller.poll_source_by_registry_id("src-ssrf-test", session=db_session)

    assert result["status"] == "security_quarantine"
    assert "SSRF Protection" in result["reason"]

    # Quarantined document row recorded in ledger DB
    quarantined = db_session.execute(select(QuarantinedDocumentModel)).scalars().all()
    assert len(quarantined) == 1
    assert quarantined[0].source_name == "Rogue Source"
    assert "Security Violation (SSRF)" in quarantined[0].rejection_reason
