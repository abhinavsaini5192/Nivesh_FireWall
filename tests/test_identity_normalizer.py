"""Unit tests for Engine 9 Normalization (Names, Organizations, Domains, Handles)."""

from nivesh.identity.normalizer import IdentityNormalizer


def test_person_name_normalization_basics():
    """Verify title stripping, lowercase, and whitespace handling."""
    assert IdentityNormalizer.normalize_person_name("Mr. Rahul Sharma") == "rahul sharma"
    assert IdentityNormalizer.normalize_person_name("Dr. Rahul Sharma") == "rahul sharma"
    assert IdentityNormalizer.normalize_person_name("CA Rahul Sharma") == "rahul sharma"
    assert IdentityNormalizer.normalize_person_name("  rahul    sharma  ") == "rahul sharma"


def test_person_name_non_aggressive_merging():
    """Verify that similar names are strictly NOT collapsed into the same string."""
    name1 = IdentityNormalizer.normalize_person_name("Rahul Sharma")
    name2 = IdentityNormalizer.normalize_person_name("Rahul K Sharma")
    name3 = IdentityNormalizer.normalize_person_name("Rahul Kumar Sharma")

    assert name1 != name2
    assert name2 != name3
    assert name1 != name3


def test_org_name_normalization_legal_suffixes():
    """Verify canonical stripping while preserving standard legal forms."""
    canon1, legal1 = IdentityNormalizer.normalize_org_name("ABC Securities Pvt. Ltd.")
    canon2, legal2 = IdentityNormalizer.normalize_org_name("ABC Securities Private Limited")
    canon3, legal3 = IdentityNormalizer.normalize_org_name("ABC Securities Ltd")
    canon4, legal4 = IdentityNormalizer.normalize_org_name("ABC Securities LLP")

    # Canonical root names must match for entity resolution
    assert canon1 == "ABC SECURITIES"
    assert canon2 == "ABC SECURITIES"
    assert canon3 == "ABC SECURITIES"
    assert canon4 == "ABC SECURITIES"

    # Legal suffixes are normalized cleanly
    assert legal1 == "ABC Securities PVT LTD"
    assert legal2 == "ABC Securities PVT LTD"
    assert legal3 == "ABC Securities LTD"
    assert legal4 == "ABC Securities LLP"


def test_domain_normalization_and_tracking_stripping():
    """Verify URL, subdomain, tracking parameters, and two-part TLD parsing."""
    root1, host1 = IdentityNormalizer.normalize_domain("https://www.abcsecurities.com/login?utm_source=telegram&ref=123")
    assert root1 == "abcsecurities.com"
    assert host1 == "abcsecurities.com"

    root2, host2 = IdentityNormalizer.normalize_domain("portal.secure.investments.co.in:8080/app")
    assert root2 == "investments.co.in"
    assert host2 == "portal.secure.investments.co.in"

    root3, host3 = IdentityNormalizer.normalize_domain("http://abc-secure-invest.com")
    assert root3 == "abc-secure-invest.com"


def test_registration_id_normalization():
    """Verify whitespace, hyphen, and slash stripping in registration IDs."""
    assert IdentityNormalizer.normalize_registration_id("INA 0000 12345") == "INA000012345"
    assert IdentityNormalizer.normalize_registration_id("inh-00000-9999") == "INH000009999"
    assert IdentityNormalizer.normalize_registration_id("U67120/MH/2010/PTC123456") == "U67120MH2010PTC123456"


def test_social_handle_normalization():
    """Verify Telegram, WhatsApp, Twitter, Instagram, and YouTube handle extraction."""
    plat1, handle1 = IdentityNormalizer.normalize_social_handle("https://t.me/rahulinvest?start=ref")
    assert plat1 == "telegram"
    assert handle1 == "rahulinvest"

    plat2, handle2 = IdentityNormalizer.normalize_social_handle("@rahul_official", platform="telegram")
    assert plat2 == "telegram"
    assert handle2 == "rahul_official"

    plat3, handle3 = IdentityNormalizer.normalize_social_handle("https://twitter.com/SEBI_Invest")
    assert plat3 == "twitter"
    assert handle3 == "sebi_invest"

    plat4, handle4 = IdentityNormalizer.normalize_social_handle("https://chat.whatsapp.com/INVITECODE")
    assert plat4 == "whatsapp"
    assert handle4 == "invitecode"
