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
        data = event.get('body')
        webhook_handler.webhook(data)

        return OK_RESPONSE
    except Exception as e:
        logger.error('ERROR occurred!', exc_info=e)

    # return ERROR_RESPONSE
    return OK_RESPONSE


def set_webhook(event, context):
    logger.info(f'Event: {event}')
    lambda_stage = event.get('requestContext').get('stage')
    if lambda_stage == '$default' or lambda_stage is None:
        lambda_stage = ''
    else:
        lambda_stage += '/'
    url = \
        f"https://{event.get('requestContext').get('domainName')}/{lambda_stage}{webhook_handler.TOKEN}"
    webhook_successful = webhook_handler.set_webhook(url)

    if webhook_successful:
        return OK_RESPONSE

    return ERROR_RESPONSE
