import logging
import sys
import datetime
import requests

from datetime import timezone
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,  # Default to INFO level
    format='%(filename)s:%(lineno)d | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("mcp-basic")

def get_book_list(keyword: str) -> str:
    """
    Search book list by keyword and then return book list
    keyword: search keyword
    return: book list
    """
    
    keyword = keyword.replace('\'','')

    answer = ""
    url = f"https://search.kyobobook.co.kr/search?keyword={keyword}&gbCode=TOT&target=total"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        prod_info = soup.find_all("a", attrs={"class": "prod_info"})
        
        if len(prod_info):
            answer = "추천 도서는 아래와 같습니다.\n"
            
        for prod in prod_info[:5]:
            title = prod.text.strip().replace("\n", "")       
            link = prod.get("href")
            answer = answer + f"{title}, URL: {link}\n\n"
    
    return answer

# def stock_data_lookup(ticker, country, period="1mo"):
#     """
#     Retrieve accurate stock data for a given ticker.
#     country: the english country name of the stock
#     ticker: the ticker to retrieve stock price history for. In South Korea, a ticker is a 6-digit number.
#     period: the period to retrieve stock price history for. for example, "1mo", "1y", "5y", "max"
#     return: the information of ticker
#     """ 
#     com = re.compile('[a-zA-Z]') 
#     alphabet = com.findall(ticker)
#     logger.info(f"alphabet: {alphabet}")

#     logger.info(f"country: {country}")

#     if len(alphabet)==0:
#         if country == "South Korea":
#             ticker += ".KS"
#         elif country == "Japan":
#             ticker += ".T"
#     logger.info(f"ticker: {ticker}")
    
#     stock = yf.Ticker(ticker)
    
#     # get the price history for past 1 month
#     history = stock.history(period=period)
#     logger.info(f"history: {history}")
    
#     result = f"## Trading History\n{history}"
#     #history.reset_index().to_json(orient="split", index=False, date_format="iso")    
    
#     result += f"\n\n## Financials\n{stock.financials}"    
#     logger.info(f"financials: {stock.financials}")

#     result += f"\n\n## Major Holders\n{stock.major_holders}"
#     logger.info(f"major_holders: {stock.major_holders}")

#     logger.info(f"result: {result}")

#     return result
