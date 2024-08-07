from flask import Blueprint, request, render_template,jsonify,Flask
import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re



gRNA_blueprint = Blueprint('gRNA_bp', __name__,template_folder='templates')
url = "https://blast.ncbi.nlm.nih.gov/Blast.cgi?PAGE_TYPE=BlastSearch&BLAST_SPEC=OGP__9606__9558&LINK_LOC=blasthome"
driver = webdriver.Chrome()


def process_chr(chr_loc):
    pattern = re.compile(r'Homo sapiens.*?chromosome (\d+)', re.IGNORECASE)
    match = pattern.search(chr_loc)
    
    if match:
        chromosome_number = match.group(1)
        return f'Homo Sapien Chromosome {chromosome_number}'
    else:
        return 'No chromosome found'


def parse_hd(hd_text):
    match = re.search(r'Range \d+: (\d+) to (\d+)', hd_text)
    if match:
        position_start = int(match.group(1))
        position_end = int(match.group(2))
    else:
        position_start = None
        position_end = None
    
    features = []
    feature_lines = hd_text.split('Features:')[-1].strip().split('\n')
    for line in feature_lines:
        if line.strip():
            features.append(line.strip())
    
    return position_start, position_end, features

def parse_ar(text):
    pattern = r"Query\s+\d+\s+([A-Z]+)\s+\d+"
    match = re.search(pattern, text)
    if match:
        sequence = match.group(1)
        return sequence
    else:
        return None

def transform_csv(input_csv, output_csv):
    with open(input_csv, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        results = []   
        for row in reader:
            dlfRow = row['dlfRow']
            hd = row['hd']
            ar = row['ar']
            position_start, position_end, features = parse_hd(hd)
            sequence_alignment = parse_ar(ar)
            features_str = '; '.join(features)
            results.append({
                'Chromosome location': process_chr(dlfRow),
                'Sequence alignment': sequence_alignment,
                'Position start': position_start,
                'Position end': position_end,
                'Proteins': features_str
            })
    
    with open(output_csv, 'w', newline='') as csvfile:
        fieldnames = ['Chromosome location', 'Sequence alignment', 'Position start', 'Position end', 'Proteins']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)


        

@gRNA_blueprint.route('/')
def index():
    return render_template('index.html')

@gRNA_blueprint.route('/use_sequence', methods=['GET'])
def use_sequence():
    sequence = request.form['text']
    return sequence

@gRNA_blueprint.route('/process', methods=['GET', 'POST'])
def process():
    sequence = use_sequence()
    if sequence:
        try:
            driver.get(url)
            sequence_textarea = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "seq"))
            )
            sequence_textarea.send_keys(sequence)  
            blast_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@id='blastButton1']/input[@class='blastbutton']"))
            )
            blast_button.click()
            format_organism_input = WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.ID, "qorganism"))
            )
            link_to_click = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//tr[@ind='1']//a[@class='deflnDesc']"))
            )
            link_to_click.click()
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            results = []
            one_seq_alns = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'oneSeqAln'))
            )

            for one_seq_aln in one_seq_alns:
                try:
                    dlf_row = one_seq_aln.find_element(By.CLASS_NAME, 'dlfRow').text

                    hd_elements = one_seq_aln.find_elements(By.XPATH, ".//div[contains(@id, 'hd_')]")
                    ar_elements = one_seq_aln.find_elements(By.XPATH, ".//div[contains(@id, 'ar_')]")
                    hd_ar_pairs = []
                    for hd_element, ar_element in zip(hd_elements, ar_elements):
                        hd_text = hd_element.text
                        ar_text = ar_element.text
                        hd_ar_pairs.append({'hd': hd_text, 'ar': ar_text})
                    results.append({'dlfRow': dlf_row, 'hd_ar_pairs': hd_ar_pairs})
                except Exception as e:
                    print(f"Error processing oneSeqAln: {e}")

            with open('blast_.csv', 'w', newline='') as csvfile:
                fieldnames = ['dlfRow', 'hd', 'ar']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for result in results:
                    dlfRow = result['dlfRow']
                    for pair in result['hd_ar_pairs']:
                        writer.writerow({'dlfRow': dlfRow, 'hd': pair['hd'], 'ar': pair['ar']})
        finally:
            time.sleep(10)
            driver.quit()

        input_csv = r'C:\Users\Anis\Desktop\Crispr model\off_target\blast_.csv'
        output_csv = 'transformed_blast.csv'
        transform_csv(input_csv, output_csv)
        df3 = pd.read_csv(r'C:\Users\Anis\Desktop\Crispr model\off_target\transformed_blast.csv') 
        table_html = df3.to_html(classes='table table-striped', index=False)
        return jsonify ({'Sequences':table_html})
    else:
        return jsonify({'error':KeyError})

