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
        'https://oplaadpalen.nl/wms?REQUEST=GetFeatureInfo&SERVICE=WMS&SRS=EPSG%3A4326&VERSION=1.1.1&INFO_FORMAT=application%2Fjson&BBOX=4.435096979141236%2C52.12392140665582%2C4.453373551368714%2C52.126305847735765&HEIGHT=724&WIDTH=3407&LAYERS=eco%3Arta_and_clusters&QUERY_LAYERS=eco%3Arta_and_clusters&X=1483&Y=220',
        'https://oplaadpalen.nl/wms?REQUEST=GetFeatureInfo&SERVICE=WMS&SRS=EPSG%3A4326&VERSION=1.1.1&INFO_FORMAT=application%2Fjson&BBOX=4.426814317703248%2C52.12497246674536%2C4.463367462158204%2C52.12974110884798&HEIGHT=724&WIDTH=3407&LAYERS=eco%3Arta_and_clusters&QUERY_LAYERS=eco%3Arta_and_clusters&X=1520&Y=294',
        'https://oplaadpalen.nl/wms?REQUEST=GetFeatureInfo&SERVICE=WMS&SRS=EPSG%3A4326&VERSION=1.1.1&INFO_FORMAT=application%2Fjson&BBOX=4.43524718284607%2C52.12657251589268%2C4.4535934925079355%2C52.12903585048001&HEIGHT=748&WIDTH=3420&LAYERS=eco%3Arta_and_clusters&QUERY_LAYERS=eco%3Arta_and_clusters&X=1597&Y=317'
    ]

    for charger in chargers_to_check:
        r = requests.get(charger)
        logger.info(r.text)
        if r.status_code != requests.codes.ok:
            logger.warning('Something went wrong getting the charger location: %s', r.status_code)
            context.bot.send_message(chat_id=chat_id, text="I could not retrieve the location of the charger. Someone needs to look into this!")
            continue
        charger_ref = r.json()['features'][0]['properties']['external_reference']
        r = requests.get(f'https://oplaadpalen.nl/api/map/location/{charger_ref}')
        logger.info(r.text)
        if r.status_code != requests.codes.ok:
            logger.warning('Something went wrong getting the charger info: %s', r.status_code)
            context.bot.send_message(chat_id=chat_id, text="I could not retrieve the status information of the charger. Someone needs to look into this!")
            continue
        data = r.json()['data']
        address = data['address']
        sockets = data['evses']
        #tariffs = sockets[0]['connectors'][0]['tariffs'][0]
    
        #tariff = tariffs['price'] + (tariffs['price'] * (tariffs['vat'] / 100))
        #currency = tariffs['currency']

        num_available = 0
        for s in sockets:
            num_available += (1 if s['status'] == 'AVAILABLE' else 0)
               
        context.bot.send_message(chat_id=chat_id, text=f'{num_available} socket(s) available at {address}')


bot = Bot(token=os.environ["TOKEN"])

dispatcher = Dispatcher(bot=bot, update_queue=None, workers=1)
dispatcher.add_handler(CommandHandler('check', check))

@app.route("/", methods=["POST"])
def index() -> Response:
    dispatcher.process_update(
        Update.de_json(request.get_json(force=True), bot)
    )

    return "", http.HTTPStatus.NO_CONTENT
