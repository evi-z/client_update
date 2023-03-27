import os
import socket
import sys
import time
import tkinter as tk
import ctypes
import subprocess
import threading
from tkinter import *
from tkinter import font
from tkinter import ttk
from itertools import cycle
from tkinter.font import nametofont
from ftplib import FTP
from winreg import *
import requests

# def is_admin():
#     try:  # Пытаемся вернуть True admin-mode
#         return ctypes.windll.shell32.IsUserAnAdmin()
#     except:  # Иначе возвращаем False
#         return False
#
#
# def path_to_script_with_space():
#     path_to_script = sys.argv[0]  # Пусть к скрипту
#
#     if ' ' in path_to_script:  # Если есть пробелы в пути
#         return True
#     else:
#         return False
#
#
# def get_correct_path():
#     if path_to_script_with_space():  # Если в пути есть пробелы
#         path_to_script = f'"{sys.argv[0]}"'  # Пишем в кавычках
#     else:
#         path_to_script = sys.argv[0]  # Возвращаем как есть
#
#     return path_to_script
#
#
# if not is_admin():
#     path_to_client = get_correct_path()  # Получаем корректный путь до скрипта
#     arg = sys.argv[1:]  # Аргументы командной строки
#
#     argv_to_ex = [path_to_client]  # Список для ShellExecuteW
#     if arg:  # Если есть аргументы - добавляем
#         argv_to_ex.extend(arg)
#
#     # Перезапускаем интерпретатор с правами админа
#     ctypes.windll.shell32.ShellExecuteW(0, 'runas', sys.executable, ' '.join(argv_to_ex), None, 1)
#     sys.exit(0)  # Завершаем работу этого скрипта


try:
    import PIL
except ImportError:
    print('\n\nОбнаружено отсутствие библиотеки pillow\nНачинаю скачивание...')
    subprocess.run('pip install pillow')
    # os.execv(sys.executable, [sys.executable] + sys.argv)
    subprocess.Popen([sys.executable, *sys.argv])
    time.sleep(1)
    sys.exit(0)

from PIL import Image, ImageTk

try:
    import qrcode
except ImportError:
    print('\n\nОбнаружено отсутствие библиотеки qrcode\nНачинаю скачивание...')
    subprocess.run('pip install qrcode')
    # os.execv(sys.executable, [sys.executable] + sys.argv)
    subprocess.Popen([sys.executable, *sys.argv])
    time.sleep(1)
    sys.exit(0)

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask

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
ROOT_PATH = PathFile.replace(r'\second_monitor.py', '').strip()
IMAGES_PATH = ROOT_PATH + r'\res'
SLIDER_PATH = ROOT_PATH + r'\slider'
PATH_TO_FILE = r'C:\output\sm_check.txt'
PATH_TO_SETTINGS = r'C:\output\settings.txt'
# PATH_TO_FILE = fr'{ROOT_PATH}\test.txt'
thread = None
thread_update = None
host = '78.37.67.153'
PAGE_SECOND_MONITOR = '/vnc_second_monitor/'
PHARMACY_SEC_DICT_KEY = 'pharmacy'
CATEGORY_SEC_DICT_KEY = 'category'
DEVICE_SEC_DICT_KEY = 'device'
BREND_SEC_DICT_KEY = 'brend'
VERSION_SEC_DICT_KEY = 'version'
APP_VERSION = '1.8'
start_time = None

print(
    '\n\nПожалуйста, не закрывайте данное окно!\n\nОно отвечает за работу программы второго монитора\n\nВы можете свернуть данное окно')

try:
    start_time = os.path.getmtime(PathFile)
