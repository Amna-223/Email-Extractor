from flask import Flask, render_template, request
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import multiprocessing
from email.mime.text import MIMEText
import smtplib
import json
import sys
import os

app = Flask(__name__)

def run_spider(url, output_file):
    scrapy_project_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'email_extractor')
    sys.path.insert(0, scrapy_project_path)
    os.chdir(scrapy_project_path)
    
    settings = get_project_settings()
    settings.update({
        'FEEDS': {
            output_file: {
                'format' : 'json',
                'overwrite': True
            }
        }
    })

    process = CrawlerProcess(settings)
    process.crawl('email_spider' , url=url)
    process.start()

def send_feedback_email(name, sender_email, message):
    try:
        msg = MIMEText(f"Name: {name}\nEmail: {sender_email}\n\nMessage:\n{message}")
        msg['Subject'] = f"Email Extractor Feedback from {name}"
        msg['From'] = sender_email
        msg['To'] = 'aamnahsaeed223@gmail.com'

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login('aamnahsaeed223@gmail.com', os.environ.get('GMAIL_APP_PASSWORD'))
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


@app.route('/' , methods=['GET', 'POST'])
def home():
    results = None
    error = None
    url = ''

    if request.method == 'POST':
        url = request.form.get('url', '').strip()

        if not url:
            error = "Please enter a URL."
        else:
            # Basic pattern check — fast, no DNS lookup
            if '.' not in url and '://' not in url:
                error = "Please enter a valid URL."
            else:
                # Scheme add karo
                if '://' not in url:
                    url = 'https://' + url

                # Scheme check only — no DNS
                if not url.startswith(('http://', 'https://')):
                    error = "Only http/https URLs are allowed."
                else:
                    output_file = os.path.join(
                        os.path.dirname(os.path.abspath(__file__)),
                        'temp_results.json'
                    )

                    if os.path.exists(output_file):
                        os.remove(output_file)

                    p = multiprocessing.Process(
                        target=run_spider,
                        args=(url, output_file)
                    )
                    p.start()
                    p.join()

                    if os.path.exists(output_file):
                        with open(output_file, 'r') as f:
                            results = json.load(f)

                    if not results:
                        results = []

    return render_template('index.html', results=results, error=error)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    sent = False
    error = None

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not message:
            error = "Please fill in all fields."
        else:
            success = send_feedback_email(name, email, message)
            if success:
                sent = True
            else:
                error = "Failed to send feedback. Please try again later."
    
    return render_template('contact.html', sent=sent, error=error)

@app.route('/terms')
def terms():
    return render_template('terms.html')

if __name__ == '__main__':
    multiprocessing.freeze_support()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)