from celery import Celery
from multiprocessing import Lock


app = Celery('tasks',
             broker='redis://localhost:6379/0',
             include=["crawl"]
             )

file_lock = Lock()


@app.task
def write_to_file(filename, data):
    with file_lock:
        with open(filename + ".txt", 'a') as f:

            f.write(data + "\n")
