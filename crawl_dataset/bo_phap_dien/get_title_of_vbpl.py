import requests
from bs4 import BeautifulSoup

def get_title(id):
    
    url = f"https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID={id}"
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin'
    }

    response = requests.get(url, headers=headers)
    # This is a hack to fix the encoding issue
    response.encoding = 'utf-8'

    # Create a BeautifulSoup object
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the div with id 'toanvancontent'
    div_content = soup.find('div', id='toanvancontent')

    # Initialize an empty list to store the texts of centered elements
    centered_texts = []

    # Find the first element inside the div that has the attribute align='center'
    current_element = div_content.find(attrs={"align": "center"})

    # Iterate through the elements until one without align='center' is found
    while current_element:
        centered_texts.append(current_element.get_text())
        current_element = current_element.find_next_sibling()
        
        # Check if the next sibling has align='center'
        if current_element and current_element.get('align') != 'center':
            break

    # Print the collected centered texts
    print(centered_texts)
    centered_texts = "\n".join(centered_texts)
    centered_texts = " ".join([ele for ele in centered_texts.replace('_', ' ').split() if ele not in [' ', '\n', '_']])
    print(centered_texts)

    return centered_texts

if __name__ == '__main__':
    get_title(id=147302)