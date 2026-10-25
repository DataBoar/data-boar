"""Legacy: prefer core.detector.SensitivityDetector and connectors.filesystem_connector for new code."""

import re
from typing import List, Dict


def detect_sensitive_data(file_content: str) -> List[Dict]:
    """Detecta dados sensíveis usando regex."""
    sensitive_patterns = [
        r"cpf:\d{11}",  # CPF no Brasil
        r"rg:\d{8}",  # RG no Brasil
        r"email:\w+@\w+\.\w+",  # Emails
        r"credit_card:\d{16}",  # Cartões de crédito
    ]
    results = []

    for pattern in sensitive_patterns:
        matches = re.findall(pattern, file_content)
        for match in matches:
            results.append(
                {
                    "data": match,
                    "pattern": pattern,
                    "sensitivity": "alto",  # ou "medio", "baixo"
                }
            )
    return results
