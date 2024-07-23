from typing import Union
from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup as bs

REQUEST_HEADER = { "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36" }

class ExtractGeneric:
    def __init__(self, url):
        self.url = url

    async def __aenter__(self):
        async with ClientSession(headers=REQUEST_HEADER, timeout=ClientTimeout(4)) as session:
            data: dict[str, Union[bool, str]] = { "status": False, "code": "" }
            async with session.post("https://pricehistory.app/api/search", data={"url": self.url}) as res:
                data = await res.json()

            if data and data["status"]:
                async with session.get(f"https://pricehistory.app/p/{data["code"]}", allow_redirects=True) as req:
                    page = await req.text()
                    soup = bs(page, "lxml")
                    return CommonPage(soup)
            else:
                soup = bs("", "lxml")
                return CommonPage(soup)
    
    async def __aexit__(self, *args):
        pass

class CommonPage:
    def __init__(self, soup: bs):
        self.soup = soup

    # Function to extract Product Title
    def get_title(self):
        try:
            title = self.soup.select_one("div#product-info > div > div > table > tbody > tr:-soup-contains('Product Name') > td")
            title_string = title.text.strip() if title else ''

        except AttributeError as e:
            title_string = ""	
            
        return title_string

    # Function to extract Product Price
    def get_price(self):
        price = self.soup.select_one("div#price-table > div > table > tbody > tr:-soup-contains('Price') > td")
        if price:
            price = price.text.strip()
        else:
            price = ''

        return price.strip().replace(',','').replace('₹', '')

    # Function to extract Product Rating
    def get_rating(self):
        rating = self.soup.select_one("div#product-info > div > div > table > tbody > tr:-soup-contains('Rating') > td")
        rating = rating.text.strip() if rating else ''

        return rating
        
    # Function to extract images 
    def get_images(self) -> list[str]:
        try:
            images = self.soup.select("body > div.container.main-container > div:nth-child(7) > div > div > div > div > div > div > img")
            # FIXME: FETCH ALL IMAGES
            return [str(image["src"]) for image in images]
        except AttributeError as e:
            print('Exception: ', e)
            return []
