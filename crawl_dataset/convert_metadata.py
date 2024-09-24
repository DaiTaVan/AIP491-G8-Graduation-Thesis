import glob
import json
import os
from urllib.parse import urlparse, unquote
from tqdm import tqdm

def get_filename_from_url(url):
    # Parse the URL to extract the path
    parsed_url = urlparse(url)
    # Decode non-ASCII characters
    path = unquote(parsed_url.path)
    # Extract the file name from the path
    filename = os.path.basename(path)
    output_name = '__SLASH__'.join([url.split('/')[-2], filename])
    return output_name

files = glob.glob('dataset/vu_an/*/*')

map_file_location = {file.split('/')[-1]: '/'.join(file.split('/')[-2:]) for file in files}
map_file_location['5ta1506062t1cvn__SLASH__21_2024_DS_GDT.pdf']

with open("/media/tavandai/DATA1/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/dataset/vu_an/metadata.txt") as f1:
    lines = [json.loads(line.strip()) for line in f1.readlines()]
lines[0]

metadata_dict = {}

for line in tqdm(lines):
    page_link = line['url']
    file_link = line['download_link']
    file_name = get_filename_from_url(file_link)
    if file_name in map_file_location:
        file_path = map_file_location[file_name]
    else:
        continue
    title = line['title']

    if 'tối cao' in title:
        cap_toa_an = 'tối cao'
    elif 'cấp cao' in title:
        cap_toa_an = 'cấp cao'
    elif 'tỉnh' in title:
        cap_toa_an = 'tỉnh'
    elif 'TAND TP' in title:
        cap_toa_an = 'thành phố'
    elif 'TAND Q' in title:
        cap_toa_an = 'quận'
    elif 'Quân khu' in title:
        cap_toa_an = 'quân khu'
    elif 'Quân sự' in title or 'TAQS' in title:
        cap_toa_an = 'quân sự'
    elif "Thành phố " in title:
        cap_toa_an = 'thành phố'
    elif "TAND TX" in title:
        cap_toa_an = 'thị xã'
    elif "huyện" in title:
        cap_toa_an = 'huyện'
    else:
        raise Exception

    metadata_dict[file_path] = {
        'page_link': page_link,
        'file_link': file_link,
        'file_name': file_name,
        'title': title,
        'cap_toa_an': cap_toa_an,
    }
    metadata = line['metadata'].split('\n')
    # print(metadata)
    for ele in metadata:
        # print(ele)
        sub_ele = ele.split(':')
        key = sub_ele[0].strip()
        value  = ':'.join(sub_ele[1:]).strip()
        metadata_dict[file_path][key] = value

json.dump(metadata_dict, open('dataset/vu_an/metadata.json', 'w'), ensure_ascii=False, indent=2)