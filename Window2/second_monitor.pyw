import os
import sys
import time
import tkinter as tk
import ctypes
import subprocess
import threading
from tkinter import *
from tkinter import font
from tkinter import ttk
from tkinter.font import nametofont
from ftplib import FTP
from winreg import *

try:
    import PIL
except ImportError:
    print('Обнаружено отсутствие библиотеки pillow\nНачинаю скачивание...\n\n')
    subprocess.run('pip install pillow')
    subprocess.Popen([sys.executable, *sys.argv])
    time.sleep(1)
    sys.exit(0)
from PIL import Image, ImageTk

try:
    import qrcode
except ImportError:
    print('Обнаружено отсутствие библиотеки qrcode\nНачинаю скачивание...\n\n')
    subprocess.run('pip install qrcode')
    subprocess.Popen([sys.executable, *sys.argv])
    time.sleep(1)
    sys.exit(0)
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask
try:
    import requests
except ImportError:
    print('Обнаружено отсутствие библиотеки requests\nНачинаю скачивание...\n\n')
    subprocess.run('pip install requests')
    subprocess.Popen([sys.executable, *sys.argv])
    time.sleep(1)
    sys.exit(0)
import requests

try:
    import datetime
except ImportError:
    print('Обнаружено отсутствие библиотеки datetime\nНачинаю скачивание...\n\n')
    subprocess.run('pip install datetime')
    subprocess.Popen([sys.executable, *sys.argv])
    time.sleep(1)
    sys.exit(0)

import datetime

day = datetime.datetime.today().isoweekday()
frame_x = 1
frame_y = 1
QR_LIST = []
label_background_8_bit_color = (255, 255, 255)
label_foreground_8_bit_color = tuple((0, 0, 0))
start_color = label_background_8_bit_color
end_color = label_foreground_8_bit_color
duration_ms = 1000
frames_per_second = 60
ms_sleep_duration = 1000 // frames_per_second
current_step = 0
last_time = 0
config_data = {}
PathFile = os.path.abspath(__file__)
ROOT_PATH = PathFile.replace(r'\second_monitor.pyw', '').strip()
IMAGES_PATH = ROOT_PATH + r'\res'
SLIDER_PATH = ROOT_PATH + r'\slider'
SLIDER_PATH_TOP = ROOT_PATH + r'\slider_top'
PATH_TO_FILE = r'C:\output\sm_check.txt'
PATH_TO_SETTINGS = r'C:\output\settings.txt'
# PATH_TO_SETTINGS = fr'{ROOT_PATH}\settings.txt'
thread = None
thread_update = None
host = '78.37.67.153'
PAGE_SECOND_MONITOR = '/vnc_second_monitor/'
PHARMACY_SEC_DICT_KEY = 'pharmacy'
CATEGORY_SEC_DICT_KEY = 'category'
DEVICE_SEC_DICT_KEY = 'device'
BREND_SEC_DICT_KEY = 'brend'
VERSION_SEC_DICT_KEY = 'version'
APP_VERSION = '3.4.3'
start_time = None

try:
    start_time = os.path.getmtime(PathFile)
except Exception:
    pass


class Slider(tk.Canvas):
    def __init__(self, master, imagesg, width=1080, height=1080, delay=5000):
        super().__init__(master, width=width, height=height, bg='black', bd=0, highlightthickness=0)
        self.images = imagesg
        self.delay = delay
        self.current_image = 0
        self.show_image()

    def show_image(self):
        image = self.images[self.current_image]
        self.create_image(0, 0, anchor=tk.NW, image=image, tags="image")
        self.after(self.delay, self.new_image)

    def new_image(self):
        self.delete("image")
        self.current_image = (self.current_image + 1) % len(self.images)
        self.show_image()


def send_data(config_dict: dict):
    url = 'http://' + host + PAGE_SECOND_MONITOR
    requests.post(url, json=config_dict)


def Startup():
    StartupKey = OpenKey(HKEY_CURRENT_USER,
                         r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
                         0, KEY_ALL_ACCESS)
    SetValueEx(StartupKey, 'name', 0, REG_SZ, PathFile)
    CloseKey(StartupKey)


