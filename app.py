from flask import Flask, render_template, request
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import multiprocessing
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

@app.route('/' , methods=['GET', 'POST'])
def home():
    results = None
    error = None
    url = ''

    if request.method == 'POST':
        url = request.form.get('url', '').strip()

        if not url:
            error = "Enter URL first"
        else:
            output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_results.json')

            p = multiprocessing.Process(
                target = run_spider, 
                args = (url, output_file)
            )

            p.start()
            p.join()

            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    results = json.load(f)

            if not results:
                results = []

        return render_template('index.html', results=results, error=error)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    app.run(debug=True)