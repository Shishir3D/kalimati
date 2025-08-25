# Kalimati Market Analytics - Local Setup Guide

## 1. Introduction

Welcome! This guide will walk you through the process of setting up and running the Kalimati Market Analytics dashboard on your own computer.

**What does this application do?**
This is a web-based dashboard that visualizes historical price data for vegetables, fruits, and other produce from Nepal's Kalimati market. It also includes an "AI Recipe Helper" that can suggest Nepali recipes based on a budget you provide.

**Who is this guide for?**
This guide is for anyone, even if you have **no technical or programming experience**. We will explain every step in plain language, from installing the necessary tools to running the application.

---

## 2. What You'll Need (Prerequisites)

Before we download the code, we need to install a few essential tools on your computer.

#### Tool 1: Python (The Engine)
The application is written in Python. We need to install it so your computer can run the code.
1. Go to the official Python download page: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download and run the installer.
3. **VERY IMPORTANT (for Windows users):** On the first screen of the installer, check the box at the bottom that says **"Add Python.exe to PATH"**. This is crucial!
   
4. Follow the on-screen instructions to complete the installation.

#### Tool 2: PostgreSQL and pgAdmin (The Database)
The application needs a database to store all the price data. We will use PostgreSQL.
1. Go to the PostgreSQL download page: [https://www.postgresql.org/download/](https://www.postgresql.org/download/)
2. Download and run the installer for your operating system.
3. During installation, it will ask you to set a **password** for the `postgres` user. For simplicity, **please set the password to `postgres`**.
4. The installer also includes **pgAdmin 4**, a user-friendly tool to manage the database.

#### Tool 3: Git (The Code Downloader)
We'll use Git to download the project from GitHub.
1. Go to the Git download page: [https://git-scm.com/downloads](https://git-scm.com/downloads)
2. Download and install Git, accepting all the default settings.

#### Tool 4: A Code Editor (e.g., VS Code)
We recommend a free, easy-to-use editor like Visual Studio Code to view project files.
1. Download and install it from: [https://code.visualstudio.com/](https://code.visualstudio.com/)

---

## 3. Step-by-Step Setup Guide

### Phase 1: Get the Code from GitHub

1.  Open your command prompt (Windows `cmd`) or terminal (Mac).
2.  Navigate to your Documents folder:
    ```bash
    cd Documents
    ```
3.  Clone the project repository (replace the URL with the actual GitHub link):
    ```bash
    git clone YOUR_GITHUB_REPOSITORY_URL
    ```
4.  Navigate into the newly created project folder:
    ```bash
    cd project-folder-name
    ```

> **Alternative:** On the GitHub page, click the green "<> Code" button and "Download ZIP". Unzip the file and navigate into the folder using the `cd` command in your terminal.

### Phase 2: Set Up the Database and Import Data

1.  Open **pgAdmin 4**.
2.  Connect to your local server using the password you set (`postgres`).
3.  **Create the Database:**
    *   Right-click **Databases > Create > Database...**
    *   Enter the name `postgres` and click **Save**.
4.  **Import the Data:**
    *   In the left panel, navigate to `Databases > postgres > Schemas > public`.
    *   Right-click on **Tables** and select **Import/Export Data...**
    *   Select the **Import** toggle.
    *   For **Filename**, browse to the `kalimati_master.csv` file inside your project folder.
    *   Turn **ON** the **Header** switch.
    *   Click **OK**. This creates and populates the `kalimati_master` table.

### Phase 3: Set Up the Project's Environment

1.  In your terminal (inside the project folder), create a virtual environment:
    ```bash
    python -m venv venv
    ```
2.  Activate the environment:
    *   **Windows:** `venv\Scripts\activate`
    *   **Mac/Linux:** `source venv/bin/activate`
    (You should see `(venv)` at the start of your command line.)
3.  Install all required packages from the `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```

### Phase 4: Configure the AI Helper (API Key)

1.  Get a free API key from Google AI Studio: [https://aistudio.google.com/](https://aistudio.google.com/)
2.  Click **"Get API key"** and create one in a new project. Copy the key.
3.  In your project folder, create a new file named exactly **`.env`**.
4.  Open the `.env` file and add the following line, pasting your key:
    ```
    GOOGLE_API_KEY="PASTE_YOUR_API_KEY_HERE"
    ```
5.  Save and close the file.

### Phase 5: Run the Application!

1.  Make sure your virtual environment is active (`(venv)` is visible).
2.  Run the application with this command:
    ```bash
    python app.py
    ```
3.  You will see output in the terminal, including a line like: `* Running on http://127.0.0.1:5000`
4.  Open your web browser and go to this address: **http://127.0.0.1:5000**
5.  Congratulations, the dashboard is running!

---

## 4. Troubleshooting Common Issues

-   **`python` or `pip` is not recognized:** You likely forgot to check **"Add Python to PATH"** during installation. Reinstall Python and make sure that box is checked.
-   **"Database connection failed":** Ensure PostgreSQL is running, your database is named `postgres`, and the password is `postgres`.
-   **Charts are empty:** The data import failed. Carefully repeat the steps in **Phase 2, Step 4**.
-   **AI Recipe Helper gives an error:** Your API key in the `.env` file is likely incorrect. Double-check it.

---

## 5. How to Stop the Application

1.  Go to the terminal window where the app is running.
2.  Press **`Ctrl + C`**.
3.  To exit the virtual environment, type `deactivate`.