def ftp_updater():
    global thread, thread_update, SLIDER_PATH, day
    now_day = datetime.datetime.today().isoweekday()
    if now_day != day:
        time.sleep(1)
        try:
            thread.cancel()
            thread_update.cancel()
        except Exception:
            pass
        print('close on 169')
        os.execv(sys.executable, ['python'] + [PathFile])
    if not os.path.exists(ROOT_PATH + r'\last_ftp_time.txt'):  # Если нет файла со временем - создаем
        with open(ROOT_PATH + r'\last_ftp_time.txt', 'w') as local_time_file:
            local_time_file.write('0')
    if not os.path.exists(ROOT_PATH + r'\last_ftp_time_sale.txt'):  # Если нет файла со временем - создаем
        with open(ROOT_PATH + r'\last_ftp_time_sale.txt', 'w') as local_time_file_sale:
            local_time_file_sale.write('0')
    if not os.path.exists(ROOT_PATH + r'\last_ftp_time_top.txt'):  # Если нет файла со временем - создаем
        with open(ROOT_PATH + r'\last_ftp_time_top.txt', 'w') as local_time_file_top:
            local_time_file_top.write('0')

    try:
        with open(PATH_TO_SETTINGS) as config:  # Читаем файлы настроек и отправляем данные на сервер
            for field in config:
                sp = field.replace('\n', '').split('=')
                name, val = sp[0].strip(), sp[-1].strip()
                config_data[name] = val
            pharmacy = config_data.get('apteka')
            category = config_data.get('category')
            device = config_data.get('device')
            brend = config_data.get('brend')
            version = APP_VERSION
            second_monitor_dict = {
                PHARMACY_SEC_DICT_KEY: pharmacy,
                CATEGORY_SEC_DICT_KEY: category,
                DEVICE_SEC_DICT_KEY: device,
                BREND_SEC_DICT_KEY: brend,
                VERSION_SEC_DICT_KEY: version
            }

            if brend == 'Nevis' and day == 2:
                SLIDER_PATH = ROOT_PATH + r'\slider_sale'
            elif brend == 'Nevis' and day != 2:
                SLIDER_PATH = ROOT_PATH + r'\slider'
            elif brend == 'LenOblFarm' and day == 5:
                SLIDER_PATH = ROOT_PATH + r'\slider_sale'
            elif brend == 'LenOblFarm' and day != 5:
                SLIDER_PATH = ROOT_PATH + r'\slider'

            if SLIDER_PATH.endswith('sale'):
                with open(ROOT_PATH + r'\last_ftp_time_sale.txt',
                          'r') as local_time_file_sale:  # Читаем время, когда были скачаны файлы с сервера
                    last_ftp_time = int(local_time_file_sale.readline())
            else:
                with open(ROOT_PATH + r'\last_ftp_time.txt',
                          'r') as local_time_file:  # Читаем время, когда были скачаны файлы с сервера
                    last_ftp_time = int(local_time_file.readline())

            with open(ROOT_PATH + r'\last_ftp_time_top.txt',
                      'r') as local_time_file_top:  # Читаем время, когда были скачаны файлы с сервера
                last_ftp_time_top = int(local_time_file_top.readline())
        try:
            send_data(second_monitor_dict)
        except Exception:
            print('Не удалось отправить данные на сервер, следующая попытка через 1 час\n\n')
    except FileNotFoundError:
        print('Файл настроек не найден! Создается при первом входе в РМК. Программа была автоматически закрыта.\n\n')
        time.sleep(1)
        try:
            thread.cancel()
            thread_update.cancel()
        except Exception:
            pass
        print('close on 226')
        sys.exit(0)

    try:
        with FTP(host='mail.nevis.spb.ru', user='2monitor', passwd='WWGFk3Se0d') as ftp:  # Соединяемся с FTP сервером
            if config_data.get('brend') == 'Nevis' and day != 2:  # Если настройка Невис и не вторник
                for name, facts in ftp.mlsd():
                    if name == 'Nevis':
                        servertime = facts.get('modify')  # Узнаем время изменения папки на сервере
                if int(servertime) > last_ftp_time:  # Если время изменения папки на сервере больше, чем последнее время в файле
                    for f in os.listdir(SLIDER_PATH):
                        os.remove(os.path.join(SLIDER_PATH, f))  # Удаляем все файлы
                    ftp.cwd('Nevis')  # Меняем каталог на Невис
                    filenames = ftp.nlst()  # Узнаем список файлов
                    for i in filenames:
                        if i == '.':
                            filenames.remove(i)  # Удаляем папку .
                    for i in filenames:
                        if i == '..':
                            filenames.remove(i)  # Удаляем папку ..
                    for filename in filenames:
                        host_file = os.path.join(SLIDER_PATH, filename)
                        with open(host_file, 'wb') as local_file:
                            ftp.retrbinary('RETR ' + filename, local_file.write)  # Скачиваем файлы
                    for f in os.listdir(SLIDER_PATH):
                        if f == 'Thumbs.db':
                            os.remove(os.path.join(SLIDER_PATH, f))  # Удаляем файл Thumbs.db
                    with open(ROOT_PATH + r'\last_ftp_time.txt',
                              'w') as local_time_file:  # Записываем в файл время скачивания
                        local_time_file.write(str(servertime))
                    time.sleep(1)
                    try:
                        thread.cancel()
                        thread_update.cancel()
                    except Exception:
                        pass
                    print('close on 262')
                    os.execv(sys.executable, ['python'] + [PathFile])
            elif config_data.get('brend') == 'Nevis' and day == 2:  # Если настройка Невис и вторник
                for name, facts in ftp.mlsd():
                    if name == 'NevisSale':
                        servertime = facts.get('modify')  # Узнаем время изменения папки на сервере
                if int(servertime) > last_ftp_time:  # Если время изменения папки на сервере больше, чем последнее время в файле
                    for f in os.listdir(SLIDER_PATH):
                        os.remove(os.path.join(SLIDER_PATH, f))  # Удаляем все файлы
                    ftp.cwd('NevisSale')  # Меняем каталог на Невис распродажа
                    filenames = ftp.nlst()  # Узнаем список файлов
                    for i in filenames:
                        if i == '.':
                            filenames.remove(i)  # Удаляем папку .
                    for i in filenames:
                        if i == '..':
                            filenames.remove(i)  # Удаляем папку ..
                    for filename in filenames:
                        host_file = os.path.join(SLIDER_PATH, filename)
                        with open(host_file, 'wb') as local_file:
                            ftp.retrbinary('RETR ' + filename, local_file.write)  # Скачиваем файлы
                    for f in os.listdir(SLIDER_PATH):
                        if f == 'Thumbs.db':
                            os.remove(os.path.join(SLIDER_PATH, f))  # Удаляем файл Thumbs.db
                    with open(ROOT_PATH + r'\last_ftp_time_sale.txt',
                              'w') as local_time_file:  # Записываем в файл время скачивания
                        local_time_file.write(str(servertime))
                    time.sleep(1)
                    try:
                        thread.cancel()
                        thread_update.cancel()
                    except Exception:
                        pass
                    print('close on 295')
                    os.execv(sys.executable, ['python'] + [PathFile])
            elif config_data.get('brend') == 'LenOblFarm' and day != 5:
                for name, facts in ftp.mlsd():
                    if name == 'LenOblFarm':
                        servertime = facts.get('modify')
                if int(servertime) > last_ftp_time:
                    for f in os.listdir(SLIDER_PATH):
                        os.remove(os.path.join(SLIDER_PATH, f))
                    ftp.cwd('LenOblFarm')
                    filenames = ftp.nlst()
                    for i in filenames:
                        if i == '.':
                            filenames.remove(i)
                    for i in filenames:
                        if i == '..':
                            filenames.remove(i)
                    for filename in filenames:
                        host_file = os.path.join(SLIDER_PATH, filename)
                        with open(host_file, 'wb') as local_file:
                            ftp.retrbinary('RETR ' + filename, local_file.write)
                    for f in os.listdir(SLIDER_PATH):
                        if f == 'Thumbs.db':
                            os.remove(os.path.join(SLIDER_PATH, f))
                    with open(ROOT_PATH + r'\last_ftp_time.txt', 'w') as local_time_file:
                        local_time_file.write(str(servertime))
                    time.sleep(1)
                    try:
                        thread.cancel()
                        thread_update.cancel()
                    except Exception:
                        pass
                    print('close on 327')
                    os.execv(sys.executable, ['python'] + [PathFile])
            elif config_data.get('brend') == 'LenOblFarm' and day == 5:
                for name, facts in ftp.mlsd():
                    if name == 'LenOblFarmSale':
                        servertime = facts.get('modify')
                if int(servertime) > last_ftp_time:
                    for f in os.listdir(SLIDER_PATH):
                        os.remove(os.path.join(SLIDER_PATH, f))
                    ftp.cwd('LenOblFarmSale')
                    filenames = ftp.nlst()
                    for i in filenames:
                        if i == '.':
                            filenames.remove(i)
                    for i in filenames:
                        if i == '..':
                            filenames.remove(i)
                    for filename in filenames:
                        host_file = os.path.join(SLIDER_PATH, filename)
                        with open(host_file, 'wb') as local_file:
                            ftp.retrbinary('RETR ' + filename, local_file.write)
                    for f in os.listdir(SLIDER_PATH):
                        if f == 'Thumbs.db':
                            os.remove(os.path.join(SLIDER_PATH, f))
                    with open(ROOT_PATH + r'\last_ftp_time_sale.txt', 'w') as local_time_file:
                        local_time_file.write(str(servertime))
                    time.sleep(1)
                    try:
                        thread.cancel()
                        thread_update.cancel()
                    except Exception:
                        pass
                    print('close on 359')
                    os.execv(sys.executable, ['python'] + [PathFile])
            # Меняем директорию на корень
            ftp.cwd('..')
            for name, facts in ftp.mlsd():
                if name == 'Top':
                    servertime = facts.get('modify')
            if int(servertime) > last_ftp_time_top:
                for f in os.listdir(SLIDER_PATH_TOP):
                    os.remove(os.path.join(SLIDER_PATH_TOP, f))
                ftp.cwd('Top')
                filenames = ftp.nlst()
                for i in filenames:
                    if i == '.':
                        filenames.remove(i)
                for i in filenames:
                    if i == '..':
                        filenames.remove(i)
                for filename in filenames:
                    host_file = os.path.join(SLIDER_PATH_TOP, filename)
                    with open(host_file, 'wb') as local_file:
                        ftp.retrbinary('RETR ' + filename, local_file.write)
                for f in os.listdir(SLIDER_PATH_TOP):
                    if f == 'Thumbs.db':
                        os.remove(os.path.join(SLIDER_PATH_TOP, f))
                with open(ROOT_PATH + r'\last_ftp_time_top.txt', 'w') as local_time_file_top:
                    local_time_file_top.write(str(servertime))
                time.sleep(1)
                try:
                    thread.cancel()
                    thread_update.cancel()
                except Exception:
                    pass
                print('close on 359')
                os.execv(sys.executable, ['python'] + [PathFile])
    except Exception:
        print('Ошибка при обращении к файловому серверу.\nСледующая попытка через 1 час.\n\n')
    thread = threading.Timer(3600.0, ftp_updater)  # Проверяем каждый час
    thread.start()


