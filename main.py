import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re


url = "https://blast.ncbi.nlm.nih.gov/Blast.cgi?PAGE_TYPE=BlastSearch&BLAST_SPEC=OGP__9606__9558&LINK_LOC=blasthome"
driver = webdriver.Chrome()

try:
    driver.get(url)

    sequence_textarea = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "seq"))
    )
    sequence_textarea.send_keys("ATGCAGTAGCTAGCTAGCTAG")  

    blast_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//div[@id='blastButton1']/input[@class='blastbutton']"))
    )
    blast_button.click()

    WebDriverWait(driver, 120).until(
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

    for result in results:
        print('---------title-------------------')

        print(f"dlfRow: {result['dlfRow']}")
        for pair in result['hd_ar_pairs']:
            print('---------------hd-------------')

            print(f"  hd: {pair['hd']}")
            print('----------------ar----------------')
            print(f"  ar: {pair['ar']}")
    print(len(results))

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

def parse_ar(ar_text):
    match = re.search(r'Query\s+\d+\s+(\S+)\s+\d+\s+\|\|+\s+(\S+)\s+\d+', ar_text)
    if match:
        query_seq = match.group(1)
        sbjct_seq = match.group(2)
        sequence_alignment = query_seq + ' | ' + sbjct_seq
    else:
        sequence_alignment = None

    return sequence_alignment

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
                'dlfRow': dlfRow,
                'sequence_alignment': sequence_alignment,
                'position_start': position_start,
                'position_end': position_end,
                'features': features_str
            })
    
    with open(output_csv, 'w', newline='') as csvfile:
        fieldnames = ['dlfRow', 'sequence_alignment', 'position_start', 'position_end', 'features']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for result in results:
            writer.writerow(result)

input_csv = r'C:\Users\Anis\Desktop\Crispr model\off_target\blast_.csv'
output_csv = 'transformed_blast.csv'
transform_csv(input_csv, output_csv)
    
