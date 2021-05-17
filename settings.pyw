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
    apt_dict = {}
    subgroup = []

    def __init__(self):
        super(Settings, self).__init__(parent=None)
        self.initWidgetsPharmacy()  # Ну так вот
        #self.ui = settings_win_office.Ui_Client_settings()  # ДЕБАГ

        self.initTitle()
        self.initDict()

    # Инициализаия окна
    def initTitle(self):
        self.setWindowIcon(QtGui.QIcon(':/icons/settings.png'))
        self.setFixedSize(257, 266)

    # Инициализация словаря
    def initDict(self):
        self.apt_dict = {}

        try:
            self.apt_dict = connect()  # Устонавливаем соединение и пишем словарь
        except OSError:  # Если соединение отсутвует
            self.ui.lab_status.setText('Оффлайн режим')
            self.ui.lab_status.setStyleSheet("color: rgb(255, 85, 0);")  # Оранжевый
            return
        self.ui.lab_status.setText('Соединение установлено')
        self.ui.lab_status.setStyleSheet("color: rgb(0, 170, 0);")  # Зелёный
        self.online = True  # Ставим флаг "В сети"

    # Инициализация виджетов
    def initWidgets(self, start=GROUP_PHARMACY_TEXT):
        # Настройки CB
        if start == GROUP_PHARMACY_TEXT:
            group_list = [GROUP_PHARMACY_TEXT, GROUP_OFFICE_TEXT]
        else:
            group_list = [GROUP_OFFICE_TEXT, GROUP_PHARMACY_TEXT]

        self.ui.cb_group.addItems(group_list)
        self.ui.cb_group.currentIndexChanged.connect(self.replaceWidgets)  # Событие выбора группы

        self.initSlots()

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

        self.initWidgets(GROUP_OFFICE_TEXT)

        self.ui.btn_add_subgroup.clicked.connect(self.addSubgroup)

    # Добавляет новую подгруппу
    def addSubgroup(self):
        inp, ok = QtWidgets.QInputDialog.getText(self, 'Новая подгруппа', 'Введите название подгруппы:')

        if ok:  # TODO Ууууу
            self.subgroup.append(inp)

            self.ui.cb_subgroup.clear()
            self.ui.cb_subgroup.addItems(self.subgroup)

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
            apt = self.ui.et_pharmacy.text()
            device = self.ui.cb_device.currentText()
            device = DEVICE_DICT[device]

            if not apt:  # Если поле пустое
                return

            if self.online:  # Если в сети
                try:
                    if self.apt_dict[apt] == device:  # Если такая запись уже есть
                        mb = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Warning, 'Предупреждение',
                                                   'Запись с такими параметрами уже существует в базе')
                        mb.setInformativeText('Соглашайтесь на запись только если уверенны в корректности данных.')
                        mb.addButton('Записать', QtWidgets.QMessageBox.ButtonRole.YesRole)
                        mb.setDefaultButton(mb.addButton('Отмена', QtWidgets.QMessageBox.ButtonRole.RejectRole))
                        mb.exec_()
                        select = mb.buttonRole(mb.clickedButton())

                        if select == QtWidgets.QMessageBox.ButtonRole.YesRole:  # Если согласны
                            createConfig(group, apt, device)
                    else:
                        createConfig(group, apt, device)

                # TODO Окно подтверждения
                except KeyError:  # Если такого люча нет
                    createConfig(group, apt, device)
            else:  # Если оффлайн режим
                createConfig(group, apt, device)

        elif group == GROUP_OFFICE_TEXT:  # Здоровенный TODO
            group = str(GROUP_OFFICE_INT)
            subgroup = self.ui.cb_subgroup.currentText()
            name = self.ui.et_name.text()

            createConfig(group, subgroup, name)

    # Кнопка "Обновить"
    def updateBtn(self):
        self.initDict()


# Создаёт settings.ini
def createConfig(group, pharmacy, device):
    config = configparser.ConfigParser()
    config.add_section(APP_SECTION)
    config.set(APP_SECTION, GROUP_PHARM, group)
    config.set(APP_SECTION, PHARMACY_OR_SUBGROUP_PHARM, pharmacy)
    config.set(APP_SECTION, DEVICE_OR_NAME_PHARM, device)

    config.add_section(CONNECT_SECTION)
    config.set(CONNECT_SECTION, HOST_PHARM, HOST)
    config.set(CONNECT_SECTION, PORT_DEMON_PHARM, str(PORT_DEMON_PORT))

    with open(CONFIG_NAME, 'w') as config_file:
        config.write(config_file)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    win = Settings()
    win.show()
    sys.exit(app.exec_())
