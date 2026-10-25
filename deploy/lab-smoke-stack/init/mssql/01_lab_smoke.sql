-- Synthetic lab data only — obvious fakes and edge cases for detector tuning (FP/FN experiments).
-- Do not use real personal data.

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'lab_smoke_mssql')
BEGIN
    CREATE DATABASE lab_smoke_mssql;
END;
GO

USE lab_smoke_mssql;
GO

CREATE TABLE lab_customers (
    id INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
    full_name NVARCHAR(MAX) NOT NULL,
    national_id NVARCHAR(32) NULL,
    contact_email NVARCHAR(255) NULL,
    comment_text NVARCHAR(MAX) NULL
);
GO

INSERT INTO lab_customers (full_name, national_id, contact_email, comment_text) VALUES
(
    N'Cliente Sintético Alfa',
    N'123.456.789-09',
    N'audit.synthetic@example.invalid',
    N'CPF formato válido de teste; email descartável.'
),
(
    N'Cliente Beta Borderline',
    N'111.444.777-35',
    N'borderline.case@example.invalid',
    N'Sequência numérica estilo documento — verificar confiança vs FP.'
),
(
    N'Cliente Gama Falso Positivo',
    N'000.000.000-00',
    N'fp.candidate@example.invalid',
    N'Padrão óbvio de zeros — pode ser rejeitado por validação de dígitos.'
),
(
    N'Inócuo Quatro',
    NULL,
    N'noreply@company.invalid',
    N'Sem national_id; apenas texto operacional SKU-99999-X e telefone falso (21) 99999-0000.'
);
GO

CREATE TABLE lab_notes (
    id INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
    body NVARCHAR(MAX) NOT NULL
);
GO

INSERT INTO lab_notes (body) VALUES
(N'Pedido #LAB-001 — observação: RG 12.345.678-9 é sintético.'),
(N'Linha só com texto: entrega agendada para depois do feriado.');
GO
