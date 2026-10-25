"""
Scan session identification: UUID v4 + timestamp.
Used for log correlation and API routes (/list, /reports/{session_id}).

Future (evidence precision / modern IDs): consider RFC 9562 UUID version 7 for session_id
(time-ordered, ms-resolution timestamp in the UUID structure). Does not replace cryptographic
integrity (hashes/signing; see PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY) but aligns identifiers with
current practice and improves sortability. Requires Python/stdlib or small helper when minimum
Python version is confirmed.
"""

import uuid
from datetime import datetime, timezone


def new_session_id() -> str:
    """Return a unique session id: UUID4 and ISO timestamp."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    u = uuid.uuid4().hex[:12]
    return f"{u}_{ts}"
