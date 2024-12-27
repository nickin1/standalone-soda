import zipfile
import os
import ssl
import requests
import shutil
import urllib3
from tqdm import tqdm

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def extract_file(zip_path, file_to_extract, output_path):
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            with zip_ref.open(file_to_extract) as source:
                with open(output_path, 'wb') as target:
                    shutil.copyfileobj(source, target)
        return True
    except Exception as e:
        print(f"Warning: Could not extract file: {e}")
        return True

def download_with_progress(url, filename, desc):
    response = requests.get(url, stream=True, verify=False)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as f:
        with tqdm(
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
            desc=desc
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                size = f.write(chunk)
                pbar.update(size)

def download_and_extract_soda():
    BOLD = '\033[1m'
    END = '\033[0m'
    
    soda_url = ('https://web.archive.org/web/20241111172244/'
                'https://dl.google.com/release2/chrome_component/'
                'kclvp6kisiomadr4jss2t7qxpi_1.1.1.7/'
                'icnkogojpkfjeajonkmlplionaamopkf_1.1.1.7_mac_arm64_adzxhqywcswlaebqt425pwq53bua.crx3')
    
    # https://web.archive.org/web/20241225183845/https://www.google.com/dl/release2/chrome_component/g5jawrf42zwxwplj4xopac5xpq_1.3050.0/oegebmmcimckjhkhbggblnkjloogjdfg_1.3050.0_all_ad7bkzqy4ef3eyen6xhsycb5enpq.crx3

    en_models_url = ('https://web.archive.org/web/20241225183845/'
                  'https://www.google.com/dl/release2/chrome_component/'
                  'g5jawrf42zwxwplj4xopac5xpq_1.3050.0/'
                  'oegebmmcimckjhkhbggblnkjloogjdfg_1.3050.0_all_ad7bkzqy4ef3eyen6xhsycb5enpq.crx3')
    
    try:
        # Download SODA
        print(f"\n{BOLD}Downloading SODA...{END}")
        download_with_progress(soda_url, 'soda.crx3', "Downloading SODA")
        
        print(f"\n{BOLD}Extracting SODA...{END}")
        # Create temp and lib directories
        os.makedirs('temp', exist_ok=True)
        os.makedirs('lib', exist_ok=True)
        
        # Extract SODA to temp directory
        os.system('unzip -o soda.crx3 -d temp 2>/dev/null >/dev/null')
        
        # Move the library file to final location
        os.rename('temp/SODAFiles/libsoda.so', 'lib/libsoda.so')
        
        # Clean up
        shutil.rmtree('temp')
        os.remove('soda.crx3')
        
        soda_path = os.path.abspath('lib/libsoda.so')
        print(f"{BOLD}SODA library extracted to:{END} {soda_path}")
        
        # Download language models
        print(f"\n{BOLD}Downloading language models...{END}")
        download_with_progress(en_models_url, 'models.crx3', "Downloading models")
        
        print(f"\n{BOLD}Extracting language models...{END}")
        models_path = os.path.abspath('models/en-US')
        os.makedirs(models_path, exist_ok=True)
        os.system('unzip -o models.crx3 -d models/en-US 2>/dev/null >/dev/null')
        print(f"{BOLD}Language models extracted to:{END} {models_path}")
        os.remove('models.crx3')


        print(f"\n{BOLD}libsoda binary and language models downloaded successfully, you now have to patch the binary :){END}")
        
        # Clean up
        print("\nDone!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    
    return True

if __name__ == "__main__":
    download_and_extract_soda() 