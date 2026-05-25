"""Licensing errors raised when enforcement blocks a scan or tier-gated feature."""


class LicenseBlockedError(RuntimeError):
    """Raised when licensing enforcement blocks starting an audit or digest session."""

    def __init__(self, state: str, message: str) -> None:
        self.state = state
        super().__init__(message)


class FeatureTierBlockedError(RuntimeError):
    """Raised when the runtime tier does not include a Pro/Enterprise feature."""

    def __init__(
        self,
        feature: str,
        reason: str,
        *,
        required_tier: str = "",
        current_tier: str = "",
    ) -> None:
        self.feature = feature
        self.reason = reason
        self.required_tier = required_tier
        self.current_tier = current_tier
        super().__init__(reason or f"Feature '{feature}' is not available for this tier.")
