import requests
from bs4 import BeautifulSoup
import boto3

def lambda_handler(event, context):
    client = boto3.client('firehose')
    fire_data = []
    for i in range(1,10):
        base_url = 'https://www.overnightoffice.com/blog/page/##/?orderby=price'
        apiBase = 'https://api.cauchon.io/ono'
        s3bucket = 'ono-product-images'
        page = requests.get(base_url.replace('##',str(i)))
        soup = BeautifulSoup(page.content, "html.parser")
        content = soup.find(id="content")
        err_page = soup.find("div", class_="error-404")
        if err_page is None:
            product_list = content.find_all("li", class_="product")
            for product in product_list:
                title = product.find("h2", class_="woocommerce-loop-product__title").text
                product_details = requests.get(product.find("a")['href'])
                product_soup = BeautifulSoup(product_details.content, "html.parser")
                product_content = product_soup.find(id="content")
                err_page = product_soup.find("div", class_="error-404")
                if err_page is None:
                    price = product_content.find("span", class_="woocommerce-Price-amount").text
                    description = ""
                    for p in product_soup.find("div", class_="woocommerce-product-details__short-description").find_all("p"):
                        description += f'{p.text}\n'
                    picture = product_content.find("figure", class_="woocommerce-product-gallery__wrapper").find("a")['href']
                    id = picture.split('/')[-1].split('.')[0]
                    b64 = requests.get(picture, stream=True)
                    s3Key = picture.split('/')[-1]
                    s3headers = {'Content-Type': 'image/jpeg'}
                    s3Data = b64.content
                    r = requests.put(f'{apiBase}/saveimage/{s3bucket}/{s3Key}', data=s3Data, headers=s3headers)
                    s3Image = f'https://{s3bucket}.s3.us-east-2.amazonaws.com/{s3Key}'
                    headers = {'Content-Type': 'application/json'}
                    product_data = {'productID': id, 'title': title, 'description': description, 'image': s3Image, 'price': price.strip('$').split('.')[0], 'quantity': '1', 'tags': ''}
                    r = requests.post(f'{apiBase}/createproductstage', json=product_data, headers=headers)
                    print(product_data)
        else: break