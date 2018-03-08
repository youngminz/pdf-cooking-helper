# pdf-cooking-helper
PDF 템플릿을 생성할 때 좌표 구하는 작업을 도와주는 도구입니다.

# 설치 방법

1. Python 3.5 이상에서 작동합니다.
2. `brew install ghostscript`
3. `pip install -r requirements`
4. KoPub 등 사용할 폰트들을 다운로드 받아 이 폴더에 넣습니다.

# 사용 방법

![사진](screenshot.png)
이와 같이 PDF 파일을 불러온 후 내용을 클릭하면 해당 좌표가 하단에 출력됩니다.

```
canvas_pdf = canvas.Canvas(in_memory_file, pagesize=A4)
canvas_pdf.translate(mm, mm)
canvas_pdf.setFont('DEFAULT_LIGHT', 10)
canvas_pdf.drawString(44.5 * mm, 225.5 * mm, '이런 식으로 문자열을 쓸 수 있습니다.')  # 여기에 찍힐 좌표를 구해줍니다.
```

# 라이센스

LICENSE 파일을 참고하세요.
