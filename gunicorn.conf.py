# Cross-Platform Production Configuration for EmailScope
# Automatically detects platform and uses appropriate WSGI server

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes (Unix only - Waitress handles this differently)
workers = 4  # Increased for paid tier
worker_class = "sync"
worker_connections = 1000
timeout = 300  # Increased for longer scraping operations
keepalive = 5

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 2000  # Increased for paid tier
max_requests_jitter = 200

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "emailscope"

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
keyfile = None
certfile = None

# Application
wsgi_module = "render_config:application"

# Preload application for better performance
preload_app = True

# Worker timeout for long-running requests (scraping operations)
worker_timeout = 300

# Graceful timeout for worker shutdown
graceful_timeout = 30