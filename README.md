# Kalimati Analytics & ETL Pipeline - Local Setup Guide for Ubuntu

## 1. Introduction

Welcome! This guide will walk you through the entire process of setting up the Kalimati Market Analytics project on your Ubuntu computer. This includes running a complete data pipeline (ETL) to download, clean, and load the data, and then running the web dashboard to view it.

**This guide is for any Ubuntu user, even if you have no technical or programming experience.** We will provide exact commands to copy and paste into your terminal.

---

## 2. Prerequisites (One-Time Setup)

Before we begin, we need to install a few essential tools. Open your terminal by pressing **`Ctrl + Alt + T`**.

#### 2.1. System Updates and Core Tools
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git curl python3 python3-pip python3-venv
```

#### 2.2. Java (Required for Spark)
The data transformation step uses Apache Spark, which requires Java.
```bash
sudo apt install -y default-jdk
```

#### 2.3. PostgreSQL (The Database)
1.  Install PostgreSQL:
    ```bash
    sudo apt install -y postgresql postgresql-contrib
    ```
2.  Start and enable the database service:
    ```bash
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    ```
3.  Set the password for the `postgres` user to `postgres`:
    ```bash
    sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';"
    ```

#### 2.4. VS Code (Recommended Code Editor)
```bash
sudo snap install --classic code
```
---

## 3. Step-by-Step Project Setup

### Phase 1: Get the Code and Prepare Directories

1.  **Download (Clone) the Code:**
    ```bash
    # Navigate to your Documents folder
    cd ~/Documents
    
    # Clone the project (replace URL with the actual GitHub link)
    git clone YOUR_GITHUB_REPOSITORY_URL KalimatiProject
    
    # Enter the project directory
    cd KalimatiProject
    ```

2.  **Create Data Directories:**
    ```bash
    mkdir -p ~/Data/Extraction
    mkdir -p ~/Data/Transformation
    ```

### Phase 2: Run the ETL (Extract, Transform, Load) Pipeline

Run these commands one-by-one from inside the `KalimatiProject` directory.

1.  **Extract:** Download the raw data.
    ```bash
    python3 extract/execute.py ~/Data/Extraction
    ```

2.  **Transform:** Clean and structure the data with Spark.
    ```bash
    python3 transform/execute.py ~/Data/Extraction ~/Data/Transformation
    ```

3.  **Load:** Move the clean data into your PostgreSQL database.
    ```bash
    python3 load/execute.py ~/Data/Transformation postgres postgres localhost
    ```
**Your database is now ready!**

### Phase 3: Set Up and Run the Web Application

1.  **Create and Activate a Virtual Environment:**
    ```bash
    # Create
    python3 -m venv venv
    
    # Activate
    source venv/bin/activate
    ```
    *(You will now see `(venv)` in your terminal prompt)*

2.  **Install Python Packages:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure the AI API Key:**
    *   Get a free API key from [Google AI Studio](https://aistudio.google.com/).
    *   Create a `.env` file with your key using this command (paste your key inside the quotes):
    ```bash
    echo "GOOGLE_API_KEY='PASTE_YOUR_API_KEY_HERE'" > .env
    ```

4.  **Run the Application!**
    ```bash
    python3 app.py
    ```
5.  **View the Dashboard:**
    Open your web browser and go to the address: **http://127.0.0.1:5000**

---

## 4. Troubleshooting

-   **`ModuleNotFoundError`:** Your virtual environment is likely not active. Run `source venv/bin/activate` and then `pip install -r requirements.txt`.
-   **"Database connection failed":** Ensure PostgreSQL is running (`sudo systemctl status postgresql`) and that you set the password correctly.
-   **ETL `load` step fails:** The username or password for PostgreSQL is incorrect. The script expects `postgres` for both.

---

## 5. How to Stop the Application

1.  Go to the terminal window where the app is running.
2.  Press **`Ctrl + C`**.
3.  To exit the virtual environment, type `deactivate`.