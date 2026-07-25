-- ============================================================
-- UmugandaSync - Community Work Management System
-- Database: umuganda_sync
-- Owner: Rebecca
--
-- Run:  mysql -u root < database.sql
-- ============================================================

DROP DATABASE IF EXISTS umuganda_sync;
CREATE DATABASE umuganda_sync
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE umuganda_sync;

-- ------------------------------------------------------------
-- Admins — system login accounts
-- ------------------------------------------------------------
CREATE TABLE admins (
    admin_id    INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(50)  NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    full_name   VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Members — community participants
-- ------------------------------------------------------------
CREATE TABLE members (
    member_id       INT AUTO_INCREMENT PRIMARY KEY,
    national_id     VARCHAR(20)  NULL UNIQUE,
    email           VARCHAR(100) NULL,
    first_name      VARCHAR(50)  NOT NULL,
    last_name       VARCHAR(50)  NOT NULL,
    phone           VARCHAR(20)  NOT NULL UNIQUE,
    village         VARCHAR(50)  NOT NULL,
    cell_name       VARCHAR(50)  NOT NULL,
    gender          VARCHAR(10)  NOT NULL,
    date_registered DATE         NOT NULL,
    status          VARCHAR(10)  NOT NULL DEFAULT 'Active',
    CONSTRAINT chk_member_status CHECK (status IN ('Active', 'Inactive')),
    CONSTRAINT chk_member_gender CHECK (gender IN ('Male', 'Female', 'Other'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_members_national_id ON members(national_id);
CREATE INDEX idx_members_phone       ON members(phone);
CREATE INDEX idx_members_status      ON members(status);
CREATE INDEX idx_members_village     ON members(village);
CREATE INDEX idx_members_name        ON members(last_name, first_name);

-- ------------------------------------------------------------
-- Attendance — one row per member per Umuganda date
-- ------------------------------------------------------------
CREATE TABLE attendance (
    attendance_id   INT AUTO_INCREMENT PRIMARY KEY,
    member_id       INT          NOT NULL,
    attendance_date DATE         NOT NULL,
    status          VARCHAR(20)  NOT NULL,
    remarks         VARCHAR(255) NULL,
    FOREIGN KEY (member_id) REFERENCES members(member_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE (member_id, attendance_date),
    CONSTRAINT chk_attendance_status CHECK (
        status IN ('Present', 'Late', 'Absent', 'Excused')
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_attendance_date         ON attendance(attendance_date);
CREATE INDEX idx_attendance_status       ON attendance(status);
CREATE INDEX idx_attendance_member_date  ON attendance(member_id, attendance_date);

-- ------------------------------------------------------------
-- Projects — community work initiatives
-- ------------------------------------------------------------
CREATE TABLE projects (
    project_id          INT AUTO_INCREMENT PRIMARY KEY,
    project_name        VARCHAR(100) NOT NULL,
    description         TEXT         NULL,
    location            VARCHAR(100) NOT NULL,
    leader_member_id    INT          NULL,
    start_date          DATE         NOT NULL,
    expected_end_date   DATE         NOT NULL,
    status              VARCHAR(20)  NOT NULL DEFAULT 'Pending',
    percent_complete    INT          NOT NULL DEFAULT 0,
    FOREIGN KEY (leader_member_id) REFERENCES members(member_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_project_status CHECK (
        status IN ('Pending', 'Ongoing', 'Completed', 'Cancelled')
    ),
    CONSTRAINT chk_project_percent CHECK (
        percent_complete BETWEEN 0 AND 100
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_projects_status   ON projects(status);
CREATE INDEX idx_projects_leader   ON projects(leader_member_id);
CREATE INDEX idx_projects_end_date ON projects(expected_end_date);

-- ------------------------------------------------------------
-- Tools — shared community inventory
-- ------------------------------------------------------------
CREATE TABLE tools (
    tool_id             INT AUTO_INCREMENT PRIMARY KEY,
    tool_name           VARCHAR(100) NOT NULL,
    category            VARCHAR(50)  NOT NULL,
    total_quantity      INT          NOT NULL,
    available_quantity  INT          NOT NULL,
    condition_status    VARCHAR(20)  NOT NULL DEFAULT 'Good',
    low_stock_limit     INT          NOT NULL DEFAULT 2,
    CONSTRAINT chk_tool_quantities CHECK (
        available_quantity BETWEEN 0 AND total_quantity
    ),
    CONSTRAINT chk_tool_condition CHECK (
        condition_status IN ('Good', 'Needs Repair', 'Broken')
    ),
    CONSTRAINT chk_tool_low_stock CHECK (low_stock_limit >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_tools_condition ON tools(condition_status);
CREATE INDEX idx_tools_category  ON tools(category);

-- ------------------------------------------------------------
-- Tool borrows — borrow / return history
-- ------------------------------------------------------------
CREATE TABLE tool_borrows (
    borrow_id    INT AUTO_INCREMENT PRIMARY KEY,
    tool_id      INT          NOT NULL,
    member_id    INT          NOT NULL,
    quantity     INT          NOT NULL,
    borrow_date  DATE         NOT NULL,
    return_date  DATE         NULL,
    status       VARCHAR(20)  NOT NULL DEFAULT 'Borrowed',
    FOREIGN KEY (tool_id)   REFERENCES tools(tool_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (member_id) REFERENCES members(member_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_borrow_status CHECK (
        status IN ('Borrowed', 'Returned')
    ),
    CONSTRAINT chk_borrow_quantity CHECK (quantity > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_borrows_status ON tool_borrows(status);
CREATE INDEX idx_borrows_tool   ON tool_borrows(tool_id);
CREATE INDEX idx_borrows_member ON tool_borrows(member_id);

-- ============================================================
-- SAMPLE DATA
-- ============================================================

INSERT INTO admins (username, password, full_name) VALUES
('admin', 'admin123', 'Umudugudu Leader'),
('secretary', 'secret123', 'Cell Secretary');

INSERT INTO members (national_id, first_name, last_name, phone, village, cell_name, gender, date_registered, status) VALUES
('1199780123456789', 'Jean',     'Uwimana',   '0788000001', 'Kagugu',  'Nyarugunga', 'Male',   '2026-01-10', 'Active'),
('1199880123456790', 'Marie',    'Mukamana',  '0788000002', 'Kagugu',  'Nyarugunga', 'Female', '2026-01-12', 'Active'),
('1199680123456791', 'Eric',     'Niyonzima', '0788000003', 'Kacyiru', 'Kimironko',  'Male',   '2026-01-15', 'Active'),
('1199580123456792', 'Claudine', 'Ingabire',  '0788000004', 'Kacyiru', 'Kimironko',  'Female', '2026-02-01', 'Active'),
('1199480123456793', 'Patrick',  'Habimana',  '0788000005', 'Remera',  'Gisozi',     'Male',   '2026-02-05', 'Inactive'),
('1199380123456794', 'Grace',    'Uwase',     '0788000006', 'Remera',  'Gisozi',     'Female', '2026-02-10', 'Active'),
('1199280123456795', 'David',    'Mugisha',   '0788000007', 'Kagugu',  'Nyarugunga', 'Male',   '2026-02-15', 'Active'),
('1199180123456796', 'Alice',    'Iradukunda','0788000008', 'Kacyiru', 'Kimironko',  'Female', '2026-03-01', 'Active');

INSERT INTO attendance (member_id, attendance_date, status, remarks) VALUES
(1, '2026-03-28', 'Present', 'Umuganda March 2026 — Road cleaning and pothole filling'),
(2, '2026-03-28', 'Present', 'Umuganda March 2026 — Road cleaning and pothole filling'),
(3, '2026-03-28', 'Absent',  'Umuganda March 2026 — Road cleaning and pothole filling | Absent'),
(4, '2026-03-28', 'Late',    'Umuganda March 2026 — Road cleaning and pothole filling | Arrived late'),
(6, '2026-03-28', 'Present', 'Umuganda March 2026 — Road cleaning and pothole filling'),
(7, '2026-03-28', 'Excused', 'Umuganda March 2026 — Road cleaning and pothole filling | Excused absence'),
(8, '2026-03-28', 'Present', 'Umuganda March 2026 — Road cleaning and pothole filling'),
(1, '2026-04-25', 'Present', 'Umuganda April 2026 — Drainage clearing before rain season'),
(2, '2026-04-25', 'Absent',  'Umuganda April 2026 — Drainage clearing before rain season | Absent'),
(3, '2026-04-25', 'Absent',  'Umuganda April 2026 — Drainage clearing before rain season | Absent'),
(4, '2026-04-25', 'Present', 'Umuganda April 2026 — Drainage clearing before rain season'),
(6, '2026-04-25', 'Present', 'Umuganda April 2026 — Drainage clearing before rain season'),
(7, '2026-04-25', 'Present', 'Umuganda April 2026 — Drainage clearing before rain season'),
(8, '2026-04-25', 'Late',    'Umuganda April 2026 — Drainage clearing before rain season | Arrived late'),
(1, '2026-05-30', 'Present', 'Umuganda May 2026 — Tree planting around the village'),
(2, '2026-05-30', 'Present', 'Umuganda May 2026 — Tree planting around the village'),
(3, '2026-05-30', 'Absent',  'Umuganda May 2026 — Tree planting around the village | Absent'),
(4, '2026-05-30', 'Present', 'Umuganda May 2026 — Tree planting around the village'),
(6, '2026-05-30', 'Present', 'Umuganda May 2026 — Tree planting around the village'),
(7, '2026-05-30', 'Absent',  'Umuganda May 2026 — Tree planting around the village | Absent'),
(8, '2026-05-30', 'Present', 'Umuganda May 2026 — Tree planting around the village'),
(1, '2026-06-27', 'Present', 'Umuganda June 2026 — Public water point cleaning'),
(2, '2026-06-27', 'Present', 'Umuganda June 2026 — Public water point cleaning'),
(4, '2026-06-27', 'Present', 'Umuganda June 2026 — Public water point cleaning'),
(6, '2026-06-27', 'Present', 'Umuganda June 2026 — Public water point cleaning'),
(8, '2026-06-27', 'Present', 'Umuganda June 2026 — Public water point cleaning');

INSERT INTO projects (project_name, description, location, leader_member_id, start_date, expected_end_date, status, percent_complete) VALUES
('Road Repair - Kagugu',     'Fix potholes on main village road',  'Kagugu Main Road', 1, '2026-05-01', '2026-06-30', 'Ongoing',   60),
('Drainage Cleaning',        'Clean drainage before rainy season', 'Kacyiru Sector',   3, '2026-06-01', '2026-07-15', 'Ongoing',   40),
('Community Garden',         'Plant vegetables for vulnerable families', 'Remera Plot B', 6, '2026-04-01', '2026-05-20', 'Completed', 100),
('School Fence Repair',      'Repair broken fence at primary school', 'Gisozi Primary', 2, '2026-03-01', '2026-04-01', 'Cancelled', 10),
('Water Point Upgrade',      'Improve public water tap access',    'Nyarugunga Cell',  4, '2026-06-10', '2026-07-01', 'Pending',   0);

INSERT INTO tools (tool_name, category, total_quantity, available_quantity, condition_status, low_stock_limit) VALUES
('Hoe',         'Farming',      20, 15, 'Good',          5),
('Spade',       'Farming',      12,  2, 'Good',          3),
('Wheelbarrow', 'Transport',     5,  1, 'Needs Repair',  2),
('Machete',     'Cutting',      10,  8, 'Good',          3),
('Pickaxe',     'Construction',  6,  0, 'Broken',        2),
('Gloves Pair', 'Safety',       30,  4, 'Good',          5);

INSERT INTO tool_borrows (tool_id, member_id, quantity, borrow_date, return_date, status) VALUES
(1, 1, 2, '2026-05-30', NULL,           'Borrowed'),
(2, 3, 1, '2026-04-25', '2026-05-30',   'Returned'),
(4, 7, 1, '2026-06-27', NULL,           'Borrowed');

SELECT 'UmugandaSync database created successfully!' AS message;
