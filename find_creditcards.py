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
    "Chase Sapphire Preferred": 'https://www.irvinecompanycredit_cards.com/locations/northern-california/santa-clara/santa-clara-square/availability.html?baths=2&beds=2#floor-plan-list'
}

filter_apt = {
    "Santa Clara Square": {'03 330'}
}

filter_start_date = datetime(2022, 8, 20)


def check_availability(filter_res=False):

    print("Time:", datetime.now().strftime("%m/%d/%Y %H:%M:%S"))

    for apt_name, apt_url in credit_cards.items():

        while True:
            browser = webdriver.Firefox(options=opts)
            browser.implicitly_wait(10)
            browser.get(apt_url)
            raw_html = browser.page_source
            soup = bs(raw_html, "lxml")
            html = soup.prettify()

            all_units = soup.select('div[class*="fapt-fp-unit fapt-fp-unit__table-row"]')
            if len(all_units) == 0:
                print("Page didn't load for", apt_name)
                browser.quit()
                sleep(10)
            else:
                break

        print(apt_url)

        # with open(f'{apt_name}.html', 'w') as f:
        #     f.write(html)

        messages = []
        avail_dates = []
        for unit in all_units:
            name = unit.find('span', class_='fapt-fp-unit__unit-name-text').text.strip()
            price = unit.find('div', class_='fapt-fp-unit__column-inner fapt-fp-unit__column-inner--price').text.strip()
            avail = unit.find('div', class_='fapt-fp-unit__column-inner fapt-fp-unit__column-inner--available').text.strip()
            date = datetime.now() if avail == 'Today' else datetime.strptime(avail, '%m/%d/%Y')

            if filter_res and (date < filter_start_date or name in filter_apt[apt_name]):
                continue

            messages.append(f'{name:8s} - {price:8s} - {avail:12s}\n')
            avail_dates.append(date)
            
        if len(messages) > 0:
            messages = [x for _, x in reversed(sorted(zip(avail_dates, messages)))]
            message_all_units = '=' * 20 + ' ' + apt_name + (' (Filtered)' if filter_res else '') + ' ' + datetime.now().strftime("%m/%d %H:%M") + ' ' + '=' * 20 + '\n' + ''.join(messages)
            print(message_all_units)

            wandb.alert(
                title=apt_name + (' (Filtered)' if filter_res else ''), 
                text=message_all_units,
                level=wandb.AlertLevel.INFO,
            )

        elif not filter_res:
            print(f'No units available for {apt_name}')
            wandb.alert(
                title=apt_name + ' (No units available)', 
                text=f'No units available for {apt_name}',
                level=wandb.AlertLevel.WARN,
                wait_duration=0
            )
        else:
            print(f'No units available for {apt_name} (Filtered)')

        
        browser.quit()


check_availability()
sleep(60)
check_availability(filter_res=True)

while True:

    while datetime.now().minute % 15 != 0:
        sleep(1)
    
    if datetime.now().hour == 9 and datetime.now().minute < 10:
        check_availability()
        sleep(60)

    check_availability(filter_res=True)

    sleep(60)


