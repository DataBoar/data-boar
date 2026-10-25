// Synthetic docs only — lab smoke for MongoDB connector (pymongo).

db = db.getSiblingDB("lab_smoke_mongo");
db.lab_people.insertMany([
    {
        nome: "Sintetico Lab Um",
        doc: "123.456.789-09",
        email: "lab1@example.invalid",
        observacao: "Corpus de teste; nao e pessoa real.",
    },
    {
        nome: "Sintetico Lab Dois",
        idade: 9,
        observacao: "Campo idade para heuristica de menor (sintetico).",
    },
]);
