import os
import http
import requests
import logging
from flask import Flask, request
from werkzeug.wrappers import Response

from telegram import Bot, Update
from telegram.ext import Dispatcher, Filters, CommandHandler, CallbackContext

app = Flask(__name__)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
chat_id = os.environ["CHAT_ID"]


def check(update: Update, context: CallbackContext) -> None:
    chargers_to_check = [
        'a358ef4a11eb9dc242010a840003f992',
        '2ba239eb11ed8d8a42010aa40fc000f0'
    ]

    for charger_ref in chargers_to_check:
        r = requests.get(f'https://oplaadpalen.nl/api/map/location/{charger_ref}')
        logger.info(r.text)
        if r.status_code != requests.codes.ok:
            logger.warning('Something went wrong getting the charger info: %s', r.status_code)
            context.bot.send_message(chat_id=chat_id, text="I could not retrieve the status information of the charger. Someone needs to look into this!")
            continue
        data = r.json()['data']
        address = data['address']
        sockets = data['evses']
        tariff = "costs unknown"
        try:
            tariffs = sockets[0]['connectors'][0]['tariffs'][0]
            tariff = str(tariffs['price'] + (tariffs['price'] * (tariffs['vat'] / 100))) + tariffs['currency'] + "/kWh"
        except IndexError:
            logger.warning('Could not retrieve tariff information, defaulting to unavailable')
        num_available = 0
        for s in sockets:
            num_available += (1 if s['status'] == 'AVAILABLE' else 0)
               
        context.bot.send_message(chat_id=chat_id, text=f'{num_available} socket(s) available at {address} ({tariff})')

bot = Bot(token=os.environ["TOKEN"])

dispatcher = Dispatcher(bot=bot, update_queue=None, workers=1)
dispatcher.add_handler(CommandHandler('check', check))

@app.route("/", methods=["POST"])
def index() -> Response:
    dispatcher.process_update(
        Update.de_json(request.get_json(force=True), bot)
    )

    return "", http.HTTPStatus.NO_CONTENT
