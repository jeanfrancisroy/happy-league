#!/usr/bin/env python

from PySide import QtCore, QtGui

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.tabs = ApplicationTabs()
        self.setCentralWidget(self.tabs)
        
        self.setWindowTitle("Happy League")
        self.setMinimumSize(600, 300)
        

class ApplicationTabs(QtGui.QTabWidget):
    def __init__(self):
        super(ApplicationTabs, self).__init__()
        
        # Schedule tab
        self.schedule_widget = ScheduleTabWidget()
        self.addTab(self.schedule_widget, "Schedule")

        # Config tab
        self.config_widget = ConfigTabWidget()
        self.addTab(self.config_widget, "Config")

        # Run tab
        self.run_widget = RunTabWidget()
        self.addTab(self.run_widget, "Run")

        self.setCurrentIndex(0)
        
        
class ScheduleTabWidget(QtGui.QWidget):
    def __init__(self):
        super(ScheduleTabWidget, self).__init__()
        
        self.schedule_config_list = ScheduleConfigPageList(self)
        
class ConfigTabWidget(QtGui.QWidget):
    def __init__(self):
        super(ConfigTabWidget, self).__init__()
        
        self.button = QtGui.QPushButton(self)
        self.button.setText("Config!")
    

class RunTabWidget(QtGui.QWidget):
    def __init__(self):
        super(RunTabWidget, self).__init__()
        
        self.button = QtGui.QPushButton(self)
        self.button.setText("Run!")
        

class ConfigElement(QtGui.QWidget):
    def __init__(self, name, input_type, parent=None):
        super(ConfigElement, self).__init__(parent)        
        
        self.value = None
        self.name = name
        self.input_type = input_type
        self.widget_map = {"text": QtGui.QLineEdit()}
        
        self.layout = QtGui.QBoxLayout(QtGui.QBoxLayout.LeftToRight)
        self.layout.addWidget(QtGui.QLabel(self.name))
        self.layout.addWidget(self.widget_map[self.input_type])
        
        self.setLayout(self.layout)
        
    
class ConfigPageList(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ConfigPageList, self).__init__(parent)
        
        self.horiz_layout = QtGui.QBoxLayout(QtGui.QBoxLayout.LeftToRight, self)
        
        self.configs_list = QtGui.QListWidget()
        self.configs_list.clicked.connect(self.load_page)
        self.config_pages = QtGui.QStackedLayout()
        
        self.horiz_layout.addWidget(self.configs_list)
        self.horiz_layout.addLayout(self.config_pages)
        
    def load_page(self, list_index):
        self.config_pages.setCurrentIndex(list_index.row())
        
    def add_config_page(self, name, page_widget, default=False):
        item = QtGui.QListWidgetItem(name)
        self.configs_list.addItem(item)
        self.config_pages.insertWidget(self.configs_list.count(), page_widget)
        
        if default:
            self.configs_list.setCurrentItem(item)
            self.load_page(self.configs_list.indexFromItem(self.configs_list.currentItem()))
        
       
class ScheduleConfigPageList(ConfigPageList):
    def __init__(self, parent):
        super(ScheduleConfigPageList, self).__init__(parent)
        
        self.add_config_page("General", ScheduleGeneralConfigPage(), True)
        self.add_config_page("Teams", QtGui.QLabel("Test1"))
        self.add_config_page("Fields", QtGui.QLabel("Test2"))


class ConfigPage(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ConfigPage, self).__init__(parent)
        self.layout = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom)
        self.setLayout(self.layout)
        self.config_elements = []
    
    def add_config_element(self, config_element):
        self.config_elements.append(config_element)
        self.layout.addWidget(config_element)
        
        
class ScheduleGeneralConfigPage(ConfigPage):
    def __init__(self, parent=None):
        super(ScheduleGeneralConfigPage, self).__init__(parent)
        self.add_config_element(ConfigElement("Test", "text"))
        self.add_config_element(ConfigElement("Test2", "text"))
        self.add_config_element(ConfigElement("Test3", "text"))
        self.add_config_element(ConfigElement("Test4", "text"))

        

if __name__ == '__main__':

    import sys

    app = QtGui.QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())