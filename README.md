# News Scrapper

## How to Install
### News Scrapper
1. Setup virtual env
> virtualenv venv

2. Activate virtualenv
> . venv/bin/activate

3. Install requirements
> pip install -r requirements.txt

4. Init scrapy (if not exist)
> scrapy startproject scrapper

## How to Run
1. Go to project folder
> cd scrapper

2. Run this command
> scrapy crawl --nolog news
> scrapy crawl news
