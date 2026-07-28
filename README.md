# Brute Force Attack Detection Simulator

## Overview

The Brute Force Attack Detection Simulator is a cybersecurity project developed to demonstrate how brute force attacks can be detected and prevented in an authorized local testing environment. The project consists of two Flask-based applications running in **Kali Linux**:

- **Velora E-Commerce Application** – Acts as the target application with a secure login system.
- **Brute Force Attack Detection Simulator** – Simulates controlled brute force login attempts against the authorized local Velora application.

The simulator monitors failed login attempts, demonstrates account lockout after the configured threshold, and generates attack reports for educational purposes.

> **Note:** This project is intended only for authorized cybersecurity demonstrations and learning. It must never be used against systems without permission.

---

# Features

- Secure login authentication
- Controlled brute force attack simulation
- Sequential failed login attempts
- Failed login detection
- Automatic account lockout
- Live simulation console
- Attack event monitoring
- PDF report generation
- Localhost-based testing
- Educational cybersecurity demonstration

---

# Technologies Used

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript
- Git
- GitHub
- Kali Linux

---

# System Requirements

- Kali Linux
- Python 3.x
- Flask
- SQLite
- Modern Web Browser
- Git

---

# Project Structure

```
Brute-Force-Attack-Detection-Simulator/
│
├── app.py
├── simulator.py
├── requirements.txt
├── README.md
│
├── templates/
│   └── index.html
│
├── static/
│   ├── css/
│   └── js/
│
└── reports/
```

---

# Installation

Clone the repository:

```bash
git clone https://github.com/JaspreetKour28/brute-force-attack-detection-simulator.git
```

Move into the project folder:

```bash
cd brute-force-attack-detection-simulator
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# How to Run

### Step 1

Run the **Velora E-Commerce Application** in **Kali Linux**.

### Step 2

Run the **Brute Force Attack Detection Simulator** in **Kali Linux**.

### Step 3

Open the locally hosted Velora login page.

### Step 4

Open the Brute Force Attack Detection Simulator.

### Step 5

Enter the authorized target application details and start the simulation.

### Step 6

Observe:

- Failed login attempts
- Live simulation console
- Account lock after the configured threshold
- Attack detection
- Generated PDF report

---

# Project Workflow

```
Start Velora Application (Kali Linux)
            │
            ▼
Start Brute Force Simulator (Kali Linux)
            │
            ▼
Configure Target Application
            │
            ▼
Start Simulation
            │
            ▼
Attempt 1
            │
            ▼
Attempt 2
            │
            ▼
Attempt 3
            │
            ▼
Account Locked
            │
            ▼
Attack Detected
            │
            ▼
Generate PDF Report
            │
            ▼
Simulation Completed
```

---

# Expected Output

- Three controlled failed login attempts
- Detection of repeated failed logins
- Automatic account lock after the configured threshold
- Live attack monitoring
- PDF report generation
- Successful demonstration of brute force attack detection

---

# Security Notice

This project is developed **only for educational purposes and authorized cybersecurity demonstrations**.

Both the **Velora E-Commerce Application** and the **Brute Force Attack Detection Simulator** are executed locally in **Kali Linux**. The simulator is designed to test only the authorized local application and must not be used against systems without explicit permission.

---

# Author

**Jaspreet Kour**

B.Tech – Computer Science Engineering (Cloud Technology)

Cybersecurity Project

---

# Repository

https://github.com/JaspreetKour28/brute-force-attack-detection-simulator
