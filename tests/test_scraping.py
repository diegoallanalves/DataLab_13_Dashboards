from scraping import extract, collect
import pytest

def test_books_parser():
    html='''<article class="product_pod"><h3><a title="Example Book" href="catalogue/example.html">Example</a></h3><p class="price_color">£12.99</p><p class="star-rating Four"></p><p class="availability">In stock</p></article>'''
    df=extract(html,'https://books.toscrape.com/','Books to Scrape')
    assert len(df)==1
    assert df.iloc[0]['Title']=='Example Book'
    assert df.iloc[0]['Price GBP']==12.99
    assert df.iloc[0]['Rating']==4

def test_quotes_parser():
    html='<div class="quote"><span class="text">Hello</span><small class="author">Author</small><a class="tag">wisdom</a></div>'
    df=extract(html,'https://quotes.toscrape.com/','Quotes to Scrape')
    assert df.iloc[0]['Author']=='Author'
    assert df.iloc[0]['Tags']=='wisdom'

def test_unapproved_site_rejected():
    with pytest.raises(ValueError): collect('https://localhost',1,1)
