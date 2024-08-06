from flask import Flask, send_file, Blueprint, make_response
from fpdf import FPDF
import io
import os
import pandas as pd
import time
import concurrent.futures
import requests

app = Flask(__name__)

report_blueprint = Blueprint('report_blueprint', __name__, template_folder='templates')

def extract_position(row):
    chromosome, start, end = row[0].split()[-1], row[2], row[3]
    return f"chr{chromosome}:{start}-{end}"

def fetch_genome_image_ucsc(position):
    ucsc_url = "https://genome.ucsc.edu/cgi-bin/hgRenderTracks"
    params = {
        'db': 'hg38',
        'position': position,
        'pix': 800,
        'hgt.trackLabel': 'on',
        'hgt.trackLabelType': 'shortLabel',
        'hgt.dinkey': 'text',
        'hgt.imageV1': '1',
        'hgt.psOutput': 'png'
    }
    
    response = requests.get(ucsc_url, params=params)
    
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to fetch image from UCSC API: {response.status_code}")

def generate_image_data(row, idx):
    position = extract_position(row)
    image_data = fetch_genome_image_ucsc(position)
    
    image_path = f'./temp/temp_image_{idx}.png'
    with open(image_path, 'wb') as img_file:
        img_file.write(image_data)
    
    return image_path

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

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_row = {executor.submit(generate_image_data, row, i): (row, i) for i, row in df.iterrows()}
        for future in concurrent.futures.as_completed(future_to_row):
            row, idx = future_to_row[future]
            try:
                image_path = future.result()
                pdf.cell(200, 10, txt=', '.join(map(str, row.values)), ln=True)
                pdf.image(image_path, x=10, y=None, w=200)
                os.remove(image_path)
            except Exception as e:
                print(f"Error processing row {idx}: {e}")

    pdf_output = io.BytesIO()
    pdf_output.write(pdf.output(dest='S').encode('latin1'))
    pdf_output.seek(0)

    response = make_response(pdf_output.getvalue())
    response.headers.set('Content-Disposition', 'attachment', filename='output.pdf')
    response.headers.set('Content-Type', 'application/pdf')

    return response

app.register_blueprint(report_blueprint)

if __name__ == '__main__':
    app.run(debug=True)
