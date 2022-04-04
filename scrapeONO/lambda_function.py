import requests
from bs4 import BeautifulSoup

#def lambda_handler(event, context):
if __name__ == '__main__':
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
                    #logic to check if product ID is known to prod table
                    #this works as long as volume is low, to be scallable it should be saved to s3 and analyzed with EMR/Glue cluster
                    existing_product = requests.post(f'{apiBase}/getproduct/{id}')
                    if existing_product.status_code == 200:
                        headers = {'Content-Type': 'application/json'}
                        s3headers = {'Content-Type': 'image/jpeg'}
                        s3Key = picture.split('/')[-1]
                        b64 = requests.get(picture, stream=True)
                        s3Data = b64.content
                        r = requests.put(f'{apiBase}/saveimage/{s3bucket}/{s3Key}', data=s3Data, headers=s3headers)
                        s3Image = f'https://{s3bucket}.s3.us-east-2.amazonaws.com/{s3Key}'
                        if existing_product.json()['body']['Count'] == 1:
                            item = existing_product.json()['body']['Items'][0]
                            price_num = float(price.strip('$').replace(',',''))
                            if price_num < float(item['price']['N']):
                                product_data = {'productID': id, 'title': title, 'description': description, 'image': s3Image, 'price': price_num, 'quantity': '1', 'tags': 'reduced'}
                                r = requests.post(f'{apiBase}/createproduct', json=product_data, headers=headers)
                                print(f"Reduced product: {r.json()['body']['Items'][0]}")
                        else:
                            #new product, save to prod db
                            product_data = {'productID': id, 'title': title, 'description': description, 'image': s3Image, 'price': price_num, 'quantity': '1', 'tags': 'new'}
                            r = requests.post(f'{apiBase}/createproduct', json=product_data, headers=headers)
                            print(f"New product: {r.json()['body']['Items'][0]}")