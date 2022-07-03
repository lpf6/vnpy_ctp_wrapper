import logging


def get_log():
    log = logging.getLogger("vnpy_gateway_wrapper")
    log.setLevel(logging.DEBUG)
    fh = logging.FileHandler('vnpy_gateway_wrapper.log')
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    # add the handlers to logger
    log.addHandler(ch)
    log.addHandler(fh)
    return log

log = get_log()
