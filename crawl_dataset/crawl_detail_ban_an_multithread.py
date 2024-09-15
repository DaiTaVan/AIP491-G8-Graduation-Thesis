from tqdm import tqdm
import os
import json
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from urllib.parse import urlparse, unquote

with open('list_vu_an_cap_huyen_remove_duplicate.txt') as f1:
   list_vu_an = [line.strip() for line in f1.readlines()]


def get_filename_from_url(url):
    # Parse the URL to extract the path
    parsed_url = urlparse(url)
    # Decode non-ASCII characters
    path = unquote(parsed_url.path)
    # Extract the file name from the path
    filename = os.path.basename(path)
    return filename

def crawl_worker(ix):
    # Initialize WebDriver (adjust path to your own WebDriver executable)
    driver = webdriver.Chrome()
    input("Press Enter to continue")

    while True:
        try:
            
            sub_list_vu_an = list_vu_an[ix*10000:(ix+1)*10000]
            num_processed = 0
            if os.path.exists(f'list_vu_an_cap_huyen_full_{ix}.txt'):
                with open(f'list_vu_an_cap_huyen_full_{ix}.txt') as f1:
                    num_processed = len(f1.readlines())
            print('num_processed:', num_processed)
            list_metadata_text = []
            for i in tqdm(range(num_processed, len(sub_list_vu_an))):
                vu_an = sub_list_vu_an[i]
                title, url = vu_an.split('\t\t\t')
                # Open the webpage
                driver.get(url=url)

                try:
                    error_url_text = driver.find_element(By.TAG_NAME, "h1").text
                    print(error_url_text)
                    continue
                except:
                    print()

                # Wait for the page to load (adjust the waiting time if needed)
                if i == 0:
                    input("Press Enter to continue")
                
                # driver.implicitly_wait(10)

                # Get metadata
                metadata_element = driver.find_element(By.CLASS_NAME, 'list-group')

                metadata = metadata_element.text

                # Get download link
                try:
                    download_element = driver.find_element(By.LINK_TEXT, 'Tải quyết định')
                except:
                    try:
                        download_element = driver.find_element(By.LINK_TEXT, 'Tải bản án')
                    except:
                        raise ReferenceError
                download_element.click()

                original_filename = download_element.text
                try:
                    element = driver.find_element(By.CLASS_NAME, 'btn_set_color')
                    
                    file_click_link = element.find_element(By.TAG_NAME, 'a')
                    

                    file_link = file_click_link.get_attribute('href')
                    
                    name = get_filename_from_url(file_link)
                    output_name = '__SLASH__'.join([file_link.split('/')[-2], name])
                    src_name = f"/media/tavandai/DATA/fpt_university/Graduation_Thesis/ChatLaw/dataset/vu_an/{name}"
                    dst_name = f"/media/tavandai/DATA/fpt_university/Graduation_Thesis/ChatLaw/dataset/vu_an/{output_name}"
                    if not os.path.exists(dst_name):
                        while True:
                            if os.path.exists(src_name):
                                break
                            file_click_link.click()

                            time.sleep(1)

                        while True:
                            try:
                                os.rename(src=src_name, dst=dst_name)
                                break
                            except Exception as error:
                                print(file_link)
                                print(error)
                                time.sleep(3)
                                continue

                    full_metadata = {
                        'title': title,
                        'url': url,
                        'metadata': metadata,
                        'original_filename': original_filename,
                        'download_link': file_link
                    }
                    full_metadata_text = json.dumps(full_metadata, ensure_ascii=False)
                    list_metadata_text.append(full_metadata_text)

                    if len(list_metadata_text) % 10 == 0:
                        with open(f'list_vu_an_cap_huyen_full_{ix}.txt', 'a') as f1:
                            for ele in list_metadata_text:
                                f1.write(f'{ele}\n')
                        list_metadata_text = []
                except:
                    continue
        except:
            print('Error, retry')

crawl_worker(1)
