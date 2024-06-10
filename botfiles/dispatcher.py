import json
import os
import signal
import time
import re
import pickle
import logging
import configparser
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from requests import Session
from vehicle import *
from car import Car
from mission import Mission
from collections import Counter

# init
config = configparser.ConfigParser()
headers = {'User-Agent': UserAgent().random}
work = Session()

logging.basicConfig(level=logging.INFO, filename='dispatcher.log', filemode='w')


def config_read():
    now_os = os.getcwd()
    now_os = os.path.join(now_os, '..', 'config')
    config.read(f'{now_os}\\config.ini')
    u = config['data']['username']
    p = config['data']['password']
    t = int(config['configurations']['generation_rate']) // 2
    a = True if (config['configurations']['alliance_missions']) == 'True' else False
    return u, p, t, a


def register():
    try:
        work.get('https://www.dispetcher112.ru/', headers=headers)
        response = work.get('https://www.dispetcher112.ru/users/sign_in', headers=headers)
        soup = BeautifulSoup(response.text, 'lxml')
        token = soup.find('form').findAll('input')
        token = token[1].get('value')
        datap = {'authenticity_token': token,
                 'user[email]': username,
                 'user[password]': password,
                 'user[remember_me]': 0}
        res = work.post('https://www.dispetcher112.ru/users/sign_in', headers=headers, data=datap, allow_redirects=True)
        soup = BeautifulSoup(res.text, 'lxml')
        token = soup.findAll('input')
        token = token[4].get('value')
        return token
    except:
        print('login is failed')


# мед контроль
# class Mission2(Mission):
#
#     def __init__(self, mission_instance, ambulance_count):
#         super().__init__(mission_instance.name, mission_instance.ID, mission_instance.send_list,
#                          mission_instance.send_dict, mission_instance.status, mission_instance.patients)
#         self.soup = BeautifulSoup((work.get('https://www.dispetcher112.ru/', headers=headers)).text, 'lxml')
#         self.dict_cars = {}
#         self.send_list = []
#         self.send_dict = []
#         self.ambulance_count = ambulance_count
#         self.dict_cars_need = {'Необходим автомобиль мед. координатора': '1',
#                                'Требуемые скорые': self.ambulance_count}
#         self.send_ambulance()
#
#     def check_status(self):
#         if self.status == 'fire_rot':
#             pass
#         elif self.status == 'fire_gelb':
#             pass
#         elif self.status == 'fire_gruen':
#             pass
#
#     def get_cars(self):
#         cars = self.soup.find_all('tr', class_='vehicle_select_table_tr')
#         for t in cars:
#             self.dict_cars.setdefault(t.find('input').get('value'), t.get('vehicle_type'))
#
#     # добавляем ТС если не хватило
#     def get_more_cars(self):
#         soup = work.get(f'https://www.dispetcher112.ru/missions/{self.ID}/missing_vehicles')
#         soup = BeautifulSoup(soup.text, 'lxml')
#         more_cars = soup.find_all('tr', class_='vehicle_select_table_tr')
#         for t in more_cars:
#             self.dict_cars.setdefault(t.find('input').get('value'), t.get('vehicle_type'))
#
#     def send_ambulance(self):
#         self.get_cars()
#         self.picker()
#         if len(self.send_list) - 1 < int(self.ambulance_count):
#             self.send_list = []
#             self.get_more_cars()
#             self.picker()
#         data2 = {
#             "utf8": "✓",
#             "authenticity_token": token,
#             'vehicle_ids[]': self.send_dict
#         }
#         work.post(f'https://www.dispetcher112.ru/missions/{self.ID}/alarm',
#                   headers=headers, data=data2, allow_redirects=True)
#
#     def picker(self):
#         w = self.dict_cars_need.keys()
#         t = self.dict_cars.keys()
#         for key in w:
#             count = int(self.dict_cars_need.get(key))
#             mnojectvo = vehicle.get(key)
#             for _ in range(count):
#                 for y in t:
#                     key2 = self.dict_cars.get(y)
#                     if (key2 in mnojectvo) and y not in self.send_dict:
#                         self.send_list.append(key2)
#                         self.send_dict.append(y)
#                         break
class Mission2:

    def __init__(self, MS):
        self.MS = MS
        self.soup = BeautifulSoup((work.get('https://www.dispetcher112.ru/', headers=headers)).text, 'lxml')
        self.dict_cars = {}
        self.send_list = []
        self.send_dict = []
        self.dict_cars_need = {'Необходим автомобиль мед. координатора': 1,
                               'Требуемые скорые': MS.patients}

    # def check_status(self):
    #     if self.status == 'fire_rot':
    #         pass
    #     elif self.status == 'fire_gelb':
    #         pass
    #     elif self.status == 'fire_gruen':
    #         pass

    def get_cars(self):
        cars = self.soup.find_all('tr', class_='vehicle_select_table_tr')
        for t in cars:
            self.dict_cars.setdefault(t.find('input').get('value'), t.get('vehicle_type'))
        if len(self.dict_cars) == 0:
            logging.critical(f'NO_Medical_Cars {self.MS.ID}')

    # добавляем ТС если не хватило
    def get_more_cars(self):
        soup = work.get(f'https://www.dispetcher112.ru/missions/{self.MS.ID}/missing_vehicles')
        soup = BeautifulSoup(soup.text, 'lxml')
        more_cars = soup.find_all('tr', class_='vehicle_select_table_tr')
        for t in more_cars:
            self.dict_cars.setdefault(t.find('input').get('value'), t.get('vehicle_type'))

    def send_ambulance(self):
        self.get_cars()
        self.picker()
        if len(self.send_list) - 1 < int(self.MS.patients):
            self.send_list = []
            self.get_more_cars()
            self.picker()
        data2 = {
            "utf8": "✓",
            "authenticity_token": token,
            'vehicle_ids[]': self.send_dict
        }
        work.post(f'https://www.dispetcher112.ru/missions/{self.MS.ID}/alarm',
                  headers=headers, data=data2, allow_redirects=True)
        logging.info(f'Medical send {self.MS.ID, self.send_list, self.send_dict}')
        return self.send_list, self.send_dict

    def picker(self):
        w = self.dict_cars_need.keys()
        t = self.dict_cars.keys()
        for key in w:
            count = int(self.dict_cars_need.get(key))
            mnojectvo = vehicle.get(key)
            for _ in range(count):
                for y in t:
                    key2 = self.dict_cars.get(y)
                    if (key2 in mnojectvo) and y not in self.send_dict:
                        self.send_list.append(key2)
                        self.send_dict.append(y)
                        break

