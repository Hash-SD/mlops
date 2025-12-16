-- Schema untuk Sistem AI Berbasis Teks
-- Database tables untuk menyimpan user inputs dan predictions

-- Table untuk menyimpan input teks dari pengguna
CREATE TABLE IF NOT EXISTS users_inputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    text_input TEXT NOT NULL,
    user_consent BOOLEAN DEFAULT 0,
    anonymized BOOLEAN DEFAULT 0
);

-- Table untuk menyimpan hasil prediksi dengan feedback
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_id INTEGER NOT NULL,
    model_version VARCHAR(10) NOT NULL,
    prediction VARCHAR(100) NOT NULL,
    confidence REAL NOT NULL,
    latency REAL NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- Feedback columns (nullable - user tidak wajib mengisi)
    feedback_correct BOOLEAN DEFAULT NULL,
    feedback_timestamp DATETIME DEFAULT NULL,
    -- Flag untuk training data
    used_for_training BOOLEAN DEFAULT 0,
    training_split VARCHAR(10) DEFAULT NULL,
    FOREIGN KEY (input_id) REFERENCES users_inputs(id)
);

-- Indexes untuk optimasi query performance
CREATE INDEX IF NOT EXISTS idx_predictions_model_version ON predictions(model_version);
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp);
CREATE INDEX IF NOT EXISTS idx_predictions_feedback ON predictions(feedback_correct);
CREATE INDEX IF NOT EXISTS idx_predictions_training ON predictions(used_for_training);
CREATE INDEX IF NOT EXISTS idx_users_inputs_consent ON users_inputs(user_consent);
CREATE INDEX IF NOT EXISTS idx_users_inputs_timestamp ON users_inputs(timestamp);
