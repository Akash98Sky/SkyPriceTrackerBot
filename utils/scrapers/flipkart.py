import re
from aiohttp import ClientSession
from bs4 import BeautifulSoup as bs

headers = {
    "Accept-Language": "en-IN;q=0.9,en;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) Gecko/20100101 Firefox/112.0"
}

class ExtractFlipkart:
    def __init__(self, url):
        self.url = url

    async def __aenter__(self):
        async with ClientSession(headers=headers) as session:
            async with session.get(self.url, allow_redirects=True) as req:
                page = await req.text()
                soup = bs(page, "lxml")
                return FlipkartPage(soup)

    async def __aexit__(self, *args):
        pass

class FlipkartPage:
    def __init__(self, soup: bs):
        self.soup = soup
    
    # Function to extract Product Title
    def get_title(self):
        try:
            title = self.soup.select_one("h1>span")
            title = title.text if title else ''
            title_string = re.sub("   +", " ", title)

        except AttributeError:
            title_string = ""	
        return title_string

    # Function to extract Product Price
    def get_price(self):
        price = self.soup.select_one('#container>div>div:nth-child(3)>div:nth-child(1)>div:nth-child(2)>div:nth-child(2)>div>div:nth-child(3)>div:nth-child(1)>div>div:nth-child(1)')
        price = price.text.strip() if price else None
        
        if not price:
            price = self.soup.select_one('#container>div>div:nth-child(3)>div:nth-child(1)>div:nth-child(2)>div:nth-child(2)>div>div:nth-child(4)>div>div>div:nth-child(1)')
            price = price.text.strip() if price else ''
        return price.replace('₹', '').replace(',', '')

    # Function to extract Product Rating
    def get_rating(self):
        try:
            rating = self.soup.select_one("#container>div>div:nth-child(3)>div:nth-child(1)>div:nth-child(2)>div:nth-child(2)>div>div:nth-child(2)>div>div>span>div")
            rating = rating.contents[0] if rating else ''
        except AttributeError:
            rating = ""	

        return rating

    # Function to extract Availability Status
    def is_available(self):
        try:
            sold_out = self.soup.select_one('#container>div>div:nth-child(3)>div:nth-child(1)>div:nth-child(2)>div:nth-child(3)>div:nth-child(1)')
            if sold_out:
                sold_out = sold_out.text.strip()
                return sold_out != 'Sold Out'
            else:
                return True
        except AttributeError as e:
            print(e)
            return True	
    

    # Function to extract images [ul>li>div>div>img]
    def get_images(self, width=500, height=500, quality=100):
        try:
            images = self.soup.select('ul>li>div>div>img')
            images_list = []
            for image in images:
                image_src = str(image['src'])
                image_src = image_src.replace('?q=70', f'?q={quality}')
                image_src = image_src.replace('image/128/128', f'image/{width}/{height}')
                images_list.append(image_src)
            return images_list
        
        except AttributeError:
            return False
    
    
