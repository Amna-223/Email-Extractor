# 📧 Email Extractor

A full-stack web application that intelligently crawls websites to extract publicly available contact emails using multiple extraction strategies, JavaScript rendering, and domain validation. Built with **Scrapy, Playwright, Flask, and Docker**, with a confidence scoring system inspired by **Hunter.io**.

> 🚧 **Live Demo:** *Coming Soon*
> 📹 **Demo Video:** *Coming Soon*

---

## 💡 Why I Built This

I built this project to solve a real-world problem.

Someone close to me regularly needed to collect contact emails from hundreds of websites, but existing tools were expensive and often returned unreliable results.

Instead of relying on paid software, I decided to build my own solution from scratch. Along the way, the project evolved into a complete web application combining intelligent crawling, JavaScript rendering, email validation, confidence scoring, and secure software engineering practices.

---

## 🚀 What It Does

Enter any public website URL and the application intelligently crawls the site, extracts contact emails using multiple extraction strategies, validates domains through MX record checks, and assigns a **High**, **Medium**, or **Low** confidence score to every result.

---

## ✨ Features

* **Multi-method extraction** — checks `mailto:` links, JSON-LD structured data, footer HTML, and free-text regex in priority order
* **JavaScript rendering** — uses Playwright (Chromium) to process dynamic websites that traditional crawlers cannot access
* **MX record validation** — filters invalid email domains by verifying configured mail servers
* **Confidence scoring** — labels every email as High, Medium, or Low confidence based on extraction source and validation results
* **Priority crawling** — visits Contact, About, Team, Careers, and Press pages before general crawling
* **Security-first design** — includes URL validation, SSRF protection, ReDoS protection, and XSS-safe rendering
* **Modern Flask interface** — responsive UI with confidence badges, loading state, feedback page, and Terms of Use

---

## 🏗️ Architecture

```text
User enters URL
      ↓
Flask (app.py)
      ↓
Scrapy Spider (email_spider.py)
  ├── Playwright renders JavaScript pages
  ├── extract_mailto()
  ├── extract_json_ld()
  ├── extract_footer()
  └── extract_regex()
      ↓
Pipeline (pipelines.py)
  ├── MX validation
  ├── Confidence scoring
  └── Confidence filtering
      ↓
Results displayed in Flask UI
```

---

## 🎯 Confidence Scoring

| Source                          | Domain Match         | MX Valid  | Confidence |
| ------------------------------- | -----------------    | --------  | ---------- |
| `mailto` / `json_ld` / `footer` | ✅                  | ✅        | **High**   |
| `regex`                         | ✅                  | ✅        | **Medium** |
| Any method                      | ❌ External domain  | ✅        | **Medium** |
| Any method                      | Any                 | ❌         | **Low**    |

Inspired by Hunter.io's validation philosophy, the application avoids pretending every email is equally reliable. Instead, each result is assigned a confidence level so users can make informed decisions.

---

## 🛠️ Tech Stack

### Backend

* Python 3.12
* Flask
* Scrapy
* scrapy-playwright

### Web Scraping

* BeautifulSoup
* Regular Expressions
* Playwright

### Validation

* dnspython (MX Record Validation)

### DevOps

* Docker

---

## 📸 Screenshots

> *Screenshots will be added soon.*

* Home Page
* Extraction Results
* Confidence Scoring
* Feedback Page

---

## 📁 Project Structure

```text
Email-Extractor/
├── app.py
├── Dockerfile
├── requirements.txt
├── templates/
├── static/
└── email_extractor/
    ├── spiders/
    ├── pipelines.py
    ├── settings.py
    └── items.py
```

---

## ⚙️ Setup

### Clone Repository

```bash
git clone https://github.com/Amna-223/Email-Extractor.git
cd Email-Extractor
```

### Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### Configure Environment

Create a `.env` file:

```env
GMAIL_APP_PASSWORD=your-app-password
```

### Run

```bash
python app.py
```

Open:

```text
http://localhost:5000
```

---

## 🔒 Security

* URL Injection Protection
* SSRF Protection
* ReDoS Protection
* Jinja2 Auto-Escaping (XSS Protection)
* No SQL Injection Surface (Database-free architecture)

---

## 📊 Output

Each extracted email contains:

| Field        | Description          |
| ------------ | -------------------- |
| `email`      | Email address        |
| `confidence` | High / Medium / Low  |
| `found_via`  | Extraction source    |
| `source_url` | Origin page          |
| `domain`     | Email domain         |
| `mx_valid`   | MX validation status |

---

## 🗺️ Roadmap

* Stable cloud deployment
* Batch URL processing (CSV upload)
* CSV / Excel export
* Database caching
* Performance optimization
* Smarter domain relationship detection

---

## 🤝 Contributing

Suggestions, bug reports, and pull requests are welcome.

If you'd like to contribute, feel free to open an issue or submit a pull request.

---

## ⚠️ Disclaimer

This project extracts **publicly available** contact information only.

Users are responsible for ensuring compliance with applicable laws and regulations, including GDPR and CAN-SPAM. The author is not responsible for misuse of the extracted data.

---

## 👤 Author

**Amna Saeed**

* LinkedIn: *(Add your LinkedIn URL)*
* GitHub: https://github.com/Amna-223

---

*Built from scratch using Python, Scrapy, Playwright, Flask, Docker, and modern software engineering practices to solve a real-world problem through intelligent web crawling and email extraction.*