def program_updater():
    global start_time, thread_update, thread
    now_time = os.path.getmtime(PathFile)
    if start_time != now_time:
        time.sleep(1)
        try:
            thread.cancel()
            thread_update.cancel()
        except Exception:
            pass
        os.execv(sys.executable, ['python'] + [PathFile])
    else:
        pass
    thread_update = threading.Timer(30.0, program_updater)
    thread_update.start()


program_updater()  # Вызываем функцию проверки обновления скрипта

# Создаем отсутствующие папки
try:
    if not os.path.exists(ROOT_PATH + r'\slider'):
        os.mkdir(ROOT_PATH + r'\slider')
    if not os.path.exists(ROOT_PATH + r'\slider_sale'):
        os.mkdir(ROOT_PATH + r'\slider_sale')
    if not os.path.exists(ROOT_PATH + r'\slider_top'):
        os.mkdir(ROOT_PATH + r'\slider_top')
except Exception:
    pass

ftp_updater()  # Вызываем функцию проверки и скачивания файлов с сервера

# Функции для определения геометрии экранов
user = ctypes.windll.user32


class RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)
    ]

    def dump(self):
        return [int(val) for val in (self.left, self.top, self.right, self.bottom)]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.c_ulong),
        ('rcMonitor', RECT),
        ('rcWork', RECT),
        ('dwFlags', ctypes.c_ulong)
    ]


