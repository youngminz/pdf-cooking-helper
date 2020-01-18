import io
import json
import sys
from io import BytesIO

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import (QApplication, QFileDialog, QGraphicsScene,
                             QInputDialog, QLineEdit, QWidget)
from reportlab.lib.units import mm
from wand.image import Image

from pdf_core_utils import generate_pdf_pages, merge_pages

size = (0, 0)
size_mm = (0, 0)

status_bar = None


class Form(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.ui = uic.loadUi("resource/ui/MainWindow.ui", self)
        self.ui.show()

        options = QFileDialog.Options()
        filename = 'example/withholding_report_template.pdf'

        global size, size_mm
        metadata = json.loads(open('example/metadata.json', 'r').read())

        # metadata.json에 정의되어 있는 "name" 에 대응되는 값들을 PDF 생성 파라미터로 넣는다.
        param2 = {
            # 글자는 이렇게 넣으면 된다.
            "corporate_name": "주식회사 피플펀드컴퍼니",
            "ceo_name": "김대윤",
            "company_registration_number": "666-88-00027",
            "address": "서울특별시 강남구 선릉로 428 18층(대치동)",
            "name": "소득자 이름",
            "identification_number": "123456-1234567",
            "earner_type": "111",

            "repayment_date_yyyy": "2020",
            "repayment_date_mm": "01",
            "repayment_date_dd": "01",
            "tax_type": "T",
            "income_type": "22",
            "special_taxation": "NN",
            "interest_calc_date": ["2020.01.01", "2020.02.01"],
            "interest_rate": "12.3",
            "amount": "10,000",
            "tax_rate": "25",
            "income_tax": "2,500",
            "corporate_tax": "",
            "resident_tax": "250",
            "total": "2,750",

            "today_yyyy": "2020",
            "today_mm": "01",
            "today_dd": "18",

            # 그림 파일은 open(filepath, 'rb') 을 넣으면 된다.
            "check": open("resource/image/icon_check_blue.png", "rb")
        }

        pages = generate_pdf_pages(filename, metadata, param2)
        merged = merge_pages(pages)

        memory = BytesIO()
        image = Image(file=merged, resolution=150)
        initiated_page = pages[0]
        conv = image.convert('png')
        size = conv.size
        size_mm = (
            float(initiated_page.mediaBox.getWidth()) / mm,
            float(initiated_page.mediaBox.getHeight()) / mm,
        )
        conv.save(memory)
        memory.seek(0)

        qimg = QtGui.QImage.fromData(memory.read())
        pixmap = QtGui.QPixmap.fromImage(qimg)
        scene = GraphicsScene()
        scene.addPixmap(pixmap)
        self.ui.graphicsView.setScene(scene)

        global status_bar
        status_bar = self.statusBar()


class GraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        super(GraphicsScene, self).__init__(parent)
        self.parent = parent

    def mouseReleaseEvent(self, event):
        global size, size_mm
        try:
            x = max(0, min(event.scenePos().x() / size[0], 1))
            y = max(0, min(event.scenePos().y() / size[1], 1))
        except ZeroDivisionError:
            x, y = -1, -1

        global status_bar
        status_bar.showMessage('Point : ({:.2f}, {:.2f})'.format(
            x * size_mm[0], (1 - y) * size_mm[1]))
        return QGraphicsScene.mouseReleaseEvent(self, event)


if __name__ == '__main__':
    try:
        app = QtWidgets.QApplication(sys.argv)
        w = Form()
        app.exec()

    except:
        import traceback
        traceback.print_exc()
