-- Same semantic content as postgres/02_lab_smoke_linkage.sql (MariaDB syntax).

CREATE TABLE lab_guardians (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name TEXT NOT NULL,
    cpf VARCHAR(32),
    email VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE lab_minors_synthetic (
    id INT AUTO_INCREMENT PRIMARY KEY,
    guardian_id INT NOT NULL,
    nome_aluno TEXT NOT NULL,
    data_nascimento VARCHAR(64) NOT NULL,
    idade INT,
    observacao TEXT,
    CONSTRAINT fk_minors_guardian FOREIGN KEY (guardian_id) REFERENCES lab_guardians (id)
) ENGINE=InnoDB;

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
    id INT AUTO_INCREMENT PRIMARY KEY,
    subscriber_label TEXT,
    phone_e164 VARCHAR(32)
) ENGINE=InnoDB;

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
