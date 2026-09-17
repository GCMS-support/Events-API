import os

bind = '0.0.0.0:' + os.environ.get('PORT', '5000')
# A single worker avoids competing SQLite schema initialization.
workers = 1
threads = 4
timeout = 60
accesslog = '-'
errorlog = '-'
