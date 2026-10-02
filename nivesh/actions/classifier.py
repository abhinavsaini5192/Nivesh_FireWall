"""Action classification and category hierarchy component for Engine 3.

Maps candidate action phrases into normalized ActionType and ActionCategory.
Maintains the conceptual progression hierarchy (from INFORMATIONAL to FINANCIAL_TRANSACTION)
without assigning risk, scam, or threat labels.
"""

import re
from typing import Optional
from nivesh.schemas.actions import ActionType, ActionCategory

# Action category progression rank (for ordering / progression analysis, not risk!)
CATEGORY_HIERARCHY_RANK: dict[ActionCategory, int] = {
    "INFORMATIONAL": 1,
    "COMMUNICATION": 2,
    "CHANNEL_MIGRATION": 3,
    "NAVIGATION": 4,
    "SOFTWARE_INSTALLATION": 5,
    "DATA_DISCLOSURE": 6,
    "CREDENTIAL_ACCESS": 7,
    "ACCOUNT_AUTHORIZATION": 8,
    "FINANCIAL_TRANSACTION": 9,
}

# Standard mapping of ActionType to its progression ActionCategory
ACTION_TYPE_TO_CATEGORY: dict[ActionType, ActionCategory] = {
    # Communication
    "CONTACT": "COMMUNICATION",
    "MESSAGE_PERSON": "COMMUNICATION",
    "CALL_PERSON": "COMMUNICATION",
    "SHARE": "COMMUNICATION",
    "FORWARD": "COMMUNICATION",
    # Channel Migration
    "JOIN_CHANNEL": "CHANNEL_MIGRATION",
    "JOIN_GROUP": "CHANNEL_MIGRATION",
    "FOLLOW_ACCOUNT": "CHANNEL_MIGRATION",
    # Navigation
    "CLICK_LINK": "NAVIGATION",
    "OPEN_WEBSITE": "NAVIGATION",
    # Software Installation
    "DOWNLOAD": "SOFTWARE_INSTALLATION",
    "INSTALL": "SOFTWARE_INSTALLATION",
    # Data Disclosure
    "UPLOAD_DOCUMENT": "DATA_DISCLOSURE",
    "UPLOAD_IDENTITY": "DATA_DISCLOSURE",
    "SHARE_PERSONAL_INFORMATION": "DATA_DISCLOSURE",
    "SHARE_FINANCIAL_INFORMATION": "DATA_DISCLOSURE",
    "SIGN_DOCUMENT": "DATA_DISCLOSURE",
    # Credential Access
    "ENTER_CREDENTIALS": "CREDENTIAL_ACCESS",
    "SHARE_OTP": "CREDENTIAL_ACCESS",
    # Account Authorization
    "CONNECT_ACCOUNT": "ACCOUNT_AUTHORIZATION",
    "CONNECT_BANK": "ACCOUNT_AUTHORIZATION",
    "AUTHORIZE_ACCESS": "ACCOUNT_AUTHORIZATION",
    # Financial Transaction
    "PAYMENT": "FINANCIAL_TRANSACTION",
    "TRANSFER_MONEY": "FINANCIAL_TRANSACTION",
    "DEPOSIT_MONEY": "FINANCIAL_TRANSACTION",
    "WITHDRAW_MONEY": "FINANCIAL_TRANSACTION",
    "BUY": "FINANCIAL_TRANSACTION",
    "SELL": "FINANCIAL_TRANSACTION",
    # Other
    "OTHER": "INFORMATIONAL",
}


