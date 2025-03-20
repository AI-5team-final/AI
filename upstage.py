# pip install requests
 
import requests
 
api_key = "up_zqkw8XS0H4k1Fdn7SE6KIF2DnAuWR"
filename = "png2pdf.pdf"
 
url = "https://api.upstage.ai/v1/document-ai/ocr"
headers = {"Authorization": f"Bearer {api_key}"}
 
files = {"document": open(filename, "rb")}
response = requests.post(url, headers=headers, files=files)
 
print(response.json())


# //////

# api_key = "up_TRqRyyAKdYTvQlt3iW00jyi4HAnY2"
# filename = "png2pdf.pdf"
 
# url = "https://api.upstage.ai/v1/document-ai/ocr"
# headers = {"Authorization": f"Bearer {api_key}"}
 
# files = {"document": open(filename, "rb")}
# response = requests.post(url, headers=headers, files=files)
 
# print(response.json())