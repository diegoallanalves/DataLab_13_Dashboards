"""Constrained educational scraper for purpose-built scraping practice websites."""
from urllib.parse import urljoin, urlparse
import requests
import pandas as pd
from bs4 import BeautifulSoup

SITES = {
    'Books to Scrape': {'url':'https://books.toscrape.com/', 'description':'A purpose-built practice catalogue: titles, prices, stock and ratings.', 'host':'books.toscrape.com'},
    'Quotes to Scrape': {'url':'https://quotes.toscrape.com/', 'description':'A purpose-built practice site: quotes, authors and tags.', 'host':'quotes.toscrape.com'},
}
RATINGS={'One':1,'Two':2,'Three':3,'Four':4,'Five':5}

def extract(html: str, base_url: str, site: str) -> pd.DataFrame:
    soup=BeautifulSoup(html,'html.parser')
    rows=[]
    if site=='Books to Scrape':
        for article in soup.select('article.product_pod'):
            link=article.select_one('h3 a')
            price=article.select_one('.price_color')
            rating=article.select_one('.star-rating')
            stock=article.select_one('.availability')
            if not link: continue
            raw_price=price.get_text(' ',strip=True) if price else ''
            try: amount=float(raw_price.replace('£','').replace('Â','').strip())
            except ValueError: amount=None
            rows.append({'Title':link.get('title') or link.get_text(' ',strip=True), 'Price GBP':amount,
                'Rating':next((v for k,v in RATINGS.items() if rating and k in rating.get('class',[])),None),
                'Availability':stock.get_text(' ',strip=True) if stock else '',
                'Product URL':urljoin(base_url,link.get('href',''))})
    elif site=='Quotes to Scrape':
        for item in soup.select('.quote'):
            q=item.select_one('.text'); author=item.select_one('.author')
            rows.append({'Quote':q.get_text(' ',strip=True) if q else '',
                         'Author':author.get_text(' ',strip=True) if author else '',
                         'Tags':', '.join(x.get_text(' ',strip=True) for x in item.select('.tag'))})
    return pd.DataFrame(rows)

def collect(site: str, pages: int = 1, delay: float = 1.0) -> pd.DataFrame:
    """No arbitrary URLs: only fixed, approved training hosts, no off-host redirects."""
    if site not in SITES: raise ValueError('Site not approved for this educational demo.')
    if not 1<=pages<=5 or not 0.5<=delay<=5: raise ValueError('Pages or delay out of range.')
    from time import sleep
    config=SITES[site]
    base=config['url']; frames=[]
    session=requests.Session()
    session.headers.update({'User-Agent':'DataLab13-EducationalDemo/1.0 (respectful scraping practice)'})
    for page in range(1,pages+1):
        url=(urljoin(base,f'catalogue/page-{page}.html') if site=='Books to Scrape' and page>1
             else urljoin(base,f'page/{page}/') if site=='Quotes to Scrape' and page>1 else base)
        response=session.get(url,timeout=12,allow_redirects=False)
        response.raise_for_status()
        if urlparse(response.url).hostname!=config['host']: raise ValueError('Unexpected host.')
        frame=extract(response.text,response.url,site)
        if frame.empty: break
        frame['Source Page']=page
        frames.append(frame)
        if page<pages: sleep(delay)
    return pd.concat(frames,ignore_index=True).drop_duplicates() if frames else pd.DataFrame()
