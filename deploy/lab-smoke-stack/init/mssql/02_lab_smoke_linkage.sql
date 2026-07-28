-- Cross-table linkage, shared-phone/email patterns, and minor-adjacent heuristics (lab only).
-- All identifiers are fictional test fixtures — not real people.

USE lab_smoke_mssql;
GO

CREATE TABLE lab_guardians (
    id INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
    full_name NVARCHAR(MAX) NOT NULL,
    cpf NVARCHAR(32) NULL,
    email NVARCHAR(255) NULL
);
GO

CREATE TABLE lab_minors_synthetic (
    id INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
    guardian_id INT NOT NULL,
    nome_aluno NVARCHAR(MAX) NOT NULL,
    data_nascimento NVARCHAR(64) NOT NULL,
    idade INT NULL,
    observacao NVARCHAR(MAX) NULL,
    CONSTRAINT fk_minors_guardian FOREIGN KEY (guardian_id) REFERENCES lab_guardians (id)
);
GO

INSERT INTO lab_guardians (full_name, cpf, email) VALUES
(
    N'Responsavel Sintetico Um',
    N'529.982.247-25',
    N'guardian.one@example.invalid'
),
(
    N'Mesmo Email Que Cliente Alfa',
    N'987.654.321-00',
    N'audit.synthetic@example.invalid'
);
GO

INSERT INTO lab_minors_synthetic (guardian_id, nome_aluno, data_nascimento, idade, observacao) VALUES
(
    1,
    N'Aluno Sintetico Menor A',
    N'15/06/2015',
    10,
    N'Fictitious school row; guardian CPF in lab_guardians.'
);
GO

CREATE TABLE lab_phone_directory (
    id INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
    subscriber_label NVARCHAR(MAX) NULL,
    phone_e164 NVARCHAR(32) NULL
);
GO

INSERT INTO lab_phone_directory (subscriber_label, phone_e164) VALUES
(N'Contato lab delta', N'+5511999990001');
GO

INSERT INTO lab_customers (full_name, national_id, contact_email, comment_text) VALUES
(
    N'Cliente Delta Linkagem',
    N'131.000.000-07',
    N'link.test@example.invalid',
    N'Telefone compartilhado para teste de correlacao: +5511999990001 (ver lab_phone_directory).'
);
GO

INSERT INTO lab_notes (body) VALUES
(N'Ticket LAB-LINK: retornar ligacao para +5511999990001 (duplicado proposital com lab_customers Delta).');
GO
