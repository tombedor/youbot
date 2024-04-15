import multiprocessing

# workers = multiprocessing.cpu_count() * 2 + 1  # Number of worker processes
workers = 4
bind = '0.0.0.0:8080'                          # Specifies server binds to the desired IP and port
timeout = 120                                  # Sets a timeouts for worker processes

# Log settings
# accesslog = 'access.log'  # where to log access
# errorlog = 'error.log'    # where to log errors

loglevel = 'info'                       # The level at which to emit logs

proc_name = 'api'                    # Changing the process name for Gunicorn process