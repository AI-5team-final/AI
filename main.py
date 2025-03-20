import pdfplumber

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"  # 페이지별로 텍스트 추출
    return text

# 사용 예시
pdf_path = "png2pdf.pdf"  # 여기에 PDF 파일 경로 입력
extracted_text = extract_text_from_pdf(pdf_path)

print(extracted_text)  # 추출된 텍스트 출력