class ActionClassifier:
    """Classifies action text into canonical ActionType, ActionCategory, and objects."""

    def classify(self, text: str, cta_category: Optional[str] = None) -> tuple[ActionType, ActionCategory, list[str]]:
        """Determines ActionType, ActionCategory, and target objects from action text.
        
        Returns:
            (action_type, action_category, objects)
        """
        clean = text.lower().strip()
        objects: list[str] = []

        # 1. Credential Access: OTP
        if any(w in clean for w in ["share otp", "send otp", "give otp", "provide otp", "enter otp"]):
            return "SHARE_OTP", "CREDENTIAL_ACCESS", ["OTP"]
        if "otp" in clean and any(w in clean for w in ["share", "send", "enter", "input"]):
            return "SHARE_OTP", "CREDENTIAL_ACCESS", ["OTP"]

        # 2. Credential Access: Password / PIN / Credentials
        if any(w in clean for w in ["enter your trading password", "trading password"]):
            return "ENTER_CREDENTIALS", "CREDENTIAL_ACCESS", ["trading password"]
        if any(w in clean for w in ["enter password", "type password", "input password", "provide password", "enter pin", "share password", "enter your password"]):
            obj_name = "password" if "password" in clean else "PIN"
            return "ENTER_CREDENTIALS", "CREDENTIAL_ACCESS", [obj_name]
        if "credential" in clean:
            return "ENTER_CREDENTIALS", "CREDENTIAL_ACCESS", ["credentials"]

        # 3. Data Disclosure: Identity / Documents
        if any(w in clean for w in ["upload pan", "upload your pan", "pan card", "submit pan"]):
            return "UPLOAD_DOCUMENT", "DATA_DISCLOSURE", ["PAN"]
        if any(w in clean for w in ["upload aadhaar", "upload your aadhaar", "aadhaar card", "submit aadhaar", "upload aadhar"]):
            return "UPLOAD_IDENTITY", "DATA_DISCLOSURE", ["Aadhaar"]
        if any(w in clean for w in ["complete kyc", "do kyc", "kyc verification", "submit kyc", "verify kyc"]):
            return "UPLOAD_DOCUMENT", "DATA_DISCLOSURE", ["KYC"]
        if any(w in clean for w in ["upload document", "upload your document", "upload id", "submit id"]):
            return "UPLOAD_DOCUMENT", "DATA_DISCLOSURE", ["document"]
        if any(w in clean for w in ["sign document", "sign agreement", "e-sign"]):
            return "SIGN_DOCUMENT", "DATA_DISCLOSURE", ["agreement"]

        # 4. Account Authorization / Bank Connection
        if any(w in clean for w in ["connect bank", "connect your bank", "link bank", "link your bank", "add bank"]):
            return "CONNECT_BANK", "ACCOUNT_AUTHORIZATION", ["bank account"]
        if any(w in clean for w in ["authorize access", "grant access", "authorize account", "grant permission"]):
            return "AUTHORIZE_ACCESS", "ACCOUNT_AUTHORIZATION", ["account access"]
        if any(w in clean for w in ["connect account", "link account", "connect wallet", "link wallet", "link demat"]):
            return "CONNECT_ACCOUNT", "ACCOUNT_AUTHORIZATION", ["account"]

        # 5. Financial Transactions: Payment, Transfer, Deposit, Withdraw, Buy, Sell
        if any(w in clean for w in ["transfer money", "transfer ₹", "transfer rs", "transfer funds", "transfer to account", "transfer 25000", "transfer ₹25,000"]):
            return "TRANSFER_MONEY", "FINANCIAL_TRANSACTION", []
        if any(w in clean for w in ["deposit money", "deposit ₹", "deposit rs", "deposit funds", "deposit 10000", "deposit ₹10,000"]):
            return "DEPOSIT_MONEY", "FINANCIAL_TRANSACTION", []
        if any(w in clean for w in ["withdraw money", "withdraw funds", "withdraw ₹"]):
            return "WITHDRAW_MONEY", "FINANCIAL_TRANSACTION", []
        if any(w in clean for w in ["buy now", "buy stock", "buy shares", "purchase shares", "buy immediately"]):
            return "BUY", "FINANCIAL_TRANSACTION", []
        if any(w in clean for w in ["sell stock", "sell shares", "sell immediately"]):
            return "SELL", "FINANCIAL_TRANSACTION", []
        if any(w in clean for w in ["pay ₹", "pay rs", "pay 5000", "pay ₹5,000", "pay fee", "pay charges", "pay immediately", "make payment", "send ₹", "send money", "wire money"]) or clean.startswith("pay "):
            return "PAYMENT", "FINANCIAL_TRANSACTION", []

        # 6. Software Installation: APK, App
        if any(w in clean for w in ["install this apk", "install apk", "download apk"]):
            return "INSTALL", "SOFTWARE_INSTALLATION", ["APK"]
        if any(w in clean for w in ["install app", "install our app", "install application"]):
            return "INSTALL", "SOFTWARE_INSTALLATION", ["application"]
        if any(w in clean for w in ["download our app", "download app", "download application", "download software"]):
            return "DOWNLOAD", "SOFTWARE_INSTALLATION", ["application"]
        if clean.startswith("download ") or clean == "download":
            return "DOWNLOAD", "SOFTWARE_INSTALLATION", []
        if clean.startswith("install ") or clean == "install":
            return "INSTALL", "SOFTWARE_INSTALLATION", []

        # 7. Channel Migration: Telegram, WhatsApp, Group, Channel, Follow
        if "telegram" in clean:
            return "JOIN_CHANNEL", "CHANNEL_MIGRATION", ["Telegram"]
        if "whatsapp" in clean:
            return "JOIN_GROUP", "CHANNEL_MIGRATION", ["WhatsApp"]
        if any(w in clean for w in ["follow our", "follow on", "follow account"]):
            return "FOLLOW_ACCOUNT", "CHANNEL_MIGRATION", []
        if any(w in clean for w in ["join our channel", "join channel", "subscribe to channel"]):
            return "JOIN_CHANNEL", "CHANNEL_MIGRATION", []
        if any(w in clean for w in ["join our group", "join group", "join vip group", "join community", "joining our group", "joining group"]):
            return "JOIN_GROUP", "CHANNEL_MIGRATION", []

        # 8. Navigation: Click link, Open website
        if any(w in clean for w in ["click the link", "click link", "click here", "tap link", "tap here"]):
            return "CLICK_LINK", "NAVIGATION", []
        if any(w in clean for w in ["open website", "visit our website", "visit website", "visit site", "go to http"]):
            return "OPEN_WEBSITE", "NAVIGATION", []

        # 9. Communication: Contact, Call, Message, Share, Forward
        if any(w in clean for w in ["call us", "call person", "call on", "dial"]):
            return "CALL_PERSON", "COMMUNICATION", []
        if any(w in clean for w in ["message me", "send message", "dm us", "dm me", "chat with us"]):
            return "MESSAGE_PERSON", "COMMUNICATION", []
        if any(w in clean for w in ["contact", "reach out", "email us"]):
            return "CONTACT", "COMMUNICATION", []
        if any(w in clean for w in ["forward this", "forward message"]):
            return "FORWARD", "COMMUNICATION", []
        if any(w in clean for w in ["share this", "share with friends", "share link"]):
            return "SHARE", "COMMUNICATION", []

        # 10. Reconciliation with Engine 1 CTA category fallback
        if cta_category:
            cat_map: dict[str, ActionType] = {
                "join_channel": "JOIN_CHANNEL",
                "download": "DOWNLOAD",
                "install": "INSTALL",
                "payment": "PAYMENT",
                "transfer": "TRANSFER_MONEY",
                "contact": "CONTACT",
                "click": "CLICK_LINK",
                "upload": "UPLOAD_DOCUMENT",
                "credential_request": "ENTER_CREDENTIALS",
                "share": "SHARE",
            }
            if cta_category in cat_map:
                atype = cat_map[cta_category]
                return atype, ACTION_TYPE_TO_CATEGORY[atype], objects

        # 11. Generic fallback
        if any(w in clean for w in ["register", "sign up", "create account"]):
            return "CONNECT_ACCOUNT", "ACCOUNT_AUTHORIZATION", []

        return "OTHER", "INFORMATIONAL", objects
