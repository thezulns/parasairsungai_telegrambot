#!/usr/bin/env python

"""
Simple Bot to send periodic Telegram messages.

This Bot uses the Updater class to handle the bot and the JobQueue to send
timed messages.

Usage:
/set <hours>
Press Ctrl-C on the command line or send a signal to the process to stop 
"""

import logging

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

import wget
from bs4 import BeautifulSoup
from urllib.request import urlopen
import ssl

ssl._create_default_https_context = ssl._create_unverified_context


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
# Best practice would be to replace context with an underscore,
# since context is an unused local variable.
# This being an example and not having context present confusing beginners,
# we decided to have it present as context.
def start(update: Update, context: CallbackContext) -> None:
	"""Sends explanation on how to use the bot."""
	update.message.reply_text('This is Sg Pedas Water level bot. \nUse /set to receive hourly Water level update')

def now(update: Update, context: CallbackContext) -> None:
	"""Retrieve water-level right away from Info Banjir MY gov"""

	url = "https://publicinfobanjir.water.gov.my/aras-air/data-paras-air/aras-air-data/?state=NSN&district=Rembau&station=2520032_&lang=en"
	contents  = urlopen(url).read()
	soup = BeautifulSoup(contents, features="html.parser")

	parent_node = soup.find("tr", {"class":"item"})
	child_data = parent_node.findAll('td',{'data-th':['Station Name', 'Last Update', 'wl', 'Normal', 'Alert', 'Warning', 'Danger']})

	store_data = []
	for child in child_data:
		"""store_data = child['data-th'] + ' = ' + child.text + '\n' """
		store_data.append(child['data-th'] + ' = ' + child.text)
	store_data = '\n'.join(store_data)
	update.message.reply_text(store_data)

def send_parasair(context: CallbackContext) -> None:
	"""
	Retrieve the water-level from a periodic job
	Pull website data from link using BeautifulSoup
	"""

	url = "https://publicinfobanjir.water.gov.my/aras-air/data-paras-air/aras-air-data/?state=NSN&district=Rembau&station=2520032_&lang=en"
	contents  = urlopen(url).read()
	soup = BeautifulSoup(contents, features="html.parser")

	parent_node = soup.find("tr", {"class":"item"})
	child_data = parent_node.findAll('td',{'data-th':['Station Name', 'Last Update', 'wl', 'Normal', 'Alert', 'Warning', 'Danger']})

	store_data = []
	for child in child_data:
		"""print(child['data-th'], "=", child.text)"""
		store_data.append(child['data-th'] + ' = ' + child.text) 
	store_data = '\n'.join(store_data)

	"""Send the water-level message."""
	job = context.job
	context.bot.send_message(job.context, store_data)

def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def set_timer(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id

    job_removed = remove_job_if_exists(str(chat_id), context)
    context.job_queue.run_repeating(send_parasair, 3600, context=chat_id, name=str(chat_id))

    text = 'Periodic updates successfully set!'
    if job_removed:
       text += ' Old one was removed.'
    update.message.reply_text(text)

    """except (IndexError, ValueError):
        update.message.reply_text('Usage: /set')"""

def unset(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Periodic updates successfully cancelled!' if job_removed else 'You have no active periodic updates.'
    update.message.reply_text(text)


def main() -> None:
	"""Run Sungai ..... Water Level bot."""
	# Create the Updater and pass it your bot's token.
	updater = Updater("TOKEN")

	# Get the dispatcher to register handlers
	dispatcher = updater.dispatcher

	# on different commands - answer in Telegram
	dispatcher.add_handler(CommandHandler("start", start))
	dispatcher.add_handler(CommandHandler("help", start))
	dispatcher.add_handler(CommandHandler("set", set_timer))
	dispatcher.add_handler(CommandHandler("unset", unset))
	dispatcher.add_handler(CommandHandler("now", now))

	# Start the Bot
	updater.start_polling()

	# Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
	# SIGABRT. This should be used most of the time, since start_polling() is
	# non-blocking and will stop the bot gracefully.
	updater.idle()


if __name__ == '__main__':
    main()
