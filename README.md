## Crawl Immi HomeAffairs
Download the compatible verson of chromedriver and set its address:<br>
**https://getwebdriver.com/**
```bash 
export chromedriver_addr=/usr/lib/chromium-browser/chromedriver
```

use Redis as broker for Celery:<br>
```bash
docker run -dit -p 6379:6379 redis
```

before runnig project:
```bash
pip install -r requirements.txt
```
first run celery workers
```bash
celery -A tasks.app worker
```
finally:
```bash
python3 goc.py
```