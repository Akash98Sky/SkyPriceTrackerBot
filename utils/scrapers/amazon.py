from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup as bs

REQUEST_HEADER = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) Gecko/20100101 Firefox/112.0" }
REQUEST_COOKIES = { "cookies_are": "working" }

class ExtractAmazon:
    def __init__(self, url):
        self.url = url

    async def __aenter__(self):
        async with ClientSession(headers=REQUEST_HEADER, cookies=REQUEST_COOKIES, timeout=ClientTimeout(4)) as session:
            async with session.get(self.url, allow_redirects=True) as req:
                page = await req.text()
                soup = bs(page, "lxml")
                return AmazonPage(soup)
    
    async def __aexit__(self, *args):
        pass

class AmazonPage:
    def __init__(self, soup: bs):
        self.soup = soup

    # Function to extract Product Title
    def get_title(self):
        try:
            title = self.soup.select_one("div[id='titleSection'] > h1[id='title'] > span[id='productTitle']")
            title_string = title.text.strip() if title else ''

        except AttributeError as e:
            title_string = ""	
            
        return title_string

    # Function to extract Product Price
    def get_price(self):
        try:
            price = self.soup.select_one("span[id='priceblock_ourprice']")
            if price:
                price = price.text.strip()
            else:
                raise AttributeError()

        except AttributeError as e:
            price_tag = self.soup.select_one("div[id='corePriceDisplay_desktop_feature_div'] span.a-price.aok-align-center.reinventPricePriceToPayMargin.priceToPay > span:nth-child(2) > span.a-price-whole")
            price = price_tag.text if price_tag else None
            if not price:
                price_table = self.soup.select_one("div[id='corePrice_desktop']>div>table>span.a-offscreen")
                price = price_table.text if price_table else ''

        return price.strip().replace(',','').replace('₹', '')

    # Function to extract Product Rating
    def get_rating(self):
        try:
            rating = self.soup.find("i", attrs={'class':'a-icon a-icon-star a-star-4-5'})
            rating = rating.text.strip() if rating else ''
        except AttributeError:
            try:
                rating = self.soup.find("span", attrs={'class':'a-icon-alt'})
                rating = rating.text.strip() if rating else ''
            except Exception as e:
                print('Exception: ', e)
                rating = ""	

        return rating

    # Function to extract Number of User Reviews
    def get_review_count(self):
        try:
            review_count = self.soup.find("span", attrs={'id':'acrCustomerReviewText'})
            review_count = review_count.text.strip() if review_count else ''
            
        except AttributeError as e:
            print('Exception: ', e)
            review_count = ""	

        return review_count

    # Function to extract Availability Status
    def is_available(self):
        try:
            available = self.soup.find("input", attrs={'id':'add-to-cart-button'})
            return bool(available)
        
        except AttributeError as e:
            print('Exception: ', e)
            return False	
        
    # Function to extract images 
    def get_images(self) -> list[str]:
        try:
            images = self.soup.select("div[id='imgTagWrapperId'] > img")
            # FIXME: FETCH ALL IMAGES
            return [str(image["src"]) for image in images]
        except AttributeError as e:
            print('Exception: ', e)
            return []
    
    # Function to extract deal badge
    def has_deal(self, get_regular_price=False):
        try:
            deal_span = self.soup.select_one('#dealBadgeSupportingText')
            # inner_span = deal_span.find('span')
            if get_regular_price:
                try:
                    regular_price = self.soup.select_one('#corePrice_feature_div > div > div > span.a-price.a-text-normal.aok-align-center.reinventPriceAccordionT2 > span:nth-child(2) > span.a-price-whole')   
                    return True if regular_price and len(regular_price.contents) > 0 else False
                
                except Exception:
                    return bool(deal_span)
                
            return bool(deal_span)
        
        except AttributeError as e:
            print('Exception: ', e)
            return False