-- Synthetic lab data — MariaDB mirror of postgres seed (same semantic rows).
-- Executed in MARIADB_DATABASE (lab_smoke_my by default).

CREATE TABLE lab_customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name TEXT NOT NULL,
    national_id VARCHAR(32),
    contact_email VARCHAR(255),
    comment_text TEXT
) ENGINE=InnoDB;

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
    id INT AUTO_INCREMENT PRIMARY KEY,
    body TEXT NOT NULL
) ENGINE=InnoDB;

INSERT INTO lab_notes (body) VALUES
('Pedido #LAB-001 — observação: RG 12.345.678-9 é sintético.'),
('Linha só com texto: entrega agendada para depois do feriado.');
