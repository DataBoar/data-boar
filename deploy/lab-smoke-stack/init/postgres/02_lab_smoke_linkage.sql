-- Cross-table linkage, shared-phone/email patterns, and minor-adjacent heuristics (lab only).
-- All identifiers are fictional test fixtures — not real people.

CREATE TABLE lab_guardians (
    id serial PRIMARY KEY,
    full_name text NOT NULL,
    cpf text,
    email text
);

CREATE TABLE lab_minors_synthetic (
    id serial PRIMARY KEY,
    guardian_id int REFERENCES lab_guardians (id),
    nome_aluno text NOT NULL,
    data_nascimento text NOT NULL,
    idade int,
    observacao text
);

COMMENT ON TABLE lab_minors_synthetic IS 'DOB/idade column names exercise DOB_POSSIBLE_MINOR heuristics; rows are synthetic.';

INSERT INTO lab_guardians (full_name, cpf, email) VALUES
(
    'Responsavel Sintetico Um',
    '529.982.247-25',
    'guardian.one@example.invalid'
),
(
    'Mesmo Email Que Cliente Alfa',
    '987.654.321-00',
    'audit.synthetic@example.invalid'
);

INSERT INTO lab_minors_synthetic (guardian_id, nome_aluno, data_nascimento, idade, observacao) VALUES
(
    1,
    'Aluno Sintetico Menor A',
    '15/06/2015',
    10,
    'Fictitious school row; guardian CPF in lab_guardians.'
);

CREATE TABLE lab_phone_directory (
    id serial PRIMARY KEY,
    subscriber_label text,
    phone_e164 text
);

INSERT INTO lab_phone_directory (subscriber_label, phone_e164) VALUES
('Contato lab delta', '+5511999990001');

INSERT INTO lab_customers (full_name, national_id, contact_email, comment_text) VALUES
(
    'Cliente Delta Linkagem',
    '131.000.000-07',
    'link.test@example.invalid',
    'Telefone compartilhado para teste de correlacao: +5511999990001 (ver lab_phone_directory).'
);

INSERT INTO lab_notes (body) VALUES
('Ticket LAB-LINK: retornar ligacao para +5511999990001 (duplicado proposital com lab_customers Delta).');
