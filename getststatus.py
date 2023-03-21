# Import modules
import requests
from bs4 import BeautifulSoup

# Define URL
url = "http://192.168.2.195/index_cn.html"

# Get URL content with requests
response = requests.get(url, auth=('admin', 'admin'))
html = response.content

# Parse HTML with BeautifulSoup
soup = BeautifulSoup(html, "html.parser")

# Find div with id webdata_now_p
div = soup.find("div", id="webdata_now_p")

# Print div content
print(div.get_text())
