from PySide.QtCore import  Qt
from PySide.QtGui import  QVBoxLayout, QApplication, QWidget, QTableWidget, QTableWidgetItem, QHBoxLayout
from PySide import QtGui as gui
import sys



wDayL = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat' ]

def main():
    app = QApplication(sys.argv)
    
    w = ConfigDate()
    w.show()
    sys.exit(app.exec_())



def populateTable(table, wDayStart, nDay):
    
    wDay = wDayStart
    wCount = 0 
    for i in range(1, nDay + 1):
        
        item = QTableWidgetItem(str(i))
        item.setFlags(Qt.ItemIsEnabled)
        
#        QObject.connect(item,SIGNAL('cellClicked()'), func)
        
        table.setItem(wCount, wDay, item)
#        mat[wCount][wDay] = str(i)
        wDay += 1
        if wDay >= 7:
            wDay = 0
            wCount += 1
            
        QTableWidgetItem()


def func(row, col, *argL):
    print 'clicked %d, %d' % (row, col)
    


class ConfigDate( QWidget ):
    
    def __init__(self, *args):
        QWidget.__init__(self, *args)
        
        dateTable = QTableWidget(5, 1, self)
        dateTable.verticalHeader().setVisible(False)
        dateTable.setHorizontalHeaderLabels(['Dates list'])

        dateTable.setShowGrid(False)

        dateTable.clicked.connect(self.showDatePicker)
        
        self.setLayout( QVBoxLayout())
        self.layout().addWidget(dateTable)
        
        
        mdp = MultiDatePicker()
        dialog = gui.QDialog()
        dialog.setModal(True)
        dialog.setLayout(QVBoxLayout())
        dialog.layout().addWidget( mdp )
        self.dialog = dialog
        
        
    def showDatePicker(self,*argL):
        self.dialog.show()

class MultiDatePicker(QWidget):
    
    def __init__(self, *args):
        QWidget.__init__(self, *args)


        table = QTableWidget(5, 7, self)
        populateTable(table, 2, 30)
        table.setHorizontalHeaderLabels(wDayL)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        table.resizeColumnsToContents()
#        table.setColumnWidth(1,100)
        table.cellClicked.connect(func)

        
        layout = QVBoxLayout()
        monthLayout = QHBoxLayout()
        
        qLeft = gui.QPushButton()
        qLeft.setText('<')
        qRight = gui.QPushButton()
        qRight.setText('>')
        monthLabel = gui.QLabel()
        monthLabel.setText('February 2012')
        monthLabel.setAlignment(Qt.AlignCenter)
        
        monthLayout.addStretch(1)
        monthLayout.addWidget(qLeft)
        monthLayout.addWidget(monthLabel)
        monthLayout.addWidget(qRight)
        monthLayout.addStretch(1)
        layout.addLayout(monthLayout)
        layout.addWidget(table)
        
        self.setLayout(layout)

        


if __name__ == "__main__":
    main()
