"""Policy & Intervention Engine configuration.

Centralized constants, policy versioning, and default intervention parameters.
"""

POLICY_VERSION: str = "8.0.0"

DEFAULT_COOLDOWN_PAUSE_SECONDS: int = 30
DEFAULT_COOLDOWN_BLOCK_SECONDS: int = 300

# High-impact action classifications requiring heightened intervention sensitivity
HIGH_IMPACT_ACTION_TYPES: set[str] = {
    # Engine 3 Action Types
    "PAYMENT",
    "TRANSFER_MONEY",
    "DEPOSIT_MONEY",
    "DOWNLOAD",
    "INSTALL",
    "ENTER_CREDENTIALS",
    "SHARE_OTP",
    "CONNECT_ACCOUNT",
    "CONNECT_BANK",
    "AUTHORIZE_ACCESS",
    # Engine 3 Action Categories
    "FINANCIAL_TRANSACTION",
    "SOFTWARE_INSTALLATION",
    "CREDENTIAL_ACCESS",
    "ACCOUNT_AUTHORIZATION",
    # Threat / Policy equivalents
    "FINANCIAL_TRANSFER",
    "PAYMENT_REQUEST",
}

# Irreversible financial actions
IRREVERSIBLE_ACTION_TYPES: set[str] = {
    "PAYMENT",
    "TRANSFER_MONEY",
    "DEPOSIT_MONEY",
    "FINANCIAL_TRANSACTION",
    "FINANCIAL_TRANSFER",
    "PAYMENT_REQUEST",
    "ACCOUNT_ACCESS",
}
