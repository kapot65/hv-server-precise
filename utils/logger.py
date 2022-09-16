import logging

def init_logger(args):
    logger = logging.getLogger('rsh_server')
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(args.logfile)
    if args.verbose:
        file_handler.setLevel(logging.DEBUG)
    else:
        file_handler.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler()
    if args.verbose:
        stream_handler.setLevel(logging.DEBUG)
    else:
        stream_handler.setLevel(logging.WARNING)

    fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt)
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    
    return logger