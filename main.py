import sys
from io import BytesIO

from PyPDF2 import PdfFileReader, PdfFileWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from wand.image import Image

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QFileDialog, QGraphicsScene, QInputDialog, QLineEdit, QWidget

size = (0, 0)
size_mm = (0, 0)

status_bar = None


class Form(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.ui = uic.loadUi("MainWindow.ui", self)
        self.ui.show()

        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "PDF 파일 (*.pdf)", options=options)
        if not filename:
            exit(0)

        global size, size_mm
        pdf_writer = PdfFileWriter()
        blank_pdf_reader = PdfFileReader(filename)
        in_memory_file = BytesIO()
        pdfmetrics.registerFont(TTFont('DEFAULT_LIGHT', 'KoPubDotumLight.ttf'))
        pdfmetrics.registerFont(TTFont('DEFAULT_MEDIUM', 'KoPubDotumMedium.ttf'))
        pdfmetrics.registerFont(TTFont('DEFAULT_BOLD', 'KoPubDotumBold.ttf'))

        canvas_pdf = canvas.Canvas(in_memory_file, pagesize=A4)
        canvas_pdf.translate(mm, mm)
        # canvas_pdf.setFont('DEFAULT_LIGHT', 10)
        # canvas_pdf.setFillColorRGB(40 / 255, 40 / 255, 40 / 255)
        # canvas_pdf.drawString(44.5 * mm, 225.5 * mm, '이런 식으로 문자열을 쓸 수 있습니다.')

        canvas_pdf.showPage()
        canvas_pdf.save()

        in_memory_pdf_reader = PdfFileReader(in_memory_file)

        initiated_page = blank_pdf_reader.getPage(0)
        initiated_page.mergePage(in_memory_pdf_reader.getPage(0))
        initiated_page.compressContentStreams()

        pdf_writer.addPage(initiated_page)
        tmp_file = BytesIO()
        pdf_writer.write(tmp_file)
        tmp_file.seek(0)

        memory = BytesIO()
        image = Image(file=tmp_file, resolution=200)
        conv = image.convert('png')
        size = conv.size
        size_mm = float(initiated_page.mediaBox.getWidth()) / mm, float(initiated_page.mediaBox.getHeight()) / mm
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
        status_bar.showMessage('Point : ({:.2f}, {:.2f})'.format(x * size_mm[0], (1 - y) * size_mm[1]))
        return QGraphicsScene.mouseReleaseEvent(self, event)


if __name__ == '__main__':
    try:
        app = QtWidgets.QApplication(sys.argv)
        w = Form()
        app.exec()

    except:
        import traceback
        traceback.print_exc()