def get_monitors():
    retval = []
    CBFUNC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(RECT), ctypes.c_double)

    def cb(hMonitor, hdcMonitor, lprcMonitor, dwData):
        r = lprcMonitor.contents
        data = [hMonitor, r.dump()]
        retval.append(data)
        return 1

    cbfunc = CBFUNC(cb)
    temp = user.EnumDisplayMonitors(0, 0, cbfunc, 0)
    return retval


def monitor_areas():
    retval = []
    monitors = get_monitors()
    for hMonitor, extents in monitors:
        data = [hMonitor]
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        mi.rcMonitor = RECT()
        mi.rcWork = RECT()
        res = user.GetMonitorInfoA(hMonitor, ctypes.byref(mi))
        data = mi.rcMonitor.dump()
        retval.append(data)
    return retval


# Анимация цвета текста
def update_treeview_text():
    global current_step
    treeview_purchase.yview_scroll(number=1, what='units')
    t = (1.0 / frames_per_second) * current_step
    current_step += 1

    new_color = interpolate(start_color, end_color, t)
    set_theme('#d6f8ff', '#%02x%02x%02x' % new_color)

    if current_step <= frames_per_second:
        window.after(ms_sleep_duration, update_treeview_text)
    else:
        current_step = 0


# Интерполяция цвета
def interpolate(color_a, color_b, t):
    return tuple(int(k + (b - k) * t) for k, b in zip(color_a, color_b))


