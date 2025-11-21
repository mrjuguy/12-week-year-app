# 12-Week Execution Engine

A high-performance project management system based on the **12-Week Year** methodology. This application helps you compress your execution cycle, focus on lead indicators, and track your weekly execution score.

## 🚀 Features
- **Dashboard:** Real-time view of your current week and execution score.
- **Execute Mode:** A focused daily view to mark tactics as complete.
- **Strategic Planning:** Define 12-week goals and break them down into weekly tactics.
- **Review:** Visualize your performance history and reflect on weekly wins.

## 🛠️ Local Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd twelve-x
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    # Windows
    .\.venv\Scripts\activate
    # Mac/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    streamlit run src/app.py
    ```

## ☁️ Cloud Deployment (Streamlit Community Cloud)

1.  **Push to GitHub:** Ensure this code is in a public or private GitHub repository.
2.  **Login:** Go to [share.streamlit.io](https://share.streamlit.io/) and log in with GitHub.
3.  **Deploy:**
    *   Click "New App".
    *   Select your repository, branch, and file path (`src/app.py`).
    *   Click "Deploy".

> **Note on Data:** This MVP uses local session state. On Streamlit Cloud, data will reset if the app reboots. For production use, connect a database like Supabase or Google Sheets.

## 📖 Methodology
*   **Vision:** Your 3-year and 1-year "Why".
*   **Goals:** 1-3 SMART goals for the current 12-week cycle.
*   **Tactics:** Specific, actionable steps assigned to a specific week.
*   **Score:** Your weekly "Execution Score" is the % of completed tactics. Aim for **85%+**.
