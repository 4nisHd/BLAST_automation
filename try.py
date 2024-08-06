import requests

def fetch_genome_image_ucsc(position):
    # Define the UCSC API endpoint and parameters
    ucsc_url = "https://genome.ucsc.edu/cgi-bin/hgRenderTracks"
    params = {
        'db': 'hg38',
        'position': position,
        'pix': 800,  # Width of the image in pixels
        'hgt.trackLabel': 'on',
        'hgt.trackLabelType': 'shortLabel',
        'hgt.dinkey': 'text',
        'hgt.imageV1': '1',
        'hgt.psOutput': 'png'
    }
    
    # Send the request to UCSC API
    response = requests.get(ucsc_url, params=params)
    
    # Check if the request was successful
    if response.status_code == 200:
        return response.content  # Return the image data as bytes
    else:
        raise Exception(f"Failed to fetch image from UCSC API: {response.status_code}")

# Usage example:
# image_data = fetch_genome_image_ucsc('chr3:174187152-174187170')
# with open('test_image.png', 'wb') as f:
#     f.write(image_data)
