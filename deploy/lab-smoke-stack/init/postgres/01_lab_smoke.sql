-- Synthetic lab data only — obvious fakes and edge cases for detector tuning (FP/FN experiments).
-- Do not use real personal data.

CREATE TABLE lab_customers (
    id serial PRIMARY KEY,
    full_name text NOT NULL,
    national_id text,
    contact_email text,
    comment_text text
);

COMMENT ON TABLE lab_customers IS 'Lab smoke: synthetic PII-shaped strings for Data Boar scans.';

-- Happy path (format used elsewhere in repo tests / troubleshooting matrix)
INSERT INTO lab_customers (full_name, national_id, contact_email, comment_text) VALUES
(
    'Cliente Sintético Alfa',
    '123.456.789-09',
    'audit.synthetic@example.invalid',
    'CPF formato válido de teste; email descartável.'
),
(
    'Cliente Beta Borderline',
    '111.444.777-35',
    'borderline.case@example.invalid',
    'Sequência numérica estilo documento — verificar confiança vs FP.'
),
(
    'Cliente Gama Falso Positivo',
    '000.000.000-00',
    'fp.candidate@example.invalid',
    'Padrão óbvio de zeros — pode ser rejeitado por validação de dígitos.'
),
(
    'Inócuo Quatro',
    NULL,
    'noreply@company.invalid',
    'Sem national_id; apenas texto operacional SKU-99999-X e telefone falso (21) 99999-0000.'
);

CREATE TABLE lab_notes (
    id serial PRIMARY KEY,
    body text NOT NULL
);

INSERT INTO lab_notes (body) VALUES
('Pedido #LAB-001 — observação: RG 12.345.678-9 é sintético.'),
('Linha só com texto: entrega agendada para depois do feriado.');
