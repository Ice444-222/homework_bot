# Telegram Bot for Yandex.Praktikum Homework Service

The goal of this bot is to notify users about the status of their homework 
reviews on the Yandex.Praktikum - Yandex.Homework service. The bot periodically checks 
the review status via the service's API every 10 minutes, and if the status changes, 
it sends a notification to the user.


## How to Run the Project:

Clone the repository and navigate to it in the command line:

```
git clone git@github.com:Ice444-222/homework_bot.git 
```

``` 
cd homework_bot
```

Create and activate a virtual environment:
```
python3 -m venv env
```
```
source env/bin/activate
```
Install dependencies from the requirements.txt file:
```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

## Technology Stack:

```
Python 3.9.10
python-telegram-bot 13.7
requests 2.26.0
```

## Description of Operation:
The main logic of the program is described in the main() function, which consists of the following functions:
```
get_api_answer(): Sends a request to the only API endpoint of the Yandex.Homework service, returns information about the latest homework.
parse_status(): Extracts the current status and title of the homework from the information.
send_message(): Sends a message to the Telegram chat.
```

## Environment Variables:
It is safer to store the tokens for accessing the Yandex.Homework API (PRAKTIKUM_TOKEN),
Telegram bot token (TELEGRAM_TOKEN), and Telegram chat ID (TELEGRAM_CHAT_ID) not directly in 
the code but in environment variables. The "location" of storing them depends on 
how you deploy the project; you can store them locally in the .env folder.
