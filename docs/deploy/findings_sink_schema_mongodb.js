// Data Boar findings sink — MongoDB collections (#552, Enterprise)
// Run against the customer database (mongosh). Unique indexes match the SQL
// UNIQUE key. Do not store sample_content unless Legal signed off (LGPD Art. 46).

db.createCollection("data_boar_sessions");
db.data_boar_sessions.createIndex({ session_id: 1 }, { unique: true, name: "uq_data_boar_session_id" });

db.createCollection("data_boar_findings");
db.data_boar_findings.createIndex(
  {
    session_id: 1,
    source_type: 1,
    target_name: 1,
    table_name: 1,
    column_name: 1,
    file_path: 1,
  },
  { unique: true, name: "uq_data_boar_finding" }
);
