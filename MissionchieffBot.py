from requests import Session
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
from missions_for_game import *
from car_marks import *
import configparser
from colorama import init, Fore


init()
config = configparser.ConfigParser()
config.read('config.ini')
start_url = config['send']['start_url'].replace('"', '')
time_send = int(config['send']['time_send'].replace('"', '')) - 1
headers = {'User-Agent': UserAgent().random}
work = Session()
work.get('https://www.dispetcher112.ru/', headers=headers)
response = work.get('https://www.dispetcher112.ru/users/sign_in', headers=headers)
soup = BeautifulSoup(response.text, 'lxml')
token = soup.find('form').findAll('input')
token = token[1].get('value')
data = {'authenticity_token': token,
        'user[email]': config["login"]["username"].replace('"', ''),
        'user[password]': config['login']['password'].replace('"', '')}
result = work.post('https://www.dispetcher112.ru/users/sign_in', headers=headers, data=data, allow_redirects=True)


def run(url):
    ms_count = 0
    successfully_mission_list = []
    failed_mission_list = []
    while True:
        ms_count += 1
        if ms_count % 150 == 0:
            successfully_mission_list = check_mission_status(successfully_mission_list)
            failed_mission_list, successfully_mission_list = \
                failed_mission_runner(failed_mission_list, successfully_mission_list)
        soup2 = BeautifulSoup((work.get(url, headers=headers)).text, 'lxml')
        name = get_name(soup2)
        if name == True:
            try:
                url = get_next_url(soup2)
            except AttributeError:
                print('goodbye')
        else:
            data2 = car_collection(get_cars(soup2), missions_for_game.get(name) + get_patients(soup2), url)
            time.sleep(time_send // 2)
            if len(data2.get('vehicle_ids[]')) != 0:
                work.post(f'{url}/alarm', headers=headers, data=data2, allow_redirects=True)
                print(Fore.GREEN + name, 'successfully :', ms_count)
                successfully_mission_list.append(url)
            else:
                print(Fore.RED + name, "failed :", ms_count)
                failed_mission_list.append(url)
            url = get_next_url(soup2)
            time.sleep(time_send // 2)


def get_name(soup3):
    try:
        name = soup3.find('div', class_='mission_header_info row')
        name = name.find('div', class_='col-md-6').get('data-mission-title')
        fire_alarm_system = name.find('(Система пожарной тревоги)')
        if fire_alarm_system != -1:
            name = name.replace('(Система пожарной тревоги)', '')
            name = list(name)
            name.pop(fire_alarm_system - 1)
            name = ''.join(name)
        return name
    except AttributeError:
        return True


def get_patients(soup4):
    patients = soup4.find_all('div', class_='col-sm-4 col-xs-6 mission_patient')
    if len(patients) == 0:
        return []
    else:
        task_ambulance = [M30] + [M31] * len(patients)
        return task_ambulance


def get_cars(soup5):
    cars = soup5.find_all('tr', class_='vehicle_select_table_tr')
    dict_cars = {}
    for t in cars:
        dict_cars.setdefault(t.get('id'), t.get('vehicle_type'))
    return dict_cars


def get_more_cars(url):
    result6 = work.get(f'{url}/missing_vehicles', headers=headers)
    soup6 = BeautifulSoup(result6.text, 'lxml')
    more_cars = soup6.find_all('tr', class_='vehicle_select_table_tr')
    print(len(more_cars))
    dict_more_cars = {}
    for t in more_cars:
        dict_more_cars.setdefault(t.get('id'), t.get('vehicle_type'))
    return dict_more_cars


def car_collection(dict_c, task_list, url):
    send_list = []
    for f in task_list:
        www = dict_c.keys()
        for key in www:
            value = dict_c.get(key)
            if (f == M1) and (value == M2 or value == M3) and (key not in send_list):
                send_list.append(key)
                break
            elif f == value and (key not in send_list):
                send_list.append(key)
                break
    if len(send_list) != len(task_list):
        dict_c.update(get_more_cars(url))
        send_list = []
        for f in task_list:
            www = dict_c.keys()
            for key in www:
                value = dict_c.get(key)
                if (f == M1) and (value == M2 or value == M3) and (key not in send_list):
                    send_list.append(key)
                    break
                elif f == value and (key not in send_list):
                    send_list.append(key)
                    break
        if len(send_list) != len(task_list):
            send_list = []
    data_send = {'authenticity_token': token}
    for i in range(len(send_list)):
        send_list[i] = send_list[i][24:]
    data_send['vehicle_ids[]'] = send_list
    return data_send


def get_next_url(soup7):
    next_url = f"https://www.dispetcher112.ru{((soup7.find('div', class_='navbar-header')).find_all('div')[1].find_all('a')[1]).get('href')}"
    next_url = next_url[0:next_url.find('?')-1]
    return next_url


def check_mission_status(mission_list):
    counter = 0
    for url in mission_list:
        counter += 1
        result7 = work.get(url, headers=headers)
        soup7 = BeautifulSoup(result7.text, 'lxml')
        count = get_patients(soup7)
        check_prisoner(soup7, counter)
        if len(count) != 0:
            data2 = car_collection(get_cars(soup7), count, url)
            work.post(f'{url}/alarm', headers=headers, data=data2, allow_redirects=True)
            print('ambulance', counter)
        if get_name(soup7) == True:
            mission_list.remove(url)
    return mission_list


def check_prisoner(soup8, counter):
    prisoner_url = soup8.find_all('a', class_='btn btn-xs btn-danger')
    if len(prisoner_url) != 0:
        prisoner_url = prisoner_url[0].get('href')
        data2 = {'authenticity_token': token}
        work.post(f'https://www.dispetcher112.ru{prisoner_url}', headers=headers, data=data2, allow_redirects=True)
        print("prisoner", counter)


def failed_mission_runner(failed_mission_list, successfully_mission_list):
    count = 0
    for url in failed_mission_list:
        count += 1
        result9 = work.get(url, headers=headers)
        soup9 = BeautifulSoup(result9.text, 'lxml')
        name = get_name(soup9)
        data2 = car_collection(get_cars(soup9), missions_for_game.get(name) + get_patients(soup9), url)
        if len(data2.get('vehicle_ids[]')) != 0:
            work.post(f'{url}/alarm', headers=headers, data=data2, allow_redirects=True)
            print(Fore.GREEN + name, 'failed_mission_successfully :', count)
            failed_mission_list.remove(url)
            successfully_mission_list.append(url)
        else:
            print(Fore.RED + name, "failed :", count)
    return failed_mission_list, successfully_mission_list


run(start_url)
