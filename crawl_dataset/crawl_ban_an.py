import time
from selenium import webdriver
from selenium.webdriver.common.by import By

def get_page(driver):
    select = driver.find_element(By.NAME, "ctl00$Content_home_Public$ctl00$DropPages")
    all_options = select.find_elements(By.TAG_NAME, 'option')
    page = -1
    for option in all_options:
        if option.get_attribute('selected'):
            page = int(option.text)
            break
    
    return page
def select_page(driver, selected_page):
    select = driver.find_element(By.NAME, "ctl00$Content_home_Public$ctl00$DropPages")
    all_options = select.find_elements(By.TAG_NAME, 'option')
    for option in all_options:
        if int(option.text) == selected_page:
            option.click()
            while True:
                if get_page(driver=driver) == selected_page:
                    break
                time.sleep(10)
            break
    if get_page(driver=driver) != selected_page:
        select_page(driver=driver, selected_page=selected_page)

def check_open(driver):
    try:
        driver.title
        return True
    except:
        return False

def startup(driver):
    try:
        disallow = driver.find_element(By.CLASS_NAME, "sp-disallow-btn")
        disallow.click()
    except:
        print()
    
    job_choose = driver.find_element(By.ID, "ctl00_Feedback_Home_Radio_STYLE_7")
    job_choose.click()
    xac_nhan = driver.find_element(By.NAME, "ctl00$Feedback_Home$cmdSave_Regis")
    xac_nhan.click()
    cap_toa_an = driver.find_element(By.NAME, "ctl00$Content_home_Public$ctl00$Drop_Levels_top")
    option_cap_toa_an = cap_toa_an.find_elements(By.TAG_NAME, "option")
    option_cap_toa_an[4].click()
    tim_kiem_button = driver.find_element(By.NAME, "ctl00$Content_home_Public$ctl00$cmd_search_banner")
    tim_kiem_button.click()

while True:
    # Initialize WebDriver (adjust path to your own WebDriver executable)
    driver = webdriver.Chrome()

    # Open the webpage
    driver.get("https://congbobanan.toaan.gov.vn/0tat1cvn/ban-an-quyet-dinh?fbclid=IwY2xjawFHip1leHRuA2FlbQIxMAABHQHl5CbXvLfvbk8pGLkLxNDszVKIUMBCMcUKZokdPutT1AruCNScmwvq0Q_aem_bdZKA7gvZFShedmVWVllpA")

    # Wait for the page to load (adjust the waiting time if needed)
    driver.implicitly_wait(10)

    startup(driver)
    start_ix = 0
    with open('list_ban_an_cap_huyen_2.txt', 'r') as f1:
        start_ix = int(f1.readlines()[-1].split('\t')[0]) + 1
    print(start_ix)
    for i in range(start_ix,3001):
        while True:
            try:
                select_page(driver=driver, selected_page=i)
                current_page = get_page(driver=driver)
                list_ban_an = []
                list_control = driver.find_elements(By.CLASS_NAME, "echo_id_pub")
                for ele in list_control:
                    text = ele.text
                    href = ele.get_attribute('href')

                    list_ban_an.append([text, href])
            
                with open('list_ban_an_cap_huyen_2.txt', 'a') as f1:
                    for ele in list_ban_an:
                        f1.write(f'{current_page}\t{ele[0]}\t\t\t{ele[1]}\n')
                break
            except:
                if not check_open(driver):
                    break
                print('Waiting ...')
                time.sleep(10)
        if not check_open(driver):
            break
    