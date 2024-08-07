import os
import pandas as pd
import concurrent.futures
from fpdf import FPDF
import io
from flask import Flask, send_file, Blueprint, make_response
import requests

app = Flask(__name__)

report_blueprint = Blueprint('report_bp', __name__, template_folder='templates')

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'R')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f'{self.page_no()}/{{nb}}', 0, 0, 'C')

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
        raise Exception(f"Failed to fetch data from UCSC API: {response.status_code}")

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
        return 404

    df = pd.read_csv(csv_file_path)

    pdf = PDF()
    pdf.alias_nb_pages()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_row = {executor.submit(generate_image_data, row, i): (row, i) for i, row in df.iterrows()}
        for future in concurrent.futures.as_completed(future_to_row):
            row, idx = future_to_row[future]
            try:
                image_path = future.result()

                pdf.add_page()
                pdf.set_fill_color(0, 102, 204)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, f"""Off-Target Report: Sequence "{row[1]}" """, 0, 1, 'C', fill=True)

                pdf.ln(10)

                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(50, 10, "Chromosome ID:", 0, 0)
                pdf.set_font('Arial', '', 12)
                pdf.cell(0, 10, f"{row[0]}", 0, 1)
                
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(50, 10, "Sequence alignment:", 0, 0)
                pdf.set_font('Arial', '', 12)
                pdf.cell(0, 10, f"{row[1]}", 0, 1)

                pdf.set_font('Arial', 'B', 12)
                pdf.cell(50, 10, "Position start:", 0, 0)
                pdf.set_font('Arial', '', 12)
                pdf.cell(0, 10, f"{row[2]}", 0, 1)

                pdf.set_font('Arial', 'B', 12)
                pdf.cell(50, 10, "Position end:", 0, 0)
                pdf.set_font('Arial', '', 12)
                pdf.cell(0, 10, f"{row[3]}", 0, 1)


                pdf.set_font('Arial', 'B', 12)
                pdf.cell(50, 10, "Protein products:", 0, 0)
                texts=row[4].split(';')
                pdf.set_font('Arial','',10)
                for t in texts:
                    pdf.cell(30,10,t.strip(),0,1)

                pdf.ln(10)

                pdf.image(image_path, x=10, y=None, w=190)
                os.remove(image_path)
            except Exception as e:
                print(f"Error processing row {idx}: {e}")
    pdf_output_path = r'C:\Users\Anis\Desktop\Crispr model\off_target\generated_report.pdf'
    with open(pdf_output_path, 'wb') as f:
        f.write(pdf.output(dest='S').encode('latin1'))
        
    pdf_output = io.BytesIO()
    pdf_output.write(pdf.output(dest='S').encode('latin1'))
    pdf_output.seek(0)

    response = make_response(pdf_output.getvalue())
    response.headers.set('Content-Disposition', 'attachment', filename='generated_report.pdf')
    response.headers.set('Content-Type', 'application/pdf')

    return response

app.register_blueprint(report_blueprint)

if __name__ == '__main__':
    app.run(debug=True)