except Exception:
    pass


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
    global thread, thread_update
    if not os.path.exists(ROOT_PATH + r'\last_ftp_time.txt'):  # Если нет файла со временем - создаем
        with open(ROOT_PATH + r'\last_ftp_time.txt', 'w') as local_time_file:
            local_time_file.write('0')
    with open(ROOT_PATH + r'\last_ftp_time.txt',
              'r') as local_time_file:  # Читаем время, когда были скачаны файлы с сервера
        last_ftp_time = int(local_time_file.readline())

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
            try:
                send_data(second_monitor_dict)
            except Exception:
                print('Не удалось отправить данные на сервер, следующая попытка через 1 час')
    except FileNotFoundError:
        print('\nФайл настроек не найден! Создается при первом входе в РМК. Программа будет закрыта через 15 сек.')
        time.sleep(15.0)
        sys.exit(0)

    try:
        with FTP(host='mail.nevis.spb.ru', user='2monitor', passwd='WWGFk3Se0d') as ftp:  # Соединяемся с FTP сервером
            if config_data.get('brend') == 'Nevis':  # Если настройка Невис
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
                    # os.execv(sys.executable, [sys.executable] + sys.argv)  # Перезапускаемся если скачали новые файлы
                    subprocess.Popen([sys.executable, *sys.argv])
                    time.sleep(1)
                    try:
                        thread.cancel()
                        thread_update.cancel()
                    except Exception:
                        pass
                    sys.exit(0)
            elif config_data.get('brend') == 'LenOblFarm':
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
                    # os.execv(sys.executable, [sys.executable] + sys.argv)
                    subprocess.Popen([sys.executable, *sys.argv])
                    time.sleep(1)
                    try:
                        thread.cancel()
                        thread_update.cancel()
                    except Exception:
                        pass
                    sys.exit(0)
    except Exception:
        print('\n\nОшибка при обращении к файловому серверу.\nСледующая попытка через 1 час.')
    thread = threading.Timer(3600.0, ftp_updater)  # Проверяем каждый час
    thread.start()


def program_updater():
    global start_time, thread_update, thread
    try:
        now_time = os.path.getmtime(PathFile)
        if start_time != now_time:
            # os.execv(sys.executable, [sys.executable] + sys.argv)  # Перезапускаемся если обновился скрипт
            subprocess.Popen([sys.executable, *sys.argv])
            time.sleep(1)
            try:
                thread.cancel()
                thread_update.cancel()
            except Exception:
                pass
            sys.exit(0)
        else:
            pass
    except Exception:
        pass
    thread_update = threading.Timer(30.0, program_updater)
    thread_update.start()


program_updater()  # Вызываем функцию проверки обновления скрипта
try:
    if not os.path.exists(SLIDER_PATH):
        os.mkdir(SLIDER_PATH)
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


def update_treeview_text():  # Анимация цвета текста
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


def interpolate(color_a, color_b, t):  # Интерполяция цвета
    return tuple(int(k + (b - k) * t) for k, b in zip(color_a, color_b))


def size_checker(label):  # Получает размеры
    global frame_x, frame_y
    window.update_idletasks()
    frame_x = label.winfo_width()
    frame_y = label.winfo_height()


def qr_maker():  # Делает QR-код
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


def show_slides():  # Слайдер
    if qr_maker() is False:
        label_qr.pack_forget()
        image_object = next(resize_image_files)
        label_image.config(image=image_object)
        window.after(5000, show_slides)
    else:
        label_image.pack_forget()
        label_qr.pack(fill='x')
        label_image.pack(expand=True, fill='both')
        image_object = QR_LIST[0]
        label_image.config(image=image_object)
        window.after(5000, show_slides)


def _fixed_map(option, style1):  # Цвет текста в строках Treeview
    return [elm for elm in style1.map("Treeview", query_opt=option) if elm[:2] != ("!disabled", "!selected")]


def set_theme(bg, fg):  # Цвет текста в строках Treeview
    style1 = ttk.Style()
    style1.theme_use("clam")
    style1.map("Treeview", foreground=_fixed_map("foreground", style1), background=_fixed_map("background", style1))
    style1.configure("Treeview", background=bg, fieldbackground=bg, foreground=fg)


