import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

url = "https://blast.ncbi.nlm.nih.gov/Blast.cgi?PAGE_TYPE=BlastSearch&BLAST_SPEC=OGP__9606__9558&LINK_LOC=blasthome"
driver = webdriver.Chrome()

try:
    driver.get(url)

    sequence_textarea = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "seq"))
    )
    sequence_textarea.send_keys("ATGCAGTAGCTAGCTAGCTAG")  # Replace with your actual sequence

    blast_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//div[@id='blastButton1']/input[@class='blastbutton']"))
    )
    blast_button.click()

    # Wait for results to load, adjust the wait time if necessary
    WebDriverWait(driver, 120).until(
        EC.presence_of_element_located((By.ID, "qorganism"))
    )

    link_to_click = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//tr[@ind='1']//a[@class='deflnDesc']"))
    )
    link_to_click.click()

    # Scroll down to load the elements and wait for 2 seconds
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    # Initialize an empty list to hold the results
    results = []

    # Locate all elements with the class 'oneSeqAln'
    one_seq_alns = WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'oneSeqAln'))
    )

    for one_seq_aln in one_seq_alns:
        try:
            # Extract the dlfRow text
            dlf_row = one_seq_aln.find_element(By.CLASS_NAME, 'dlfRow').text

            # Find all hd and ar elements within this oneSeqAln
            hd_elements = one_seq_aln.find_elements(By.XPATH, ".//div[contains(@id, 'hd_')]")
            ar_elements = one_seq_aln.find_elements(By.XPATH, ".//div[contains(@id, 'ar_')]")

            # Create a list of pairs of hd and ar texts
            hd_ar_pairs = []
            for hd_element, ar_element in zip(hd_elements, ar_elements):
                hd_text = hd_element.text
                ar_text = ar_element.text
                hd_ar_pairs.append({'hd': hd_text, 'ar': ar_text})

            # Append the dlfRow text and the list of hd_ar pairs to the results
            results.append({'dlfRow': dlf_row, 'hd_ar_pairs': hd_ar_pairs})
        except Exception as e:
            print(f"Error processing oneSeqAln: {e}")

    # Print the results
    for result in results:
        print('---------title-------------------')

        print(f"dlfRow: {result['dlfRow']}")
        for pair in result['hd_ar_pairs']:
            print('---------------hd-------------')

            print(f"  hd: {pair['hd']}")
            print('----------------ar----------------')
            print(f"  ar: {pair['ar']}")
    print(len(results))

    # Save the results to a CSV file
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
