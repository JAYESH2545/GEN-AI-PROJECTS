import logging
import sys 

def configure_logging(log_level=logging.INFO):
    logging.basicConfig(
        level = logging.INFO,
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers = [
            logging.StreamHandler(sys.stdout)
        ]
    )