# обработка задания
class Generate:
    def __init__(self, ID, name, status, patients):
        self.change_os = None
        self.flag = True
        self.dict_cars_need = {}
        self.dict_cars = {}
        self.send_list = []
        self.send_dict = []
        self.ID = ID
        self.name = name
        self.status = status
        self.soup = BeautifulSoup((work.get(f"https://www.dispetcher112.ru/missions/{self.ID}", headers=headers)).text, 'lxml')
        self.patients = patients
        self.check_name()

    def claim(self):
        s = self.soup.find_all('a', id='easter-egg-link')
        if len(s) != 0:
            work.post(f'https://www.dispetcher112.ru/missions/{self.ID}/claim_found_object_sync', headers=headers,
                      data=data)

    # получаем имя
    def check_name(self):
        self.name = self.name.replace('(Система пожарной тревоги)', '').replace('/', '').replace('', '') \
            .replace(',', '').replace(' ', '')
        dp.data[self.ID][0] = self.name

    # мы смотрим есть ли config файл с такой миссией,  альше запускаем сборщик транспорта
    def send_cars(self):
        self.change_os = os.path.join(os.getcwd(), "..", "json")
        if not os.path.isfile(self.change_os + f"\\{self.name}.json"):
            self.task_requirements()
        with open(f"{self.change_os}\\{self.name}.json", 'r') as f:
            f = f.read()
        self.dict_cars_need = json.loads(f)
        self.claim()
        time.sleep(time_sleep)
        self.get_cars()
        self.picker()
        if not self.flag:
            self.flag = True
            self.get_more_cars()
            self.send_list = []
            self.send_dict = []
            self.picker()
        # отсюда отправка

        if self.flag:
            data2 = {
                "utf8": "✓",
                "authenticity_token": token,
                'vehicle_ids[]': self.send_dict
            }
            work.get(f'https://www.dispetcher112.ru/missions/{self.ID}/alliance', headers=headers)
            work.post(f'https://www.dispetcher112.ru/missions/{self.ID}/alarm', headers=headers,
                      data=data2, allow_redirects=True)
            dp.missions_ok.append(
                Mission(self.name, self.ID, self.status, self.patients, self.send_list, self.send_dict))
            logging.info(f'Mission_cars_send { self.ID, self.name, self.send_list}')
            print(self.name, self.send_list)
            time.sleep(time_sleep)
        else:
            print('Mиссия провалена', self.name, self.ID)
            logging.info(f'Failed_mission{self.ID, self.name}')

    # получаем ТС со страницы
    def get_cars(self):
        cars = self.soup.find_all('tr', class_='vehicle_select_table_tr')

        for t in cars:
            self.dict_cars.setdefault(t.find('input').get('value'), t.get('vehicle_type'))
        if len(self.dict_cars) == 0:
            logging.critical(f'NO_Cars{self.ID}')

    # добавляем ТС если не хватило
    def get_more_cars(self):
        soup = work.get(f'https://www.dispetcher112.ru/missions/{self.ID}/missing_vehicles')
        soup = BeautifulSoup(soup.text, 'lxml')
        more_cars = soup.find_all('tr', class_='vehicle_select_table_tr')
        for t in more_cars:
            self.dict_cars.setdefault(t.find('input').get('value'), t.get('vehicle_type'))


    # выдача пациентов
    def get_patients(self):
        if self.patients == 0:
            return {}
        else:
            return {'Необходим автомобиль мед. координатора': 1, 'Требуемые скорые': 1 * self.patients}
        # patients = self.soup.find_all('div', class_='col-sm-4 col-xs-6 mission_patient')
        # return ['Машина Скорой Помощи'] * len(patients)

    ## очень громоздкая херня

    def picker(self):
        med = self.get_patients()
        self.dict_cars_need = dict(Counter(med) + Counter(self.dict_cars_need))
        w = self.dict_cars_need.keys()
        t = self.dict_cars.keys()
        water = 0
        foam = 0
        fire_car = 0
        kombat = 0
        police_car = 0
        swat = 0
        for key in w:
            count = self.dict_cars_need.get(key)
            mnojectvo = vehicle.get(key)
            logging.debug(f'Picker{key, mnojectvo}')
            if key in ('Требуется вода', 'Требуется пена', 'Требуемый персонал спецназа (в машинах спецназа)'):
                for y in t:
                    key2 = self.dict_cars.get(y)
                    if (key2 in mnojectvo) and y not in self.send_dict:
                        key2 = Car(key2)
                        key2.cargo()
                        water += key2.water
                        foam += key2.foam
                        fire_car += key2.fire_car
                        kombat += key2.kombat
                        police_car += key2.police_car
                        swat += key2.swat
                        self.send_list.append(key2.name)
                        self.send_dict.append(y)
                    match key:
                        case 'Требуется вода' if count - water <= 0:
                            break
                        case 'Требуется пена' if count - foam <= 0:
                            break
                        case 'Требуемый персонал спецназа (в машинах спецназа)' if count - swat <= 0:
                            break
                match key:
                    case 'Требуется вода' if count - water > 0:
                        self.flag = False
                        break
                    case 'Требуется пена' if count - foam > 0:
                        self.flag = False
                        break
                    case 'Требуемый персонал спецназа (в машинах спецназа)' if count - swat > 0:
                        self.flag = False
                        break
            else:
                match key:
                    case 'Требуемые пожарные машины':
                        count = count - fire_car
                    case 'Требуемые машины командира батальона':
                        count = count - kombat
                    case 'Автомобиль с полицейской собакой':
                        count = count - police_car
                cc = 0
                for _ in range(count):
                    for y in t:
                        key2 = self.dict_cars.get(y)
                        if (key2 in mnojectvo) and y not in self.send_dict:
                            cc += 1
                            key2 = Car(key2)
                            water += key2.water
                            foam += key2.foam
                            fire_car += key2.fire_car
                            kombat += key2.kombat
                            police_car += key2.police_car
                            swat += key2.swat
                            self.send_list.append(key2.name)
                            self.send_dict.append(y)
                            break
                if count - cc > 0:
                    self.flag = False
                    break

    # сбор требований миссии
    def task_requirements(self):
        trhref = self.soup.find('a', class_='btn btn-default btn-xs navbar-btn hidden-xs').get('href')
        sp = BeautifulSoup((work.get(f'https://www.dispetcher112.ru{trhref}', headers=headers)).text, 'lxml')
        sp = sp.findAll('tbody')
        sp1 = sp[1]
        sp1 = sp1.findAll('td')
        sp2 = sp[2]
        sp2 = sp2.findAll('td')
        d = {}
        for qq in range(0, len(sp1) - 1, 2):
            text = sp1[qq].get_text().strip()
            count = int((sp1[qq + 1]).get_text().strip())
            if (text.find('Вероятность') and text.find('Обычный минимум Личный состав пожарных')) == -1:
                d.setdefault(text, count)
        for key in vehicle_to_find:
            if key in d:
                r = d.pop(key)
                d.setdefault(key, r)

        # for qqq in range(0, len(sp2) - 1, 2):
        #     text = sp2[qqq].get_text().strip()
        #     if text == "Минимальное число пациентов":
        #         count = (sp2[qqq + 1]).get_text().strip()
        #         if 'Требуемые скорые' in d:
        #             d['Требуемые скорые'] = str(int(d['Требуемые скорые']) + int(count))
        #             d.setdefault('Необходим автомобиль мед. координатора', '1')
        #         else:
        #             d.setdefault('Требуемые скорые', str(count))
        #             d.setdefault('Не обходим автомобиль мед. координатора', '1')
        print('Сохранено', d)
        logging.info(f'Save{self.name, d}')
        dt = self.change_os + f"\\{self.name}.json"
        with open(dt, 'w') as json_file:
            json.dump(d, json_file)


