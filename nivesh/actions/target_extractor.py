"""Target extraction and normalization component for Engine 3.

Identifies the recipient, channel, application, website, or entity that the action
operates upon, without making claims regarding its legitimacy.
Maintains privacy by not persisting sensitive account or credential data.
"""

import re
from typing import Optional
from nivesh.schemas.actions import ActionTarget, ActionType, TargetType
from nivesh.schemas.normalized import NormalizedContent


class ActionTargetExtractor:
    """Extracts and normalizes ActionTarget from text and Engine 1 structured signals."""

    def extract_target(
        self,
        action_text: str,
        action_type: ActionType,
        content: Optional[NormalizedContent] = None,
    ) -> ActionTarget:
        """Extracts normalized ActionTarget for the given action snippet."""
        clean = action_text.strip()
        lower = clean.lower()

        # 1. Channels (Telegram, WhatsApp, Instagram, YouTube)
        if action_type in {"JOIN_CHANNEL", "JOIN_GROUP", "FOLLOW_ACCOUNT"}:
            if "telegram" in lower or "t.me" in lower:
                # Look for specific telegram handle/url in content or snippet
                t_val = "Telegram"
                if content and content.structured_signals:
                    for h in content.structured_signals.social_handles:
                        if h.platform.lower() == "telegram" and (h.handle in clean or h.raw in clean or len(clean) > 0):
                            t_val = h.raw or h.handle
                            break
                    if t_val == "Telegram":
                        for u in content.structured_signals.urls:
                            if "t.me" in u.url.lower():
                                t_val = u.url
                                break
                return ActionTarget(type="channel", value=t_val)

            if "whatsapp" in lower or "wa.me" in lower or "chat.whatsapp" in lower:
                w_val = "WhatsApp"
                if content and content.structured_signals:
                    for h in content.structured_signals.social_handles:
                        if h.platform.lower() == "whatsapp":
                            w_val = h.raw or h.handle
                            break
                return ActionTarget(type="channel", value=w_val)

            if "instagram" in lower:
                return ActionTarget(type="channel", value="Instagram")
            if "youtube" in lower:
                return ActionTarget(type="channel", value="YouTube")
            return ActionTarget(type="channel", value="channel")

        # 2. Applications (App, APK, Software)
        if action_type in {"DOWNLOAD", "INSTALL"}:
            if "apk" in lower:
                return ActionTarget(type="application", value="APK")
            if "app" in lower:
                return ActionTarget(type="application", value="app")
            return ActionTarget(type="application", value="application")

        # 3. Person / Contacts (Email, Phone, Person)
        if action_type in {"CONTACT", "CALL_PERSON", "MESSAGE_PERSON"}:
            # Check for email in action text
            email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", clean)
            if email_match:
                return ActionTarget(type="person", value=email_match.group(0).lower())
            if content and content.structured_signals and content.structured_signals.email_addresses:
                for email in content.structured_signals.email_addresses:
                    if email.lower() in lower:
                        return ActionTarget(type="person", value=email.lower())

            # Check for phone in action text
            phone_match = re.search(r"(?:\+91[\-\s]?)?[6789]\d{9}", clean)
            if phone_match:
                return ActionTarget(type="person", value=phone_match.group(0))
            if content and content.structured_signals and content.structured_signals.phone_numbers:
                for ph in content.structured_signals.phone_numbers:
                    if ph in clean:
                        return ActionTarget(type="person", value=ph)

            # Check for person name in content entities
            if content and content.entities and content.entities.people:
                for p in content.entities.people:
                    if p.normalized.lower() in lower:
                        return ActionTarget(type="person", value=p.normalized)

            return ActionTarget(type="person", value=None)

        # 4. Websites / Links
        if action_type in {"CLICK_LINK", "OPEN_WEBSITE"}:
            url_match = re.search(r"https?://\S+", clean)
            if url_match:
                return ActionTarget(type="website", value=url_match.group(0).rstrip(".,!?"))
            if content and content.structured_signals and content.structured_signals.urls:
                for u in content.structured_signals.urls:
                    if u.url in clean:
                        return ActionTarget(type="website", value=u.url)
            return ActionTarget(type="website", value=None)

        # 5. Accounts / Financial Targets
        if action_type in {"PAYMENT", "TRANSFER_MONEY", "DEPOSIT_MONEY", "WITHDRAW_MONEY"}:
            # Privacy rule: Do NOT store full bank/account credentials
            if any(w in lower for w in ["account", "bank", "vpa", "upi"]):
                return ActionTarget(type="account", value="account")
            return ActionTarget(type="account", value="unknown")

        return ActionTarget(type="unknown", value=None)
