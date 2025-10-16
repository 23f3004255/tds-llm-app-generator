# 🤖 LLM Code Deployment & Evaluation Automation

A fully automated backend system that:
- Accepts a **POST request** with task instructions,
- Uses an **LLM** to generate a minimal functional web app,
- Publishes it to **GitHub Pages** automatically,
- Submits the repo and commit details to an **evaluation endpoint** within 10 minutes.

This repository demonstrates an end-to-end continuous deployment workflow using Python, FastAPI, and GitHub APIs — designed for scalable LLM-based coding challenges.

---

## 🧩 Project Overview

When a student (or external system) sends a JSON payload describing a coding task, this system:

1. Validates and parses the incoming request.  
2. Generates the required web app using an LLM (e.g., GPT).  
3. Creates a new public GitHub repository named after the task (e.g., `task-captcha-solver`).  
4. Adds:
   - MIT License  
   - Professional README.md  
   - All generated app files  
5. Commits and pushes everything to GitHub.  
6. Enables **GitHub Pages** for live access.  
7. Posts the evaluation result JSON (with repo URL, commit SHA, and live Pages URL) back to the evaluation server within **10 minutes**.

---

## ⚙️ Core Features

| Feature | Description |
|----------|--------------|
| 🧠 **LLM Code Generator** | Uses an AI model to create working apps from briefs |
| 💾 **Dynamic GitHub Repo Creation** | Automatically creates, commits, and pushes code |
| 🌍 **GitHub Pages Deployment** | Makes the generated site publicly accessible |
| 🔄 **Evaluation Submission** | Sends results (repo, commit, live URL) to given endpoint |
| ⏱ **Timed Auto-Submission** | Ensures reporting within 10 minutes with exponential backoff |
| 🧾 **License & README Enforcement** | Automatically adds MIT license and complete documentation |

---

## 🧠 Input Specification

The API expects a JSON POST request like this:

```json
{
  "email": "student@example.com",
  "secret": "shared-secret-123",
  "task": "captcha-solver-123",
  "round": 1,
  "nonce": "ab12-...",
  "brief": "Create a captcha solver that handles ?url=https://.../image.png. Default to attached sample.",
  "checks": [
    "Repo has MIT license",
    "README.md is professional",
    "Page displays captcha URL passed at ?url=...",
    "Page displays solved captcha text within 15 seconds"
  ],
  "evaluation_url": "https://example.com/notify",
  "attachments": [
    { "name": "sample.png", "url": "data:image/png;base64,iVBORw..." }
  ]
}
````

---

## 📤 Output Specification (Evaluation Payload)

After deployment, your system must POST this JSON back to the evaluation URL **within 10 minutes**:

```json
{
  "email": "student@example.com",
  "task": "captcha-solver-123",
  "round": 1,
  "nonce": "ab12-...",
  "repo_url": "https://github.com/23f3004255/task-captcha-solver-123",
  "commit_sha": "a1b2c3d4",
  "pages_url": "https://23f3004255.github.io/task-captcha-solver-123/"
}
```

The evaluation server will verify:

* Response received within time limit
* Repo accessibility (public, MIT license, professional README)
* GitHub Pages site is reachable and functioning

---

## 🏗️ Architecture

```
┌────────────────────────────┐
│   POST /api-endpoint       │
│   (JSON task input)        │
└────────────┬───────────────┘
             │
             ▼
     ┌───────────────┐
     │ LLM Generator │  ← generates app code
     └──────┬────────┘
            │
            ▼
  ┌──────────────────────┐
  │ GitHub Automation    │
  │ - Create repo        │
  │ - Commit & push code │
  │ - Enable Pages       │
  └─────────┬────────────┘
            │
            ▼
  ┌──────────────────────┐
  │ Evaluation Handler   │
  │ - Build payload      │
  │ - POST to evaluation │
  │ - Retry if failed    │
  └──────────────────────┘
```

---

## 🧰 Tools & Libraries Used

| Purpose                | Library                       |
| ---------------------- | ----------------------------- |
| Web Framework          | **FastAPI**                   |
| Web Server             | **Uvicorn**                   |
| GitHub API             | **PyGithub**, **requests**    |
| LLM Integration        | **OpenAI GPT API**            |
| Async Tasks            | **Starlette BackgroundTasks** |
| Environment Management | **python-dotenv**             |
| Version Control        | **GitHub REST API**           |
| Deployment             | **GitHub Pages**              |

---

## 🧑‍💻 Setup Instructions

### 1. Clone the Repo

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
GITHUB_USERNAME=23f3004255
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxx
```

> **Note:** The GitHub token must have `repo`, `public_repo`, and `delete_repo` permissions.

---

## ▶️ Running the Server

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

---

## 🧾 Example API Request

```bash
curl -X POST http://127.0.0.1:8000/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "secret": "abc123",
    "task": "captcha-solver-xyz",
    "round": 1,
    "nonce": "nce-123",
    "brief": "Generate a captcha solver...",
    "evaluation_url": "https://example.com/notify"
  }'
```

---

## 🧱 Handling Multiple Rounds

For later rounds (`round = 2`, `round = 3`, etc.):

* The system fetches the same repo.
* Modifies existing code (adds new features or bug fixes).
* Updates README.md.
* Pushes again to redeploy.
* Sends the new commit details to the evaluation URL.

---

## 📬 Retry Logic (Auto Re-Submission)

If evaluation submission fails (due to downtime or rate limit), it will:

* Retry at 1s, 2s, 4s, 8s, … intervals
* Cap retries within **10 minutes**
* Stop after a successful HTTP 200 response

---

## ✅ Example Evaluation Workflow

1. Evaluation server sends:

   ```json
   {
     "email": "student@example.com",
     "secret": "abcd",
     "task": "captcha-solver-456",
     "round": 1,
     "nonce": "xyz-123",
     "evaluation_url": "https://example.com/notify"
   }
   ```

2. Student server generates app → pushes to GitHub → deploys to Pages.

3. Student server sends:

   ```json
   {
     "email": "student@example.com",
     "task": "captcha-solver-456",
     "round": 1,
     "nonce": "xyz-123",
     "repo_url": "https://github.com/student/task-captcha-solver-456",
     "commit_sha": "abc123",
     "pages_url": "https://student.github.io/task-captcha-solver-456/"
   }
   ```

4. Evaluation system verifies:

   * ✅ Repo public and accessible
   * ✅ Pages live
   * ✅ Commit recent and matches task
   * ✅ MIT License and README exist
   * ✅ Sent within time window

---

## 🧾 License

This project is licensed under the **MIT License** — free to use, modify, and distribute with attribution.

---

## 👨‍💻 Author

**Sriyansh Srivastava**
🎓 IITM BS in Data Science
💻 Developer | ML & LLM Enthusiast | Builder of Autonomous Systems
📬 [23f3004255@ds.study.iitm.ac.in](mailto:23f3004255@ds.study.iitm.ac.in)

---

## 🌟 Acknowledgments

* [FastAPI](https://fastapi.tiangolo.com/)
* [PyGithub](https://pygithub.readthedocs.io/)
* [GitHub REST API](https://docs.github.com/en/rest)
* [OpenAI GPT](https://platform.openai.com/)
* [Uvicorn](https://www.uvicorn.org/)

> “Automation is the art of making machines do the thinking — so humans can keep creating.” ⚡
