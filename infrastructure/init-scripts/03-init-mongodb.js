// MongoDB initialization for document storage

// Switch to stratum database
db = db.getSiblingDB('stratum_documents');

// Create collections
db.createCollection("reports");
db.createCollection("configurations");
db.createCollection("ml_models");
db.createCollection("audit_logs");

// Create indexes
db.reports.createIndex({ "created_at": -1 });
db.reports.createIndex({ "report_type": 1, "created_at": -1 });

db.configurations.createIndex({ "service_name": 1 });
db.configurations.createIndex({ "version": -1 });

db.ml_models.createIndex({ "model_name": 1, "version": -1 });
db.ml_models.createIndex({ "created_at": -1 });

db.audit_logs.createIndex({ "timestamp": -1 });
db.audit_logs.createIndex({ "user_id": 1, "timestamp": -1 });
db.audit_logs.createIndex({ "action_type": 1 });

// Insert sample configuration
db.configurations.insertOne({
    "service_name": "data-ingestion",
    "version": "1.0.0",
    "config": {
        "buffer_size": 1000,
        "flush_interval": 5,
        "validation_rules": {
            "load_max": 1.5,
            "temperature_range": [-50, 150]
        }
    },
    "created_at": new Date()
});

// Insert sample report template
db.reports.insertOne({
    "report_type": "daily_summary",
    "template_version": "1.0",
    "sections": [
        "infrastructure_health",
        "critical_alerts",
        "simulation_results",
        "policy_recommendations"
    ],
    "created_at": new Date()
});

print("MongoDB initialization complete!");
