# 📄 Resume-to-LinkedIn Parser with LLM Summarization (Ollama + Python)

This tool converts your LaTeX-generated **PDF resume** into **LinkedIn-compatible JSON**, using an offline LLM via **Ollama** to summarize your experience and skills. Optionally, it can assist in opening your LinkedIn profile and partially automate data entry using **Playwright**.

---

## ✨ Features

* 📄 Extracts resume sections: Summary, Experience, Education, Skills, Projects
* 🧠 Summarizes raw bullet points into LinkedIn-friendly descriptions using **Ollama**
* 🗂 Outputs clean `resume_parsed.json`
* 🔐 CAPTCHA-safe automation: pauses for manual resolution
* 💻 100% Offline capable (privacy-first)

---

## 📦 Requirements

* Python 3.8+
* [Ollama](https://ollama.com) installed and running
* Chromium browser for automation
* Linux/macOS/Windows (WSL supported)

---

## 🔧 Installation

### 1. Install Python dependencies

```bash
pip install pymupdf playwright requests
playwright install
```

### 2. Install and Run Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull mistral

# Start serving the model
ollama run mistral
```

You can substitute `mistral` with `llama3`, `phi3`, `gemma`, etc.

---

## 🧪 Usage

### A. Just Parse and Summarize Resume

```bash
python main.py
```

This will:

* 📂 Read `resume.pdf`
* 🧠 Summarize job experiences via Ollama
* 📄 Save output to `resume_parsed.json`

### B. Attempt LinkedIn Autofill (Manual CAPTCHA)

```bash
python resume_to_linkedin.py --upload --email your@email.com --password yourpassword
```

This will:

* 🔐 Open LinkedIn via Playwright
* ✋ Pause if a CAPTCHA is detected for manual solving
* 🗺️ Navigate to your profile edit page and allow you to paste the structured data

> ⚠️ **IMPORTANT:** This does not directly write into your profile fields. It assists by opening and navigating the browser for convenience.

---

## 🧠 Example Output: `resume_parsed.json`

```json
{
  "headline": "Full-stack engineer focused on scalable backend systems.",
  "experience": [
    {
      "title": "Software Engineer",
      "company": "Dell Technologies",
      "duration": "2022 - 2024",
      "description": "Developed a Redis-based token cache for OAuth2, integrated with internal API marketplace."
    }
  ],
  "education": ["BSc Computer Science – University of XYZ"],
  "skills": ["FastAPI", "Docker", "PostgreSQL"]
}
```

---

## 🛠️ Full Python Script

<details><summary>Click to view code</summary>

```python
# Full script provided above, copy the full `resume_to_linkedin.py` here
```

</details>

---

## 👀 Recommended Ollama Models

| Model   | RAM Required | Notes                                |
| ------- | ------------ | ------------------------------------ |
| phi3    | 4–6 GB       | Fast, ideal for resume summarization |
| mistral | 8–12 GB      | Balanced, high accuracy              |
| llama3  | 12–16 GB     | Very strong comprehension, heavier   |

---

## 📋 License

MIT License © 2025 Your Name

---

## ❓ FAQ

### Can I fully automate LinkedIn uploads?

Not entirely. LinkedIn doesn't allow automatic resume/profile editing via public APIs. This tool simulates browser behavior using Playwright and pauses for manual CAPTCHA resolution. It's designed to help, not replace you.

### Can I use this offline?

Yes — Ollama + this parser works 100% offline (aside from optional browser automation).

### Want a Web UI?

You can build one with Flask or Streamlit! Ask if you'd like a starter.

---
