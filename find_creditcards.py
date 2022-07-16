import wandb
from email import message
from selenium import webdriver
from selenium.webdriver import FirefoxOptions
from bs4 import BeautifulSoup as bs
from datetime import date, datetime
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


wandb.init(project="find-apt")


opts = FirefoxOptions()
opts.add_argument("--headless")

credit_cards = {
    "MBB": 'https://creditcard.americanexpress.com/d/bonvoy-business/',
    "CSP": 'https://creditcards.chase.com/rewards-credit-cards/sapphire/preferred',
}

points_threshold = {
    "MBB": 75000,
    "CSP": 60000,
}


def check_availability(filter_res=False):

    print("Time:", datetime.now().strftime("%m/%d/%Y %H:%M:%S"))

    bonus_dict = dict()
    success = False

    for cc_name, cc_url in credit_cards.items():

        while True:
            browser = webdriver.Firefox(options=opts)
            browser.implicitly_wait(10)
            browser.get(cc_url)
            raw_html = browser.page_source
            soup = bs(raw_html, "lxml")
            html = soup.prettify()
            if cc_name == "CSP":
                elements = soup.find_all('strong', class_='description-title')
            elif cc_name == "MBB":
                elements = soup.find_all('p', class_='text-32 line-height-44 font-bold h-top-5')
            
            if len(elements) == 0:
                print("Page didn't load for", cc_name)
                browser.quit()
                sleep(10)
            else:
                break

        text = [x.text.strip() for x in elements if 'bonus' in x.text.lower().strip()][0]
        text = text.replace(',', '')
        points = max([int(x) for x in text.split() if x.isdigit()])
        if points > points_threshold[cc_name]:
            success = True
        
        bonus_dict[cc_name] = points
        browser.quit()
        
    message = ''
    if success:
        message += 'Yay! We did it!\n'
    for cc_name, points in bonus_dict.items():
        message += f'{cc_name} bonus points: {points}\n'
    print(message)

    if success:
        wandb.alert(
            title='Yay! We did it!', 
            text=message,
            level=wandb.AlertLevel.INFO,
        )
    else:
        wandb.alert(
            title=f'No new bonus',
            text=message,
            level=wandb.AlertLevel.ERROR,
        )



check_availability()

while True:

    if datetime.now().hour == 5 and datetime.now().minute < 10:
        check_availability()
        sleep(800)

    sleep(60)


