CREATE TABLE IF NOT EXISTS carriers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trucks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    truck_code VARCHAR(10) NOT NULL UNIQUE,
    tag_epc VARCHAR(24) NOT NULL UNIQUE,
    carrier_id INT NOT NULL,
    active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_trucks_carrier FOREIGN KEY (carrier_id) REFERENCES carriers (id)
);

CREATE TABLE IF NOT EXISTS locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    location_type VARCHAR(10) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_locations_type CHECK (location_type IN ('gate', 'dock'))
);

CREATE TABLE IF NOT EXISTS scan_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    truck_id INT NOT NULL,
    location_id INT NOT NULL,
    reader_id VARCHAR(30) NOT NULL,
    scanned_at DATETIME NOT NULL,
    rssi_dbm SMALLINT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_scans_truck FOREIGN KEY (truck_id) REFERENCES trucks (id),
    CONSTRAINT fk_scans_location FOREIGN KEY (location_id) REFERENCES locations (id),
    INDEX idx_scans_truck_time (truck_id, scanned_at)
);

CREATE TABLE IF NOT EXISTS deliveries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    delivery_code VARCHAR(20) NOT NULL UNIQUE,
    truck_id INT NOT NULL,
    scheduled_arrival DATETIME NULL,
    gate_in_at DATETIME NOT NULL,
    dock_location_id INT NULL,
    dock_arrival_at DATETIME NULL,
    gate_out_at DATETIME NULL,
    status VARCHAR(10) NOT NULL DEFAULT 'open',
    exception_note VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_deliveries_truck FOREIGN KEY (truck_id) REFERENCES trucks (id),
    CONSTRAINT fk_deliveries_dock FOREIGN KEY (dock_location_id) REFERENCES locations (id),
    CONSTRAINT chk_deliveries_status CHECK (status IN ('open', 'closed')),
    CONSTRAINT chk_deliveries_dock_time CHECK (dock_arrival_at IS NULL OR dock_arrival_at >= gate_in_at),
    CONSTRAINT chk_deliveries_out_time CHECK (gate_out_at IS NULL OR gate_out_at >= gate_in_at),
    INDEX idx_deliveries_status (status),
    INDEX idx_deliveries_truck_time (truck_id, gate_in_at)
);