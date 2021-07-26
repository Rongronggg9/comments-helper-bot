import json

import webhook_handler
from log import logger

OK_RESPONSE = {
    'statusCode': 200,
    'headers': {'Content-Type': 'application/json'},
    'body': json.dumps('ok')
}
ERROR_RESPONSE = {
    'statusCode': 400,
    'body': json.dumps('Oops, something went wrong!')
}


def webhook(event, context):
    logger.info(f'Event: {event}')

    try:
        if event.get('httpMethod') == 'POST' and event.get('body'):
            data = event.get('body')
            webhook_handler.webhook(data)

            return OK_RESPONSE
    except Exception as e:
        logger.error('ERROR occurred!', exc_info=e, stack_info=True)

    # return ERROR_RESPONSE
    return OK_RESPONSE


def set_webhook(event, context):
    logger.info(f'Event: {event}')
    url = \
        f"https://{event.get('headers').get('Host')}/{event.get('requestContext').get('stage')}/{webhook_handler.TOKEN}"
    webhook = webhook_handler.set_webhook(url)

    if webhook:
        return OK_RESPONSE

    return ERROR_RESPONSE
