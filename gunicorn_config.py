import multiprocessing

# Bind to localhost
bind = "0.0.0.0:5000"

# Increase timeout to 5 minutes (300 seconds) for long AI generations
timeout = 300

# Worker configuration
workers = 3  # Start with a few workers
worker_class = "sync"
threads = 2

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
