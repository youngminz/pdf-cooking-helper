import io
from functools import lru_cache
from io import BytesIO

from PIL import Image
from PyPDF2 import (
    PdfFileReader,
    PdfFileWriter,
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import (
    ImageReader,
    simpleSplit,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import getAscentDescent
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

LINE_HEIGHT = 1.1

pdfmetrics.registerFont(TTFont('DEFAULT_LIGHT', 'resource/font/KoPubDotumLight.ttf'))
pdfmetrics.registerFont(TTFont('DEFAULT_MEDIUM', 'resource/font/KoPubDotumMedium.ttf'))
pdfmetrics.registerFont(TTFont('DEFAULT_BOLD', 'resource/font/KoPubDotumBold.ttf'))


@lru_cache()
def font_height(font, size):
    """글꼴의 높이를 반환한다."""
    ascent, descent = getAscentDescent(font, size)
    return (ascent - descent) * LINE_HEIGHT


def y_correction(current_index, sentence_count):
    """[0, 1, 2, ..., sentence_count - 1]까지 문자열을 쓸 때, 가운데 정렬을 하기 위해 곱해져야 하는 값을 구한다.

    >>> y_correction(0, 1)
    0.0

    >>> y_correction(0, 2)
    -0.5
    >>> y_correction(1, 2)
    0.5

    >>> y_correction(0, 3)
    -1.0
    >>> y_correction(1, 3)
    0.0
    >>> y_correction(2, 3)
    1.0
    """

    return -(sentence_count - 1) / 2 + current_index


def normalize_string(to_draw, font, size, max_width):
    """문자열을 draw_strings 함수에서 사용할 수 있게 정규화한다."""

    # 리스트나 튜플로 들어오면 그대로 반환하면 된다.
    if isinstance(to_draw, (list, tuple)):
        strings = to_draw

    # 문자열로 들어오면 최대 길이에 맞게 쪼갠다.
    elif isinstance(to_draw, str):
        strings = simpleSplit(to_draw, font, size, max_width)

    else:
        assert False

    return strings


def draw_strings(canvas_, strings, font, size, pos_x, pos_y, align="left"):
    """문자열들을 주어진 좌표 가운데로 정렬해서 그린다."""
    canvas_.setFont(font, size)
    for index, string in enumerate(strings):
        # y 축은 아래에서 위로 올라가는 좌표계이기 때문에 반대로 빼야 한다.
        y = pos_y - y_correction(index, len(strings)) * font_height(font, size)
        if align == "middle":
            canvas_.drawCentredString(pos_x, y, string)
        elif align == "right":
            canvas_.drawRightString(pos_x, y, string)
        else:
            canvas_.drawString(pos_x, y, string)


def draw_image(canvas_, image_file, pos_x, pos_y, size_x, size_y):
    """이미지를 캔버스에 그린다."""
    canvas_.drawImage(ImageReader(image_file), pos_x, pos_y, size_x, size_y, mask='auto', preserveAspectRatio=True)
    image_file.seek(0)


def generate_pdf_pages(template_pdf, metadata, serialized_data):
    """템플릿 이미지에 글자와 이미지를 그린다.
    리스트를 반환하는데, merge_pages 으로 넘기면 PDF 파일이 만들어진다."""
    template_pdf = PdfFileReader(template_pdf)

    pages = []

    assert template_pdf.getNumPages() == len(metadata)

    for page, fields in enumerate(metadata):
        layer_pdf = io.BytesIO()

        canvas_ = canvas.Canvas(layer_pdf, pagesize=A4)
        canvas_.translate(mm, mm)
        canvas_.setFillColorRGB(10 / 255, 126 / 255, 194 / 255)

        for field in fields:
            to_draw = serialized_data[field['name']]

            if field['type'] == 'text':
                assert isinstance(to_draw, (str, list, tuple))

                strings = normalize_string(to_draw, field['font'], field['size'], field.get('max_width', 210) * mm)
                draw_strings(
                    canvas_=canvas_,
                    strings=strings,
                    font=field['font'],
                    size=field['size'],
                    pos_x=field['position'][0] * mm,
                    pos_y=field['position'][1] * mm,
                    align=field.get('align', 'left'),
                )

            elif field['type'] == 'image':
                assert hasattr(to_draw, 'read')

                draw_image(
                    canvas_=canvas_,
                    image_file=to_draw,
                    pos_x=field['position'][0] * mm,
                    pos_y=field['position'][1] * mm,
                    size_x=field['size'][0] * mm,
                    size_y=field['size'][1] * mm,
                )

            else:
                assert False

        canvas_.save()
        layer_pdf.seek(0)

        in_memory_pdf_reader = PdfFileReader(layer_pdf)
        template_page = template_pdf.getPage(page)
        template_page.mergePage(in_memory_pdf_reader.getPage(0))
        template_page.compressContentStreams()

        pages.append(template_page)

    return pages


def merge_pages(pages, file_obj=None, password=None):
    if file_obj is None:
        file_obj = io.BytesIO()
    pdf_writer = PdfFileWriter()

    if password is not None:
        pdf_writer.encrypt(password)

    for template_page in pages:
        pdf_writer.addPage(template_page)

    pdf_writer.write(file_obj)
    file_obj.seek(0)

    return file_obj


def is_large_image(image_size):
    return image_size > 200 * 1024  # 200 KB 이상 이미지는 줄인다.


def shrink_image(image_bytes):
    image = Image.open(image_bytes).convert("RGB")
    original_width, original_height = image.size

    width = 1200
    height = int(original_height / original_width * width)
    image = image.resize((width, height), Image.ANTIALIAS)

    resized_image = BytesIO()
    image.save(resized_image, format='JPEG', quality=70)
    resized_image.seek(0)

    return resized_image


def convert_image_to_pdf_page(image):
    """
    이미지 파일을 받아서 canvas 으로 구워준다.
    Args:
        image (BytesIO|FileField): 이미지 파일

    Returns:
        BytesIO: PDF 파일
    """

    image_byte = image.read()

    image_bytes_io = BytesIO()
    image_bytes_io.write(image_byte)
    image_bytes_io.seek(0)

    if is_large_image(len(image_byte)):
        image = shrink_image(image_bytes_io)

    else:
        image = image_bytes_io

    # 1. 이미지를 PyPDF2가 사용할 수 있도록 읽는다.
    image_reader = ImageReader(image)

    # 2. 이미지를 그릴 캔버스를 준비한다.
    content_canvas = BytesIO()
    canvas_ = canvas.Canvas(content_canvas, pagesize=A4)

    # 3. 캔버스에 이미지를 붙여넣는다.
    space = 5 * mm
    canvas_.drawImage(image_reader, space, space, A4[0] - 2 * space, A4[1] - 2 * space, preserveAspectRatio=True)
    canvas_.save()

    # 4. 생성된 PDF 파일을 다른 곳에서 읽을 수 있게 한다.
    content_canvas.seek(0)

    in_memory_pdf_reader = PdfFileReader(content_canvas)
    return in_memory_pdf_reader.getPage(0)
