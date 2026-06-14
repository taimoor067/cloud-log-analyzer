# Secure Cloud Log Analyzer with MapReduce

## Project Overview

Secure Cloud Log Analyzer is a cloud-based web application developed for the Cloud Computing (CS-508) course project. The system allows administrators to upload server log files, process them using a MapReduce-based analytics engine, and visualize critical system statistics such as HTTP error frequencies and peak traffic hours.

The application demonstrates cloud-native development practices including authentication, secure secrets management, cloud database integration, version control, and automated deployment.

---

## Features

### Secure Authentication

* Administrator login system
* Protected dashboard access
* Session-based authentication

### Log File Upload

* Upload raw `.log` files through a web interface
* Server-side file validation

### MapReduce Processing Engine

The analytics engine follows the MapReduce paradigm:

1. **Split**

   * Large log files are divided into smaller chunks.

2. **Map**

   * Each chunk is processed independently.
   * Intermediate key-value pairs are generated.

3. **Shuffle & Sort**

   * Similar keys are grouped together.

4. **Reduce**

   * Values are aggregated to produce final counts.

### Analytics Dashboard

Displays:

* HTTP 404 Error Count
* HTTP 500 Error Count
* Peak Traffic Hours
* Log Analysis Summary

### Cloud Database Integration

Stores:

* User information
* Upload history
* Analysis results
* Audit records

### Secure Secrets Management

Sensitive credentials are stored using environment variables rather than hardcoded in source code.

---

## Technology Stack

### Backend

* Python
* Flask

### Authentication

* Flask-Login

### Database

* Neon PostgreSQL / Firebase Firestore

### Deployment

* Railway

### Version Control

* GitHub

---

## Project Structure

```text
SecureCloudLogAnalyzer/
│
├── app.py
├── mapreduce.py
├── requirements.txt
├── .gitignore
├── README.md
│
├── templates/
│   ├── login.html
│   ├── upload.html
│   └── dashboard.html
│
├── static/
│
└── uploads/
```

## Installation

### Clone Repository

```bash
git clone <repository-url>
cd SecureCloudLogAnalyzer
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

Windows:

```bash
venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file:

```env
DATABASE_URL=your_database_connection_string
SECRET_KEY=your_secret_key
```

The `.env` file must never be pushed to GitHub.

Add the following to `.gitignore`:

```text
.env
__pycache__/
```

---

## Running the Application

```bash
python app.py
```

Open:

```text
http://localhost:5000
```

---

## Deployment

The application is deployed on Railway and configured for automatic deployment through GitHub integration.

Whenever changes are pushed to the main branch:

1. Railway detects updates.
2. Dependencies are installed automatically.
3. Environment variables are loaded securely.
4. The application is redeployed automatically.

---

## Security Measures

* Authentication-based access control
* Protected dashboard routes
* Environment variable configuration
* Hidden database credentials
* Git version control security practices

---

## Learning Outcomes

This project demonstrates:

* Cloud-based application deployment
* Parallel processing using MapReduce
* Secure authentication mechanisms
* Cloud database integration
* Environment variable management
* Continuous deployment workflows
* GitHub version control practices

---

## Course Information

**Course:** Cloud Computing (CS-508)

**Project Title:** Secure Cloud Log Analyzer with MapReduce

**Deployment Platform:** Railway

**Repository:** GitHub
