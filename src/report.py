from flask import Flask, send_file, Blueprint
from fpdf import FPDF
import io
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

app = Flask(__name__)

report_blueprint = Blueprint('report_blueprint', __name__, template_folder='templates')


def extract_position(row):
    chromosome, start, end = row[0].split()[-1], row[2], row[3]
    return f"chr{chromosome}:{start}-{end}"


def fetch_genome_image(position):
    options = Options()
    options.headless = True
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get('https://genome.ucsc.edu/cgi-bin/hgTracks?db=hg38&lastVirtModeType=default&lastVirtModeExtraState=&virtModeType=default&virtMode=0&nonVirtPosition=&position=chr3%3A174187152%2D174187170&hgsid=2326089496_hvkPuryWkwOQObK7SCsBmdjUJ4Hh')
        
        position_input = driver.find_element(By.ID, 'positionInput')
        position_input.clear()
        position_input.send_keys(position)
        
        go_button = driver.find_element(By.ID, 'goButton')
        go_button.click()

        time.sleep(5)

        image_element = driver.find_element(By.ID, 'chrom')
        image_src = image_element.get_attribute('src')

        driver.get(image_src)
        image_data = driver.page_source

    finally:
        driver.quit()

    return image_data


@report_blueprint.route('/generate-pdf', methods=['GET'])
def generate_pdf():
    csv_file_path = r'C:\Users\Anis\Desktop\Crispr model\off_target\transformed_blast.csv'
    
    if not os.path.exists(csv_file_path):
        return 'CSV file not found', 404

    df = pd.read_csv(csv_file_path)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(200, 10, txt="CSV Data with Genome Images", ln=True, align='C')
    
    pdf.set_font('Arial', '', 10)
    for i, row in df.iterrows():
        pdf.cell(200, 10, txt=', '.join(map(str, row.values)), ln=True)
        
        position = extract_position(row)
        image_data = fetch_genome_image(position)
        
        image_path = f'temp_image_{i}.png'
        with open(image_path, 'wb') as img_file:
            img_file.write(image_data)

        pdf.image(image_path, x=10, y=None, w=200)
        
        os.remove(image_path)
    
    pdf_output = io.BytesIO()
    pdf_output.write(pdf.output(dest='S').encode('latin1'))
    pdf_output.seek(0)

    return send_file(pdf_output, as_attachment=True, download_name='output.pdf', mimetype='application/pdf')


app.register_blueprint(report_blueprint)

if __name__ == '__main__':
    app.run(debug=True)