# Получает размеры
def size_checker(label):
    global frame_x, frame_y
    window.update_idletasks()
    frame_x = label.winfo_width()
    frame_y = label.winfo_height()


# Делает QR-код
def qr_maker():
    global QR_LIST
    with open(ROOT_PATH + r'\qr.txt', encoding='utf-8') as qr_file:
        href = qr_file.readline().split()
    if href:
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
        qr.clear()
        qr.add_data(href[0])
        img = qr.make_image(image_factory=StyledPilImage,
                            module_drawer=RoundedModuleDrawer(radius_ratio=0),
                            color_mask=RadialGradiantColorMask((255, 255, 255), (226, 32, 33), (15, 161, 225)),
                            embeded_image_path=IMAGES_PATH + r'\logo.png')
        new_img = ImageTk.PhotoImage(img)
        QR_LIST.append(new_img)
        return True
    else:
        QR_LIST.clear()
        return False


# Цвет текста в строках Treeview
def _fixed_map(option, style1):
    return [elm for elm in style1.map("Treeview", query_opt=option) if elm[:2] != ("!disabled", "!selected")]


def set_theme(bg, fg):
    style1 = ttk.Style()
    style1.theme_use("clam")
    style1.map("Treeview", foreground=_fixed_map("foreground", style1), background=_fixed_map("background", style1))
    style1.configure("Treeview", background=bg, fieldbackground=bg, foreground=fg)


# Очищает Treeview
def deleter():
    for iid in id_list:
        treeview_purchase.delete(iid)
    id_list.clear()
    for iid in id_itog:
        treeview_itog.delete(iid)
    id_itog.clear()
    for iid in id_oplat:
        treeview_oplat.delete(iid)
    id_oplat.clear()


# Заполняет Treeview если файл изменился
def writer():
    global last_time
    i = 1  # Нумерация строк
    try:
        t = os.path.getmtime(PATH_TO_FILE)
        if t > last_time:
            deleter()
            thanks_label.pack_forget()
            treeview_purchase.pack(fill='both', expand=True)
            meds = [eval(x) for x in open(PATH_TO_FILE, 'r', encoding='ANSI').read().rstrip('\n').split('\n')]
            for med in meds[:-1]:  # Вставка в чек
                med = list(med)
                med.insert(0, i)
                if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
                    if len(med[1]) > 30:
                        tmp = med[1]
                        string = tmp[:30] + '\n' + tmp[30:]
                        med[1] = string
                else:
                    if len(med[1]) > 23:
                        tmp = med[1]
                        string = tmp[:23] + '\n' + tmp[23:]
                        med[1] = string
                med[2] += ' ₽'
                med[3] += ' шт.'
                med[4] += ' ₽'
                med = tuple(med)
                if i % 2 != 0:
                    id_list.append(treeview_purchase.insert('', END, values=med, tags='first_color'))
                else:
                    id_list.append(treeview_purchase.insert('', END, values=med, tags='second_color'))
                i += 1
            itog_vals = [('  Скидка: ', f'{meds[-1][1]} ₽  '), ('  Итого: ', f'{meds[-1][2]} ₽  ')]
            oplat_vals = [('  К оплате: ', f'{meds[-1][3]} ₽  ')]
            for val in itog_vals:
                id_itog.append(treeview_itog.insert('', END, values=val, tags='TkTextFont'))
            for val in oplat_vals:
                if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
                    id_oplat.append(treeview_oplat.insert('', END, values=val, tags='TkTextFont1'))
                else:
                    id_oplat.append(treeview_oplat.insert('', END, values=val, tags='TkTextFont1.5'))
            cashback_text_label.configure(text=f'С данного чека\n Вам начислен КешБэк: {meds[-1][0]} бон. ₽')
            update_treeview_text()
            last_time = t
    except SyntaxError:
        treeview_purchase.pack_forget()
        thanks_label.pack(fill='both', expand=True)
        cashback_text_label.configure(text='С данного чека\n Вам начислен КешБэк: 0 бон. ₽')
        itog_vals = [('  Скидка: ', '0 ₽  '), ('  Итого:', '0 ₽  ')]
        oplat_vals = [('  К оплате: ', '0 ₽  ')]
        for val in itog_vals:
            id_itog.append(treeview_itog.insert('', END, values=val, tags='TkTextFont'))
        for val in oplat_vals:
            if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
                id_oplat.append(treeview_oplat.insert('', END, values=val, tags='TkTextFont1'))
            else:
                id_oplat.append(treeview_oplat.insert('', END, values=val, tags='TkTextFont1.5'))
    except FileNotFoundError:
        deleter()
        treeview_purchase.pack_forget()
        thanks_label.pack(fill='both', expand=True)
        cashback_text_label.configure(text='С данного чека\n Вам начислен КешБэк: 0 бон. ₽')
        itog_vals = [('  Скидка: ', '0 ₽  '), ('  Итого:', '0 ₽  ')]
        oplat_vals = [('  К оплате: ', '0 ₽  ')]
        for val in itog_vals:
            id_itog.append(treeview_itog.insert('', END, values=val, tags='TkTextFont'))
        for val in oplat_vals:
            if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
                id_oplat.append(treeview_oplat.insert('', END, values=val, tags='TkTextFont1'))
            else:
                id_oplat.append(treeview_oplat.insert('', END, values=val, tags='TkTextFont1.5'))
    window.after(1000, writer)


