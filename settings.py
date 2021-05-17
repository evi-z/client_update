from PyQt5 import QtWidgets, QtCore, QtGui
import configparser
import sys

import windows.settings_window_pharmacy as settings_win_pharmacy
import windows.settings_window_office as settings_win_office
from res import icons

from values import *

from settings_fun import *

# TODO Зависимость от config
HOST = '192.168.150.43'
SQL_DEMON_PORT = 12342

ENDSWITH = '#'
MODE = 'settings'  # Флаг для SQL Demon


class Settings(QtWidgets.QMainWindow):
    online = False  # Флаг статуса соединения

    pharmacy_dict = {}  # Краткий словарь аптек
    office_dict = {}  # Краткий словарь офиса
    subgroup = []  # Список подгрупп

    def __init__(self):
        super(Settings, self).__init__(parent=None)
        self.initWidgetsPharmacy()  # Ну так вот
        #self.ui = settings_win_office.Ui_Client_settings()  # ДЕБАГ

        self.initTitle()
        self.initDict()

    # Инициализаия окна
    def initTitle(self):
        self.setWindowIcon(QtGui.QIcon(':/icons/settings.png'))
        self.setFixedSize(270, 240)

    # Инициализация словаря
    def initDict(self):
        try:  # Пытаемся получить словари
            self.pharmacy_dict, self.office_dict = connect_to_sql()  # Устанавливаем соединение и пишем словари
            # Добавляет в список подгрупп подгруппу, если её там ещё нет
            self.subgroup = [sub for sub in self.office_dict if sub not in self.subgroup]

        except OSError:  # Если соединение отсутвует
            self.online = False  # Ставим флаг "Оффлайн"
            self.setConnectStatus()  # Обновляем статус подключения
            return

        self.online = True  # Ставим флаг "Онлайн"
        self.setConnectStatus()  # Обновляем статус подключения

    # Инициализация виджетов
    def initWidgets(self, start=GROUP_PHARMACY_TEXT):
        # Настройки CB
        if start == GROUP_PHARMACY_TEXT:  # Если группа Аптеки
            group_list = [GROUP_PHARMACY_TEXT, GROUP_OFFICE_TEXT]
        elif start == GROUP_OFFICE_TEXT:  # Если группа Офис
            group_list = [GROUP_OFFICE_TEXT, GROUP_PHARMACY_TEXT]

        self.ui.cb_group.addItems(group_list)
        self.ui.cb_group.currentIndexChanged.connect(self.replaceWidgets)  # Событие выбора группы

        self.initSlots()  # Инициализация общих слотов
        self.setConnectStatus()  # Пишет состояние соединения

        self.ui.btn_quit_and_start.setToolTip('Выходит из мастера и запускает клиент')
        self.ui.btn_update.setToolTip('Обновляет соединение с сервером')

    # Устанавливает lab_ststus в зависимости от флага
    def setConnectStatus(self):
        if self.online:
            self.ui.lab_status.setText('Онлайн')
            self.ui.lab_status.setStyleSheet("color: rgb(0, 170, 0);")  # Зелёный
        else:
            self.ui.lab_status.setText('Оффлайн')
            self.ui.lab_status.setStyleSheet("color: rgb(255, 85, 0);")  # Оранжевый

    # Меняет вид программы в соответсвии с выбранной группой
    def replaceWidgets(self):
        current_cb = self.ui.cb_group.currentText()

        if current_cb == GROUP_PHARMACY_TEXT:  # Если выбранно Аптеки
            self.initWidgetsPharmacy()
        elif current_cb == GROUP_OFFICE_TEXT:  # Если выбранно Офис
            self.initWidgetsOffice()

    # Инициализирует вид программы для группы Аптеки
    def initWidgetsPharmacy(self):
        self.ui = settings_win_pharmacy.Ui_Client_settings()
        self.ui.setupUi(self)

        self.initWidgets(GROUP_PHARMACY_TEXT)

        # Настройки CB Устройства
        device_list = [KOMZAV, KASSA1, KASSA2, KASSA3,
                       KASSA4, KASSA5, MINISERVER]

        self.ui.cb_device.addItems(device_list)

        # Настройки ET
        self.ui.et_pharmacy.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.ui.et_pharmacy.setMaxLength(30)

    # Инициализирует вид программы для группы Офис
    def initWidgetsOffice(self):
        self.ui = settings_win_office.Ui_Client_settings()
        self.ui.setupUi(self)

        self.initWidgets(GROUP_OFFICE_TEXT)  # Инициализация общих виджетов

        self.ui.cb_subgroup.addItems(self.subgroup)  # Добавляем подгруппы к CB
        self.ui.btn_add_subgroup.clicked.connect(self.addSubgroup)  # Подключает кнопку добавления подгруппы

    # Добавляет новую подгруппу
    def addSubgroup(self):
        inp, ok = QtWidgets.QInputDialog.getText(self, 'Новая подгруппа', 'Введите название подгруппы:')

        if ok:  # Если нажата ОК
            self.subgroup.append(inp)  # Добавляем подгруппу к остальным

            self.ui.cb_subgroup.clear()  # Чистим виджет
            self.ui.cb_subgroup.addItems(self.subgroup)  # Добавляем элементы
            self.ui.cb_subgroup.setCurrentText(inp)  # Ставим на только введённое

    # Инициализация слотов
    def initSlots(self):
        self.ui.btn_save.clicked.connect(self.saveBtn)
        self.ui.btn_update.clicked.connect(self.updateBtn)

    # Возвращает выбранную группу
    def getCurrentGroup(self):
        return self.ui.cb_group.currentText()

    # Кнопка "Записать"
    def saveBtn(self):
        group = self.getCurrentGroup()

        if group == GROUP_PHARMACY_TEXT:
            group = str(GROUP_PHARMACY_INT)
            pharmacy = self.ui.et_pharmacy.text()
            device = self.ui.cb_device.currentText()
            device = DEVICE_DICT[device]

            if not pharmacy:  # Если поле пустое
                return

            if self.online:  # Если в сети
                try:
                    if device in str(self.pharmacy_dict[pharmacy]):  # Если такая запись уже есть
                        mb = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Warning, 'Предупреждение',
                                                   'Запись с такими параметрами уже существует в базе')
                        mb.setInformativeText('Соглашайтесь на эту конфигурацию только '
                                              'если уверенны в корректности данных.')
                        mb.addButton('Записать', QtWidgets.QMessageBox.ButtonRole.YesRole)
                        mb.setDefaultButton(mb.addButton('Отмена', QtWidgets.QMessageBox.ButtonRole.RejectRole))
                        mb.exec_()
                        select = mb.buttonRole(mb.clickedButton())

                        if select == QtWidgets.QMessageBox.ButtonRole.YesRole:  # Если согласны
                            self.createConfig(group, pharmacy, device)
                    else:
                        self.createConfig(group, pharmacy, device)

                except KeyError:  # Если такого ключа нет
                    self.createConfig(group, pharmacy, device)
            else:  # Если оффлайн режим
                self.createConfig(group, pharmacy, device)

        elif group == GROUP_OFFICE_TEXT:  # Здоровенный TODO
            group = str(GROUP_OFFICE_INT)
            subgroup = self.ui.cb_subgroup.currentText()
            name = self.ui.et_name.text()

            self.createConfig(group, subgroup, name)

    # Создаёт конфиг и печатает информацию
    def createConfig(self, group, pharm_or_sub, dev_or_name):
        createConfig(group, pharm_or_sub, dev_or_name)  # Пишем конфиг

        if group == str(GROUP_PHARMACY_INT):  # Если группа Аптека
            print('Тут')
            first_parm = 'Аптека:'
            second_pharm = 'Устройство:'
            dev_or_name = self.ui.cb_device.currentText()

        elif group == str(GROUP_OFFICE_INT):  # Если группа Офис
            first_parm = 'Подгруппа:'
            second_pharm = 'Имя:'

        mb = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Information, 'Сохраненно',
                                   f'{first_parm} {pharm_or_sub}\n'
                                   f'{second_pharm} {dev_or_name}')
        mb.setInformativeText('Конфигурация успешно сохранена\n'
                              'Нажмите кнопку "Выход и запуск клиента", чтобы закончить работу')
        mb.setDefaultButton(mb.addButton('Отлично', QtWidgets.QMessageBox.ButtonRole.RejectRole))
        mb.exec_()

    # Кнопка "Обновить"
    def updateBtn(self):
        self.initDict()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    win = Settings()
    win.show()
    sys.exit(app.exec_())
