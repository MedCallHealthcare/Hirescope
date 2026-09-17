# HireScope – MedCall Job Scraper

HireScope is a job scraping and data processing tool used to collect, filter, organize, analyze, and export healthcare job postings.

The tool is mainly used for scraping job data from sources such as **Indeed** and **ZipRecruiter**, then processing the results through filtering, deduplication, categorization, scoring, and export.

---

## Features

- Job scraping
- Search by job title or keyword
- Location-based search
- Positive keyword filtering
- Negative keyword filtering
- Duplicate removal
- Job categorization
- Facility type classification
- Priority scoring
- Analytics summary
- Export to Excel / CSV
- SharePoint export
- Scraping logs
- Job result review

---

# Requirements

Before setting up HireScope, make sure the following are installed:

- Git
- Python 3.x
- Visual Studio Code
- Internet connection
- Access to the HireScope GitHub repository
- Required credentials and environment variables

You can verify Git and Python using:

```bash
git --version
python --version
```

---

# How to Clone HireScope from GitHub

## 1. Copy the Repository Link

Go to the HireScope GitHub repository.

Click:

**Code → HTTPS → Copy Repository URL**

Example:

```text
https://github.com/USERNAME/HireScope.git
```

---

## 2. Open Command Prompt or Terminal

Open:

- Command Prompt
- PowerShell
- VS Code Terminal

Go to the folder where you want to save HireScope.

Example:

```bash
cd C:\Users\YOUR_USERNAME\Documents
```

---

## 3. Clone the Repository

Run:

```bash
git clone https://github.com/USERNAME/HireScope.git
```

Replace the link with the actual HireScope GitHub repository link.

After cloning is complete, enter the project folder:

```bash
cd HireScope
```

---

## 4. Open the Project in Visual Studio Code

Run:

```bash
code .
```

Or manually open the HireScope folder in Visual Studio Code.

---

# Setup

## 1. Create a Virtual Environment

Run:

```bash
python -m venv venv
```

---

## 2. Activate the Virtual Environment

### Command Prompt

```bash
venv\Scripts\activate
```

### PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

When activated, the terminal should look similar to:

```text
(venv) C:\...\HireScope>
```

---

## 3. Install Required Packages

Run:

```bash
pip install -r requirements.txt
```

Wait until all required Python packages are installed.

---

# Environment Configuration

HireScope may require credentials, API keys, SharePoint settings, or other configuration values.

These values are stored inside the:

```text
.env
```

file.

If an `.env.example` file is included, create a copy and rename it to:

```text
.env
```

Then enter the required configuration values.

Example:

```env
USERNAME=your_username
PASSWORD=your_password
API_KEY=your_api_key
```

> Do not upload passwords, API keys, access tokens, or other private credentials to GitHub.

---

# How to Run HireScope

Every time you want to run the application:

### 1. Open the project folder

```bash
cd HireScope
```

### 2. Activate the virtual environment

```bash
venv\Scripts\activate
```

### 3. Start HireScope

```bash
python main.py
```

The HireScope application should open.

---

# Basic Scraping Process

Once HireScope is running:

1. Open the **Scraping Tool**
2. Select the job source
3. Enter the job title or search term
4. Enter the target location
5. Add include keywords if needed
6. Add exclude keywords if needed
7. Configure the scraping settings
8. Start the scraper
9. Monitor the scraping logs
10. Review the results
11. Check the analytics summary
12. Export the final data

---

# Analytics Overview

After scraping, HireScope displays a summary of the collected data.

This may include:

- **Total Jobs** – total job postings collected
- **Companies** – total unique companies found
- **Keywords** – number of search keywords used
- **Duplicates Removed** – duplicate job postings removed
- **Positive Keyword Matches** – jobs matching positive keywords
- **Job Demand** – summary of job title demand

HireScope also displays analytics such as:

- Top Companies
- Top Job Titles
- Job Demand

---

# HireScope Data Flow

```text
Search Configuration
        ↓
Job Scraping
        ↓
Raw Job Data
        ↓
Data Normalization
        ↓
Positive Keyword Filtering
        ↓
Negative Keyword Filtering
        ↓
Duplicate Removal
        ↓
Job Categorization
        ↓
Facility Type Classification
        ↓
Priority Scoring
        ↓
Analytics Review
        ↓
Export
        ↓
SharePoint / Excel
```

---

# Updating HireScope

To download the latest version of the code from GitHub:

```bash
git pull
```

If new packages were added, run:

```bash
pip install -r requirements.txt
```

Then start HireScope again:

```bash
python main.py
```

---

# Troubleshooting

## Python is not recognized

Check if Python is installed:

```bash
python --version
```

If the command is not recognized, reinstall Python and make sure Python is added to the Windows PATH.

---

## Git is not recognized

Check Git:

```bash
git --version
```

If the command does not work, install Git and restart the terminal.

---

## Virtual Environment Cannot Activate

If PowerShell shows an execution policy error, try using Command Prompt instead:

```bash
venv\Scripts\activate
```

---

## Missing Python Module

Activate the virtual environment and run:

```bash
pip install -r requirements.txt
```

---

## Application Does Not Start

Make sure:

- The virtual environment is active
- All packages are installed
- The `.env` file is configured correctly
- Python is installed properly

Then run:

```bash
python main.py
```

---

## SharePoint Export Fails

Check the following:

- SharePoint access is available
- Credentials are correct
- The Excel file path is correct
- The file is not locked
- Internet connection is available
- The correct Daily Scraping file is being used

---

# Security

Do not upload the following to GitHub:

- `.env`
- Passwords
- API keys
- Access tokens
- SharePoint credentials
- Confidential client information

Make sure your `.gitignore` includes:

```gitignore
.env
venv/
__pycache__/
*.pyc
```

---

# New Machine Setup Checklist

Use this checklist when setting up HireScope on another computer:

```text
1. Install Git
2. Install Python
3. Install Visual Studio Code
4. Clone the HireScope repository
5. Open the project folder
6. Create the virtual environment
7. Activate the virtual environment
8. Install requirements.txt
9. Configure the .env file
10. Confirm SharePoint / service access
11. Run python main.py
12. Perform a small test scrape
13. Verify the exported results
```

---

# Quick Start

```bash
git clone https://github.com/USERNAME/HireScope.git

cd HireScope

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

python main.py
```

---

# Project Status

HireScope is an actively maintained internal tool.

Scraping rules, filters, integrations, and export workflows may change as the system continues to be improved.

Always use the latest approved version of the repository and documentation.

---

## HireScope – MedCall Healthcare Scraping Tool