# Инициализация окон
window = tk.Tk()  # Главное окно


#  Закрыть окно
def close(e):
    thread.cancel()
    thread_update.cancel()
    print('close on 630')
    window.quit()


#  Закрыть окно
def reboot(x):
    time.sleep(1)
    thread.cancel()
    thread_update.cancel()
    os.execv(sys.executable, ['python'] + [PathFile])


# Установка размеров окон и смещение на второй монитор
try:
    if abs(monitor_areas()[1][0]) == 1080:  # Вертикальное положение
        window.geometry(f'{abs(monitor_areas()[1][0])}x{monitor_areas()[1][3]}-{monitor_areas()[0][2]}+0')
    elif abs(monitor_areas()[0][0]) == 1080:
        window.geometry(f'{abs(monitor_areas()[0][0])}x{monitor_areas()[0][3]}-{monitor_areas()[1][2]}+0')
    elif abs(monitor_areas()[1][0]) == 1920:  # Горизонтальное положение
        window.geometry(f'{abs(monitor_areas()[1][0])}x{monitor_areas()[1][3]}-{monitor_areas()[0][2]}+0')
    elif abs(monitor_areas()[0][0]) == 1920:
        window.geometry(f'{abs(monitor_areas()[0][0])}x{monitor_areas()[0][3]}-{monitor_areas()[1][2]}+0')
except IndexError:
    print('Ошибка! Второй монитор не обнаружен.\n\nПрограмма была автоматически закрыта.\n\n')
    try:
        thread.cancel()
        thread_update.cancel()
    except Exception:
        pass
    print('close on 658')
    sys.exit(0)

list_fonts = list(font.families())

# Проверка на установку шрифтов
if 'Montserrat' not in list_fonts:
    print(
        f'Ошибка! Не установлен шрифт "Montserrat"\n\nУстановите шрифт из папки: {ROOT_PATH}\n\nПрограмма была автоматически закрыта.\n\n')
    try:
        thread.cancel()
        thread_update.cancel()
    except Exception:
        pass
    sys.exit(0)
if 'Montserrat Medium' not in list_fonts:
    print(
        f'Ошибка! Не установлен шрифт "Montserrat Medium"\n\nУстановите шрифт из папки: {ROOT_PATH}\n\nПрограмма была автоматически закрыта.\n\n')
    try:
        thread.cancel()
        thread_update.cancel()
    except Exception:
        pass
    print('close on 681')
    sys.exit(0)

# Заголовки окон
window.title('')

# Стили окон
window.overrideredirect(True)  # Убиваем титлбар
window.after_idle(window.attributes, '-topmost', True)  # Главное окно поверх всех окон
window.state('zoomed')  # Главное окно на весь экран
window.resizable(False, False)  # Запрет изменения размера

id_list = []  # Список id для Treeview_purchase
id_itog = []  # Список id для Treeview_itog
id_oplat = []  # Список id для Treeview_oplat

#  Фрейм во все главное окно
main_window = tk.Frame(window, bg='black')
main_window.pack(fill='both', expand=True)

#  Фрейм левый
if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
    frame_left = tk.Frame(main_window, borderwidth="0", background='#d6f8ff', height=840, padx=15, pady=15)
    frame_left.pack(fill='both', side="top", expand=True)
    frame_left.pack_propagate(False)
else:
    frame_left = tk.Frame(main_window, borderwidth="0", width=890, padx=15, pady=15, background='#d6f8ff')
    frame_left.pack(fill='both', side="left", expand=True)
    frame_left.pack_propagate(False)

