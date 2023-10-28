import logging

def config():
    FORMAT = '%(asctime)s %(message)s'
    logging.basicConfig(format=FORMAT,
                        level=logging.INFO)


