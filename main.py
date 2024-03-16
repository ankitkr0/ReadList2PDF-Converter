from flask import Flask, render_template, request, send_from_directory, send_file
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import os
import base64
import json
import time
import PyPDF2

app = Flask(__name__)

def setup_driver():
    # Configure Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": os.getcwd(),
        "download.prompt_for_download": False,
    })
    # Initialize WebDriver with ChromeDriverManager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def convert_to_pdf(url, output_filename):
    driver = setup_driver()
    driver.get(url)
    
    # Use Chrome DevTools Protocol to change page into print mode, then print to PDF
    calculated_print_options = {
        "landscape": False,
        "displayHeaderFooter": False,
        "printBackground": True,
        "preferCSSPageSize": True,
    }
    result = driver.execute_cdp_cmd("Page.printToPDF", calculated_print_options)
    pdf_content = base64.b64decode(result['data'])
    
    # Define path for the PDF file
    pdf_path = os.path.join(os.getcwd(), f"{output_filename}.pdf")
    
    # Save the PDF to a file
    with open(pdf_path, "wb") as f:
        f.write(pdf_content)
    
    driver.quit()
    return pdf_path

def combine_pdfs(pdf_list, output_filename):
    pdf_writer = PyPDF2.PdfWriter()

    for pdf in pdf_list:
        pdf_reader = PyPDF2.PdfReader(pdf)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            pdf_writer.add_page(page)

    with open(output_filename, 'wb') as out:
        pdf_writer.write(out)

    return output_filename

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        urls = request.form.get('urls', '').splitlines()
        pdf_paths = []
        if urls:  # Check if there's at least one URL
            for i, url in enumerate(urls):
                output_filename = f"pdf_{i}"
                pdf_path = convert_to_pdf(url, output_filename)  # Convert URL to PDF
                pdf_paths.append(pdf_path)
            
            if pdf_paths:
                combined_pdf_path = combine_pdfs(pdf_paths, "combined.pdf")  # Combine PDFs
                return send_file(combined_pdf_path, as_attachment=True)  # Serve the combined PDF as a download
            else:
                return "No PDFs generated."
        else:
            return "No URLs provided."
    
    return render_template('home.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