# Оформление Treeview
style = ttk.Style()
style.theme_use('clam')
style.configure('Treeview.Heading', font=('Montserrat', 23), background='#32beec',
                foreground='black', relief='flat')  # Стиль заголовков таблицы
style.map('Treeview', background=[('selected', 'black')])
style.configure('Treeview', foreground='black', background='#d6f8ff', fieldbackground='#d6f8ff',
                rowheight=80)  # Стиль строк таблицы
style.configure('New.Treeview', foreground='black', background='#d6f8ff', fieldbackground='#d6f8ff',
                rowheight=50)
style.configure('New1.Treeview', foreground='black', background='#d6f8ff', fieldbackground='#d6f8ff',
                rowheight=100)
style.layout("Treeview", [
    ('Treeview.treearea', {'sticky': 'nswe'})
])
nametofont("TkDefaultFont").configure(size=19, family='Montserrat Medium')  # Стиль текста

#  Таблица чека
frame_for_treeview = tk.Frame(frame_left)  # Фрейм для таблицы чека
frame_for_treeview.pack(fill='both', expand=True)

thanks_label = tk.Label(frame_for_treeview, text='Спасибо за покупку!', background='#d6f8ff', justify='center',
                        anchor='center', font=('Montserrat', 40), height=9)

columns = ('nom', 'name', 'cost', 'count', 'sum')  # Инициализация столбиков
if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
    treeview_purchase = ttk.Treeview(frame_for_treeview, height=6, padding=0, columns=columns, show='headings')
else:
    treeview_purchase = ttk.Treeview(frame_for_treeview, height=8, padding=0, columns=columns, show='headings')
treeview_purchase.tag_configure('first_color', background='#d6f8ff')
treeview_purchase.tag_configure('second_color', background='white')
treeview_purchase.pack(fill='both', expand=True)
treeview_purchase.heading('nom', text='№')
treeview_purchase.heading('name', text='Наименование')
treeview_purchase.heading('cost', text='Цена')
treeview_purchase.heading('count', text='Кол-во')
treeview_purchase.heading('sum', text='Сумма')
if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
    treeview_purchase.column('#1', width=60, stretch=NO, anchor='c')
    treeview_purchase.column('#2')
    treeview_purchase.column('#3', width=155, stretch=NO, anchor='c')
    treeview_purchase.column('#4', width=215, stretch=NO, anchor='c')
    treeview_purchase.column('#5', width=160, stretch=NO, anchor='c')
else:
    treeview_purchase.column('#1', width=60, stretch=NO, anchor='c')
    treeview_purchase.column('#2')
    treeview_purchase.column('#3', width=155, stretch=NO, anchor='c')
    treeview_purchase.column('#4', width=125, stretch=NO, anchor='c')
    treeview_purchase.column('#5', width=155, stretch=NO, anchor='c')

#  Таблица итогов
columns1 = ('first', 'second')  # Инициализация столбиков
treeview_itog = ttk.Treeview(frame_left, show='', columns=columns1, height=2, style='New.Treeview')
treeview_itog.tag_configure('TkTextFont', font=('Montserrat', 25), background='white')

cashback_text_label = tk.Label(frame_left, background='#f79400', foreground='black', font=('Montserrat', 28),
                               justify='center')
cashback_text_label.pack(fill=X, side="top", expand=True, anchor='n', ipady=5)

treeview_itog.pack(fill=X, side="left", expand=True, anchor='s')
if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
    treeview_itog.column('#1', width=70, stretch=YES, anchor='w')
    treeview_itog.column('#2', width=100, stretch=YES, anchor='e')
else:
    treeview_itog.column('#1', width=180, stretch=NO, anchor='w')
    treeview_itog.column('#2', width=215, stretch=NO, anchor='w')

buffer_label = ttk.Label(frame_left, background='#d6f8ff', width=1)
buffer_label.pack(fill=X, side='left', expand=True)

#  Таблица оплата
columns2 = ('fir', 'sec')  # Инициализация столбиков
treeview_oplat = ttk.Treeview(frame_left, show='', columns=columns2, height=1, style='New1.Treeview')
treeview_oplat.tag_configure('TkTextFont1', font=('Montserrat', 32), foreground='black', background='#32beec')
treeview_oplat.tag_configure('TkTextFont1.5', font=('Montserrat', 27), foreground='black', background='#32beec')
treeview_oplat.pack(fill=X, side="left", expand=True)
if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
    treeview_oplat.column('#1', width=120, stretch=YES, anchor='w')
    treeview_oplat.column('#2', width=120, stretch=YES, anchor='e')
