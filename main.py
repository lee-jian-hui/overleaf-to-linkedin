import argparse
import json
import os
import re
import time
import random
import requests
import fitz  # PyMuPDF

from typing import Dict, Callable
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# === CONSTANTS ===
LINKEDIN_BASE_URL = "https://www.linkedin.com"
OVERLEAF_BASE_URL = "https://www.overleaf.com"
OLLAMA_HOST_URL = "http://localhost:11434"

# === Load .env ===
load_dotenv()

OVERLEAF_EMAIL = os.getenv("OVERLEAF_EMAIL")
OVERLEAF_PASSWORD = os.getenv("OVERLEAF_PASSWORD")
OVERLEAF_PROJECT_URL = os.getenv("OVERLEAF_PROJECT_URL")
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

def human_delay(min_ms=100, max_ms=400):
    time.sleep(random.uniform(min_ms, max_ms) / 1000)

class ResumeProcessor:
    def __init__(self, summarizer: Callable[[str], str] = None):
        self.summarizer = summarizer

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        doc = fitz.open(pdf_path)
        return "\n".join([page.get_text() for page in doc])

    def parse_resume_text(self, text: str) -> Dict:
        parsed = {"summary": "", "experience": [], "education": [], "skills": [], "projects": []}
        sections = re.split(r"\n(?=[A-Z][a-z]+:)", text)
        for section in sections:
            header = section.split(":", 1)[0].lower()
            body = section.split(":", 1)[1].strip() if ":" in section else ""
            lines = [line.strip() for line in body.split("\n") if line.strip()]
            if "summary" in header or "about" in header:
                parsed["summary"] = body
            elif "experience" in header:
                parsed["experience"] = lines
            elif "education" in header:
                parsed["education"] = lines
            elif "skills" in header:
                parsed["skills"] = re.split(r"[,\n]", body)
            elif "project" in header:
                parsed["projects"] = lines
        return parsed

    def summarize_to_linkedin_format(self, parsed_json: Dict) -> Dict:
        structured_exp = []
        for exp in parsed_json.get("experience", []):
            match = re.match(r"(.*) at (.*) \\(.*\\)", exp)
            title, company, duration = match.groups() if match else (exp, "Unknown", "Unknown")
            description = self.summarizer(exp) if self.summarizer else ""
            structured_exp.append({
                "title": title.strip(),
                "company": company.strip(),
                "duration": duration.strip(),
                "description": description
            })
        return {
            "headline": parsed_json.get("summary", "")[:120],
            "experience": structured_exp,
            "education": parsed_json.get("education", []),
            "skills": parsed_json.get("skills", []),
        }

class OverleafDownloader:
    def __init__(self):
        pass

    def download_pdf(self, project_url: str, output_path: str):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()

            print("[*] Opening Overleaf login page...")
            page.goto(f"{OVERLEAF_BASE_URL}/login")
            human_delay(1000, 1500)

            print("[*] Please log in manually (e.g., Google SSO)...")
            input("🔒 Press ENTER once you're logged in and the project is fully loaded...")

            if "/project/" in project_url:
                project_id = project_url.rstrip("/").split("/")[-1]
                project_url = f"{OVERLEAF_BASE_URL}/project/{project_id}"

            print("[*] Navigating to Overleaf project page...")
            page.goto(project_url)
            human_delay(2000, 3000)

            print("[*] Triggering compile via Ctrl+Enter (with delay)...")
            page.keyboard.down("Control")
            human_delay(200, 400)
            page.keyboard.press("Enter")
            page.keyboard.up("Control")
            print("[*] Waiting for Overleaf to generate PDF...")
            human_delay(3000, 5000)

            print("[*] Clicking 'Download PDF' button...")
            page.locator("#panel-pdf span:text('Download')").click(timeout=10000)
            human_delay(1000, 2000)

            print("[*] Waiting for download...")
            with page.expect_download(timeout=60000) as download_info:
                pass
            download = download_info.value
            download.save_as(output_path)

            print(f"✅ PDF downloaded to {output_path}")
            browser.close()

class LinkedInUploader:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password

    def fill_profile(self, data: Dict):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            print("[*] Logging into LinkedIn...")
            page.goto(f"{LINKEDIN_BASE_URL}/login")
            human_delay(1000, 1500)
            page.fill("input#username", self.email)
            human_delay(200, 500)
            page.fill("input#password", self.password)
            human_delay(200, 500)
            page.click("button[type='submit']")
            page.wait_for_timeout(5000)

            if "captcha" in page.content().lower():
                print("⚠️ CAPTCHA detected. Please solve it manually.")
                input("🔒 Press ENTER when done...")

            print("[*] Navigating to profile...")
            page.goto(f"{LINKEDIN_BASE_URL}/in/me/edit/intro/")
            page.wait_for_timeout(5000)

            for exp in data["experience"]:
                print(f"• {exp['title']} @ {exp['company']} ({exp['duration']})")

            time.sleep(30)
            browser.close()

def offline_llm_stub(text: str) -> str:
    prompt = f"Summarize this resume bullet point for a LinkedIn profile:\n\n{text}\n\nSummary:"
    try:
        response = requests.post(
            f"{OLLAMA_HOST_URL}/api/generate",
            json={"model": "mistral", "prompt": prompt, "stream": False}
        )
        return response.json().get("response", "").strip()
    except Exception as e:
        print("⚠️ Failed to contact Ollama:", e)
        return text

def cli_main():
    parser = argparse.ArgumentParser(description="Latex PDF to LinkedIn automation CLI")
    subparsers = parser.add_subparsers(dest="command")

    download_parser = subparsers.add_parser("download", help="Download PDF from Overleaf")
    download_parser.add_argument("--from-url", type=str, required=True, help="Overleaf share URL")

    upload_parser = subparsers.add_parser("upload", help="Upload parsed resume to LinkedIn")
    upload_parser.add_argument("--from-pdf", type=str, required=True, help="Path to local resume PDF")

    args = parser.parse_args()

    if args.command == "download":
        overleaf = OverleafDownloader()
        overleaf.download_pdf(project_url=args.from_url, output_path="resume_from_overleaf.pdf")

    elif args.command == "upload":
        pdf_path = args.from_pdf
        processor = ResumeProcessor(summarizer=offline_llm_stub)
        text = processor.extract_text_from_pdf(pdf_path)
        parsed = processor.parse_resume_text(text)
        linkedin_data = processor.summarize_to_linkedin_format(parsed)

        with open("resume_parsed.json", "w") as f:
            json.dump(linkedin_data, f, indent=2)
        print("✅ Saved as resume_parsed.json")

        linkedin = LinkedInUploader(email=LINKEDIN_EMAIL, password=LINKEDIN_PASSWORD)
        linkedin.fill_profile(linkedin_data)

    else:
        parser.print_help()

if __name__ == "__main__":
    cli_main()
    # python main.py download --from-url https://www.overleaf.com/project/xxxxxx
    # python main.py upload --from-pdf resume_from_overleaf.pdf
