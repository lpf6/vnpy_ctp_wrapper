import logging


log_level = logging.INFO

def is_debug():
    return log_level <= logging.DEBUG


def get_log():
    log = logging.getLogger("vnpy_gateway_wrapper")
    log.setLevel(log_level)
    fh = logging.FileHandler('vnpy_gateway_wrapper.log')
    fh.setLevel(log_level)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(filename)s:%(lineno)d[%(thread)d] - %(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    # add the handlers to logger
    log.addHandler(ch)
    log.addHandler(fh)
    return log

log = get_log()