else:
    treeview_oplat.column('#1', width=213, stretch=NO, anchor='w')
    treeview_oplat.column('#2', width=100, stretch=YES, anchor='e')

#  Фрейм правый
if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
    frame_right = tk.Frame(main_window, borderwidth="0", background='#d6f8ff', height=1080)
    frame_right.pack(fill='both', side="top", expand=True)
else:
    frame_right = tk.Frame(main_window, borderwidth="0", background='#d6f8ff', width=1080)
    frame_right.pack(fill='both', side="left", expand=True)


#  Лейбл оплата по QR
label_qr = tk.Label(frame_right,
                    font=('Montserrat', 23), background='#d6f8ff',
                    borderwidth="0",
                    relief="flat",
                    anchor="center",
                    text="ВЫ МОЖЕТЕ ОПЛАТИТЬ ПОКУПКУ ПО QR:",
                    fg='black',
                    pady=15)

window.update_idletasks()

#  Лейбл со слайдером
image_files = []
files = os.listdir(SLIDER_PATH)

for file in files:
    a = os.path.join(SLIDER_PATH, file)
    image_files.append(a)

resize_image_files = []
resize_big_image_files = []
im = Image.open(IMAGES_PATH + r'\default_slide_back1_vertical.png')
default_slide_back = ImageTk.PhotoImage(im)
brend = config_data.get('brend')
if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
    im2 = Image.open(IMAGES_PATH + r'\default_slide_back1_vertical.png')
else:
    im2 = Image.open(IMAGES_PATH + r'\default_slide_back1_vertical.png')
default_big_slide_back = ImageTk.PhotoImage(im2)

for file in os.listdir(SLIDER_PATH_TOP):
    img = PIL.Image.open(os.path.join(SLIDER_PATH_TOP, file))
    wid = img.size[0]
    if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
        if wid >= 1079:
            im3 = img
        else:
            continue
    else:
        if wid <= 841:
            im3 = img
        else:
            continue

if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
    label_big_slides = tk.Label(main_window, width=1080, background='black')  # Лейбл под слайдер в простое
else:
    label_big_slides = tk.Label(main_window, width=1080, background='black')  # Лейбл под слайдер в простое
try:
    default_cashback = ImageTk.PhotoImage(im3)
except Exception:
    if brend == 'Nevis':
        if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
            im3 = Image.open(IMAGES_PATH + r'\KOMAR1080840.png')
        else:
            im3 = Image.open(IMAGES_PATH + r'\KOMAR8401080.png')
    elif brend == 'LenOblFarm':
        if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
            im3 = Image.open(IMAGES_PATH + r'\KOMAR1080840.png')
        else:
            im3 = Image.open(IMAGES_PATH + r'\KOMAR8401080.png')
    default_cashback = ImageTk.PhotoImage(im3)


# Подгон размеров фоток под лейбл (фрейм)
def resize():
    global resize_image_files
    for image in image_files:
        b = Image.open(image)
        if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
            new = b.resize((1080, 1080))
        else:
            new = b.resize((1040, 1080))
        new1 = ImageTk.PhotoImage(new)
        resize_image_files.append(new1)


def resize_big():
    global resize_big_image_files
    for image in image_files:
        b = Image.open(image)
        new = b.resize((1080, 1080))
        new1 = ImageTk.PhotoImage(new)
        resize_big_image_files.append(new1)


resize()
resize_big()

cashback_label = tk.Label(main_window, height=840, image=default_cashback, bg='black')


def check_display_mode():
    global resize_big_image_files
    if not id_list:
        frame_right.pack_forget()
        frame_left.pack_forget()
        if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
            cashback_label.pack(fill='both', expand=True)
            slider.pack(fill='both', expand=True)
        else:
            slider.pack(fill='both', side='left', expand=True)
            cashback_label.pack(fill='both', side='left', expand=True)
    else:
        cashback_label.pack_forget()
        slider.pack_forget()
        main_window.pack_forget()
        main_window.pack(fill='both', expand=True)
        if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
            frame_left.pack(fill='both', side="top", expand=True)
            frame_right.pack(fill='both', side="top", expand=True)
        else:
            frame_left.pack(fill='both', side="left", expand=True)
            frame_right.pack(fill='both', side="left", expand=True)
    window.after(3000, check_display_mode)


try:
    Startup()
except Exception:
    pass
window.bind('<Control-Alt-w>', close)
window.bind('<Control-Alt-r>', reboot)
slider = Slider(main_window, resize_big_image_files)
slider2 = Slider(frame_right, resize_image_files)
slider2.pack()
check_display_mode()
writer()
window.mainloop()