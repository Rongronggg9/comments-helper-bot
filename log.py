import logging

logger = logging.getLogger()
if logging.getLogger().hasHandlers():
    # for AWS Lambda
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)