def deleter():  # Очищает Treeview
    for iid in id_list:
        treeview_purchase.delete(iid)
    id_list.clear()
    for iid in id_itog:
        treeview_itog.delete(iid)
    id_itog.clear()
    for iid in id_oplat:
        treeview_oplat.delete(iid)
    id_oplat.clear()


def writer():  # Заполняет Treeview если файл изменился
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
    print('\n\nОшибка! Второй монитор не обнаружен.\n\nПрограмма будет автоматически закрыта через 15 сек.')
    thread.cancel()
    thread_update.cancel()
    time.sleep(15.0)
    sys.exit()

list_fonts = list(font.families())

if 'Montserrat' not in list_fonts:
    print(
        f'\n\nОшибка! Не установлен шрифт "Montserrat"\n\nУстановите шрифт из папки: {ROOT_PATH}\n\nПрограмма будет автоматически закрыта через 15 сек.')
    thread.cancel()
    thread_update.cancel()
    time.sleep(15.0)
    sys.exit()
if 'Montserrat Medium' not in list_fonts:
    print(
        f'\n\nОшибка! Не установлен шрифт "Montserrat Medium"\n\nУстановите шрифт из папки: {ROOT_PATH}\n\nПрограмма будет автоматически закрыта через 15 сек.')
    thread.cancel()
    thread_update.cancel()
    time.sleep(15.0)
    sys.exit()

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
main_window = tk.Frame(window, bg='#d6f8ff')
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
    frame_right.pack(fill='both', side="left", expand=False)


def show_big_slides():  # Слайдер
    image_object = next(resize_big_image_files)
    label_big_slides.config(image=image_object)
    window.after(5000, show_big_slides)


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
if brend == 'Nevis':
    if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
        im3 = Image.open(IMAGES_PATH + r'\NEVIS1080840.png')
    else:
        im3 = Image.open(IMAGES_PATH + r'\NEVIS8401080.png')
elif brend == 'LenOblFarm':
    if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
        im3 = Image.open(IMAGES_PATH + r'\LOF1080840.png')
    else:
        im3 = Image.open(IMAGES_PATH + r'\LOF8401080.png')
else:
    print('\nНе удалось определить бренд аптеки')
if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
    label_big_slides = tk.Label(main_window, width=1080, image=default_big_slide_back)  # Лейбл под слайдер в простое
else:
    label_big_slides = tk.Label(main_window, width=1076, image=default_big_slide_back)  # Лейбл под слайдер в простое
default_cashback = ImageTk.PhotoImage(im3)


# Подгон размеров фоток под лейбл (фрейм)
def resize():
    global resize_image_files
    for image in image_files:
        b = Image.open(image)
        new = b.resize((1080, 1080))
        new1 = ImageTk.PhotoImage(new)
        resize_image_files.append(new1)


def resize_big():
    global resize_big_image_files
    for image in image_files:
        b = Image.open(image)
        new = b.resize((1080, 1080))
        new1 = ImageTk.PhotoImage(new)
        resize_big_image_files.append(new1)


label_image = tk.Label(frame_right, bg='#d6f8ff', image=default_slide_back)
label_image.pack(anchor=W, expand=True, fill='both', side='left')
size_checker(label_image)
resize()
resize_image_files = cycle(resize_image_files)  # Итератор для уменьшенных картинок
resize_big()
resize_big_image_files = cycle(resize_big_image_files)

cashback_label = tk.Label(main_window, height=840, image=default_cashback, bg='black')


def check_display_mode():
    global resize_big_image_files
    if not id_list:
        frame_right.pack_forget()
        frame_left.pack_forget()
        if abs(monitor_areas()[1][0]) == 1080 or abs(monitor_areas()[0][0]) == 1080:
            cashback_label.pack(fill='both', expand=True)
            label_big_slides.pack(fill='both', expand=True)
        else:
            label_big_slides.pack(fill='both', side='left', expand=True)
            cashback_label.pack(fill='both', side='left', expand=True)
    else:
        cashback_label.pack_forget()
        label_big_slides.pack_forget()
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
check_display_mode()
show_big_slides()
show_slides()
writer()
window.mainloop()
