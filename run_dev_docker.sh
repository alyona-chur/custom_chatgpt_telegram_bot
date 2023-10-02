#!/bin/bash

docker-compose --env-file config/config.env run -v $(pwd):/code chatgpt_telegram_bot /bin/bash
