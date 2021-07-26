# Telegram Channel Comments Helper

[@comments_helper_bot](https://t.me/comments_helper_bot)

## Features

* Auto attach a poll to each channel message in discussion group
    * Even if the message is a media group, would not send duplicated polls like similar bots
    * Polls can be customized
* Auto remove any user (and ban for 60s) attempting to join the discussion group
    * Only if granted "Ban user" permission

## Usage

* Add [@comments_helper_bot](https://t.me/comments_helper_bot) to the **discussion group** of a channel
* Grant `Ban users` permission if needed
* `/set_poll` to set customized polls

## Deployment

### AWS Lambda

1. Clone
    ```sh
    git clone https://github.com/Rongronggg9/comments-helper-bot
    cd comments-helper-bot
    ```
1. Install dependencies
    ```sh
    npm install serverless -g
    npm install
    ```
1. [Get an AWS Access Key and configure it locally](https://www.serverless.com/framework/docs/providers/aws/guide/credentials/)
1. Create `serverless.env.yml`
    ```yaml
    TOKEN: <your token>
    REDIS_HOST: <your redis host> # optional, customized poll will be enabled if set
    REDIS_PORT: <redis port> # optional
    REDIS_PASSWORD: <redis password> # optional
    ```

1. Deploy
    ```sh
    serverless deploy --region <AWS region>
    ```
1. Activate Webhook
    * GET or POST the `set_webhook` endpoint. It should be like:
    ```
    https://<depends-on-your-deployment>.amazonaws.com/dev/set_webhook
    ```

### Docker
_not tested_

For the docker image go to: https://hub.docker.com/r/rongronggg9/comments-helper-bot

```sh
docker run \
 --restart unless-stopped \
 -e TOKEN=<bot token> \
 -e T_PROXY=<scheme://host:port/> \
 -e REDIS_HOST=<redis host> \
 -e REDIS_PORT=<redis port> \
 -e REDIS_PASSWORD=<redis password>
 rongronggg9/comments-helper-bot
```
