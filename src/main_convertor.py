import json

from pdf_core_utils import generate_pdf_pages, merge_pages


def main():
    metadata = json.loads(open('example/metadata.json', 'r').read())

    # metadata.json에 정의되어 있는 "name" 에 대응되는 값들을 PDF 생성 파라미터로 넣는다.
    parameter = {
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

    filename = 'example/withholding_report_template.pdf'
    pages = generate_pdf_pages(filename, metadata, parameter)
    merged = merge_pages(pages)

    with open('example/withholding_report_example_output.pdf', 'wb') as out:
        out.write(merged.read())


if __name__ == "__main__":
    main()
