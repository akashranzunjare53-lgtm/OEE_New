CREATE DATABASE IF NOT EXISTS oee_db;
USE oee_db;

CREATE TABLE IF NOT EXISTS predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    machine_age DOUBLE NOT NULL,
    oee_lag_1 DOUBLE NOT NULL,
    avail_hrs_lag_1 DOUBLE NOT NULL,
    mc_running_hrs_lag_1 DOUBLE NOT NULL,
    total_dt_lag_1 DOUBLE NOT NULL,
    prod_qty_lag_1 DOUBLE NOT NULL,
    rej_qty_lag_1 DOUBLE NOT NULL,
    maintenance_flag_lag_1 TINYINT NOT NULL,
    predicted_oee DOUBLE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);