# главный механизм
class Dispatcher:

    def __init__(self):
        self.soup = None
        self.data = {}
        self.missions = []
        self.missions_ok = []
        self.load_file()

    def get_soup(self):
        self.soup = BeautifulSoup((work.get('https://www.dispetcher112.ru/', headers=headers)).text, 'lxml')

    def scan(self):
        self.soup = self.soup.find_all('script')[12]
        pattern = re.compile(r'missionMarkerAdd\((.*?)\);', re.DOTALL)
        matches = pattern.findall(self.soup.text)
        for match in matches:
            json_str = match
            data2 = json.loads(json_str)
            if not alliance_missions:
                if data2.get('alliance_id') is None:
                    self.data[data2.get('id')] = [data2.get('caption'), data2.get('icon'),
                                                  data2.get('prisoners_count'), data2.get('patients_count')]
                    self.missions.append(data2.get('id'))
            else:
                self.data[data2.get('id')] = [data2.get('caption'), data2.get('icon'),
                                              data2.get('prisoners_count'), data2.get('patients_count')]
                self.missions.append(data2.get('id'))

        logging.info(f'Start {self.missions}')

    def load_file(self):
        try:
            change_os = os.path.join(os.getcwd(), '..', 'config')
            with open(f'{change_os}\\data.json', 'r') as f, open(f'{change_os}\\missions.pkl', 'rb') as f2:
                # self.data = json.load(f)
                m = json.load(f)
                self.missions_ok = pickle.load(f2)
        except:
            logging.warning("Error_Loading_file")
            print('Error_Loading')

    def save_file(self, signal, frame):
        change_os = os.path.join(os.getcwd(), '..', 'config')
        try:
            with open(f'{change_os}\\data.json', 'w') as f, open(f'{change_os}\\missions.pkl', 'wb') as f2:
                json.dump(self.data, f)
                pickle.dump(self.missions_ok, f2)
        except Exception as e:
            logging.warning(f'Error_Uploading {e}')
            print("Ошибка при сохранении файлов:", e)

    def management(self):
        self.missions = []
        # data1 = {}
        # for i in self.missions_ok:
        #     data1.setdefault(i.ID, self.data.get(i.ID))
        self.get_soup()
        self.scan()
        self.missions_ok = [i for i in self.missions_ok if i.ID in self.missions]
        for i in self.missions_ok:
            try:
                self.missions.remove(i.ID)
            except ValueError:
                pass
        for i in self.missions_ok:
            try:
                if self.data.get(i.ID)[3] > i.patients:
                    time.sleep(3)
                    logging.info(f'NEW_MED{i.ID}')
                    i.patients = self.data.get(i.ID)[3]
                    a, b = Mission2(i).send_ambulance()
                    print(i.name, a)
                    i.send_list.append(a)
                    i.send_dict.append(b)
                elif self.data.get(i.ID) != 0:
                    logging.info(f'Prisoner{i.ID}')
                    work.post(f'https://www.dispetcher112.ru/missions/{i.ID}/gefangene/entlassen',
                              headers=headers, data=data)
                    time.sleep(3)
            except TypeError:
                logging.critical(f"TypeError{i.ID}")
            except ValueError:
                logging.critical(f"ValueError{i.ID}")
        print(len(self.missions_ok), len(self.missions))
        logging.info(f'Next round{len(self.missions), self.missions}')
        for ms in self.missions:
            try:
                j = Generate(ms, self.data.get(ms)[0], self.data.get(ms)[1], self.data.get(ms)[3])
                j.send_cars()
            except TypeError:
                print("Миссия не поддерживается", 'Парашютист на дереве')


# run
username, password, time_sleep, alliance_missions = config_read()
token = register()
data = {'authenticity_token': token}
dp = Dispatcher()
try:
    while 1:
        dp.management()
except KeyboardInterrupt:
    print('Вы успешно выключили бота')
    logging.info('complete work')
    dp.save_file(signal.SIGINT, None)
except Exception as e:
    print('Завершение работы', e)
    logging.info(f'work completed with problems {e}')
    dp.save_file(signal.SIGINT, None)
