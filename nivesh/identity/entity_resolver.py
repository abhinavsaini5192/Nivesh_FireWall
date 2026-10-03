"""Claimed Entity Extraction and Resolution for Engine 9.

Aggregates entity references across NormalizedContent, Claims, and Signals
into structured ClaimedEntity instances with associated registrations,
domains, and channels.
"""

from typing import Optional
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.identity.schemas import (
    ClaimedEntity,
    IdentityEntityType,
)
from nivesh.identity.normalizer import IdentityNormalizer


class EntityResolver:
    """Extracts, normalizes, and groups claimed entities from upstream intelligence."""

    ROLE_KEYWORDS = {
        "advisor": IdentityEntityType.ADVISER,
        "adviser": IdentityEntityType.ADVISER,
        "investment advisor": IdentityEntityType.ADVISER,
        "research analyst": IdentityEntityType.ADVISER,
        "broker": IdentityEntityType.BROKER,
        "stockbroker": IdentityEntityType.BROKER,
        "sub-broker": IdentityEntityType.BROKER,
        "intermediary": IdentityEntityType.FINANCIAL_INTERMEDIARY,
        "mutual fund": IdentityEntityType.ORGANIZATION,
        "amc": IdentityEntityType.ORGANIZATION,
    }

    REGULATOR_NAMES = {
        "sebi": "SEBI",
        "rbi": "RBI",
        "nse": "NSE",
        "bse": "BSE",
        "irda": "IRDAI",
        "irdai": "IRDAI",
        "pfrda": "PFRDA",
    }

    @classmethod
    def resolve_claimed_entities(
        cls,
        content: NormalizedContent,
        claims: Optional[ClaimAnalysis] = None,
    ) -> list[ClaimedEntity]:
        """Resolves all claimed and observed entities in the interaction."""
        entities: list[ClaimedEntity] = []
        seen_keys: set[str] = set()
        ent_counter = 1

        # 1. Associated signals
        primary_reg = None
        for reg in content.structured_signals.registration_numbers:
            primary_reg = reg.value
            break

        primary_domain = None
        for d in content.structured_signals.domains:
            primary_domain = d.domain
            break
        if not primary_domain and content.structured_signals.urls:
            primary_domain = content.structured_signals.urls[0].domain

        primary_channel = None
        for h in content.structured_signals.social_handles:
            primary_channel = f"{h.platform}:{h.handle}"
            break

        # 2. Extract People from NormalizedContent
        for p in content.entities.people:
            raw_name = p.text
            norm_name = IdentityNormalizer.normalize_person_name(raw_name)
            key = f"PERSON:{norm_name}"
            if key not in seen_keys and norm_name:
                seen_keys.add(key)
                
                # Check for role attribution
                ent_type = IdentityEntityType.PERSON
                lower_raw = content.normalized.text.lower()
                for kw, mapped_role in cls.ROLE_KEYWORDS.items():
                    if kw in lower_raw:
                        ent_type = mapped_role
                        break

                entities.append(ClaimedEntity(
                    entity_id=f"ENT-{ent_counter:03d}",
                    name=raw_name,
                    normalized_name=norm_name,
                    entity_type=ent_type,
                    original_form=p.normalized or raw_name,
                    associated_registration=primary_reg,
                    associated_domain=primary_domain,
                    associated_channel=primary_channel,
                    source_claim_ids=[c.claim_id for c in (claims.claims if claims else []) if norm_name in c.text.normalized.lower()],
                    attributes={"source": "content.entities.people"},
                ))
                ent_counter += 1

        # 3. Extract Organizations from NormalizedContent
        for o in content.entities.organizations:
            raw_org = o.text
            canon_name, clean_legal = IdentityNormalizer.normalize_org_name(raw_org)
            key = f"ORG:{canon_name}"
            if key not in seen_keys and canon_name:
                seen_keys.add(key)

                # Check if it's actually a known regulator
                if canon_name.lower() in cls.REGULATOR_NAMES:
                    ent_type = IdentityEntityType.REGULATOR
                    canon_name = cls.REGULATOR_NAMES[canon_name.lower()]
                else:
                    ent_type = IdentityEntityType.ORGANIZATION

                entities.append(ClaimedEntity(
                    entity_id=f"ENT-{ent_counter:03d}",
                    name=raw_org,
                    normalized_name=canon_name,
                    entity_type=ent_type,
                    original_form=clean_legal,
                    associated_registration=primary_reg,
                    associated_domain=primary_domain,
                    associated_channel=primary_channel,
                    source_claim_ids=[c.claim_id for c in (claims.claims if claims else []) if canon_name.lower() in c.text.normalized.lower()],
                    attributes={"clean_legal_name": clean_legal},
                ))
                ent_counter += 1

        # 4. Extract Regulators from NormalizedContent
        for r in content.entities.regulators:
            raw_reg = r.text
            canon_reg = cls.REGULATOR_NAMES.get(raw_reg.lower(), raw_reg.upper())
            key = f"REGULATOR:{canon_reg}"
            if key not in seen_keys:
                seen_keys.add(key)
                entities.append(ClaimedEntity(
                    entity_id=f"ENT-{ent_counter:03d}",
                    name=raw_reg,
                    normalized_name=canon_reg,
                    entity_type=IdentityEntityType.REGULATOR,
                    original_form=raw_reg,
                    source_claim_ids=[c.claim_id for c in (claims.claims if claims else []) if canon_reg.lower() in c.text.normalized.lower()],
                    attributes={"regulator_jurisdiction": "IN"},
                ))
                ent_counter += 1

        # 5. Extract Domains as explicit DOMAIN entities (distinguished from Person/Org)
        for d in content.structured_signals.domains:
            root_d, host_d = IdentityNormalizer.normalize_domain(d.domain)
            key = f"DOMAIN:{root_d}"
            if key not in seen_keys and root_d:
                seen_keys.add(key)
                entities.append(ClaimedEntity(
                    entity_id=f"ENT-{ent_counter:03d}",
                    name=d.domain,
                    normalized_name=root_d,
                    entity_type=IdentityEntityType.DOMAIN,
                    original_form=host_d,
                    associated_domain=root_d,
                    attributes={"effective_host": host_d},
                ))
                ent_counter += 1

        # 6. Extract Social Channels as explicit CHANNEL / SOCIAL_ACCOUNT entities
        for h in content.structured_signals.social_handles:
            plat, handle = IdentityNormalizer.normalize_social_handle(h.handle, h.platform)
            key = f"CHANNEL:{plat}:{handle}"
            if key not in seen_keys and handle:
                seen_keys.add(key)
                entities.append(ClaimedEntity(
                    entity_id=f"ENT-{ent_counter:03d}",
                    name=f"@{handle}" if h.platform != "whatsapp" else handle,
                    normalized_name=handle,
                    entity_type=IdentityEntityType.CHANNEL if plat in ("telegram", "whatsapp") else IdentityEntityType.SOCIAL_ACCOUNT,
                    original_form=h.raw,
                    associated_channel=f"{plat}:{handle}",
                    attributes={"platform": plat},
                ))
                ent_counter += 1

        # 7. Check claims for subjects/attribution not yet captured
        if claims:
            for c in claims.claims:
                subj = c.subject.strip()
                if not subj or len(subj.split()) > 12 or subj.lower() in ("learn", "we", "i", "they", "our team"):
                    continue

                canon_s, clean_s = IdentityNormalizer.normalize_org_name(subj)
                norm_p = IdentityNormalizer.normalize_person_name(subj)

                # Check if already captured in entities
                already_captured = False
                for e in entities:
                    e_name = e.name.lower()
                    e_norm = e.normalized_name.lower()
                    if (
                        e_name in subj.lower()
                        or subj.lower() in e_name
                        or (canon_s and (canon_s.lower() in e_norm or e_norm in canon_s.lower()))
                        or (norm_p and norm_p == e_norm)
                    ):
                        already_captured = True
                        if c.claim_id not in e.source_claim_ids:
                            e.source_claim_ids.append(c.claim_id)
                        break

                if already_captured:
                    continue

                # Determine if organization or person
                is_org = any(suffix in subj.lower() for suffix in ("ltd", "limited", "pvt", "llp", "inc", "corp", "company", "fund", "bank", "securities"))
                if is_org:
                    key = f"ORG:{canon_s}"
                    if key not in seen_keys and canon_s and len(canon_s) >= 2:
                        seen_keys.add(key)
                        entities.append(ClaimedEntity(
                            entity_id=f"ENT-{ent_counter:03d}",
                            name=subj,
                            normalized_name=canon_s,
                            entity_type=IdentityEntityType.ORGANIZATION,
                            original_form=clean_s,
                            associated_registration=primary_reg,
                            associated_domain=primary_domain,
                            associated_channel=primary_channel,
                            source_claim_ids=[c.claim_id],
                            attributes={"source": "claim.subject"},
                        ))
                        ent_counter += 1
                else:
                    key = f"PERSON:{norm_p}"
                    if key not in seen_keys and norm_p and len(norm_p) >= 3:
                        seen_keys.add(key)
                        entities.append(ClaimedEntity(
                            entity_id=f"ENT-{ent_counter:03d}",
                            name=subj,
                            normalized_name=norm_p,
                            entity_type=IdentityEntityType.PERSON,
                            original_form=subj,
                            associated_registration=primary_reg,
                            associated_domain=primary_domain,
                            associated_channel=primary_channel,
                            source_claim_ids=[c.claim_id],
                            attributes={"source": "claim.subject"},
                        ))
                        ent_counter += 1

        return entities

