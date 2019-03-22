import praw
from praw.models import Message
from praw.exceptions import APIException
import traceback
import logging
import json
import random
import time

# very important logging stuff
logger = logging.getLogger('prawcore')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('log.log')
fh.setLevel(logging.WARNING)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# we are storing everything in a json file. I wasnt prepared for that amount, shhh
database = json.load(open('./database.json'))

# subreddits where the bot should do nothing
Blacklist = ["Animemes"]


class Database(object):

    def __init__(self):
        self.redditors = []

    def to_dict(self):
        return {'redditors': self.redditors}

    def from_dict(self, submissions_dict):
        self.redditors = submissions_dict.get("redditors")

    def add_redditor(self, redditor_name):
        skip = False
        for name in self.redditors:
            if name == redditor_name:
                return False
        if not skip:
            self.redditors.append(redditor_name)
            return True

    def remove_redditor(self, redditor_name):
        try:
            self.redditors.remove(redditor_name)
            return True
        except ValueError:
            return False

    def get_redditors(self):
        temp = self.redditors
        random.shuffle(temp)
        return temp


databasestuff = Database()
databasestuff.from_dict(database)


def main():
    reddit = praw.Reddit(user_agent='im booping',
                         client_id='', client_secret='',
                         username="srgrafo_bot", password="!")
    submission_stream = reddit.redditor('SrGrafo').stream.submissions(skip_existing=True, pause_after=-1)
    inbox_stream = reddit.inbox.stream(skip_existing=True, pause_after=-1)
    while True:
        try:
            for submission in submission_stream:
                if submission:
                    if submission.subreddit in Blacklist:
                        logger.warning("Got post from blacklist, didnt do anything.")
                        break
                    else:
                        logger.warning("Did post " + submission.permalink)
                        process_submission(submission, reddit)
                else:
                    break
            for item in inbox_stream:
                if item:
                    process_item(item, reddit)
                else:
                    break
        except Exception as e:
            logger.warning("Error in main function")
            logger.warning(traceback.format_exc())
            seconds = 150
            recovered = False
            for num in range(1, 4):
                time.sleep(seconds)
                try:
                    if reddit.user.me():
                        recovered = True
                except Exception as err:
                    seconds = seconds * 2
                    break
            problemStrList = []
            if recovered:
                logger.warning("Messaging owner that that we recovered from a problem")
                problemStrList.append("Recovered from an exception after " + str(seconds) + " seconds.")
                problemStrList.append("\n\n*****\n\n")
                if not reddit.redditor("JustCallMePoolitzer").message("Recovered", ''.join(problemStrList)):
                    logger.warning("Could not send message to owner when notifying recovery")
            else:
                logger.warning("Messaging owner that that we failed to recover from a problem")
                problemStrList.append("Failed to recovered from an exception after " + str(seconds) + " seconds.")
                problemStrList.append("\n\n*****\n\n")
                if not reddit.redditor("JustCallMePoolitzer").messagge("Failed recovery", ''.join(problemStrList)):
                    logger.warning("Could not send message to owner when notifying failed recovery")


def process_submission(submission, reddit):
    skip = False
    insert = len(databasestuff.get_redditors())
    content = "This should never be seen, but if it does, here is the submission: {}"
    fallback = "This should never be seen, but if it does, here is the submission: {}"
    for message in reddit.inbox.messages():
        if message.author.name == "SrGrafo":
            content = message.body
            try:
                content = content.format(submission.permalink)
            except KeyError:
                content = fallback.format(submission.permalink)
            if "private" in message.subject.lower():
                skip = True
            break
    if not skip:
        submission.reply(
            f"Hello there.\n\nI'm a little bot which follows **SrGrafo** around and can notify you to new posts from him, "
            f"regardless where he posts.\n\nIn order to get notifications from me like {insert} redditors right now, "
            f"you need to send me a message with the word _subscribe_ in it. Doesn't matter if it is a comment or a "
            f"[PM](https://np.reddit.com/message/compose/?to=srgrafo_bot&message=Could+you+subscribe+me+please+ty"
            f"&subject=Doesn't+matter).\n\nTo unsubscribe, just do the same with the word _unsubscribe_. Either a PM or "
            f"a comment.\n\nSince a "
            f"lot of you guys decided to use me, it takes me quite some time to notify you all. This also means that I "
            f"won't send you a PM that you successfully subscribed right away since I am busy notificating other "
            f"redditors. Please give me up to two hours to get this done.\n\nIf you are an moderator of the current "
            f"subreddit I'm commenting in and don't want me to do that, please ping my creator u/JustCallMePoolitzer. He "
            f"will blacklist your subreddit then.\n\n Have a great day :)")
    # lets count the time
    start_time = time.time()
    for username in databasestuff.get_redditors():
        try:
            reddit.redditor(username).message(f"New SrGrafo Post!", content)
        except APIException:
            databasestuff.remove_redditor(username)
            pass
    elapsed_time = time.time() - start_time
    logger.warning(elapsed_time)
    formatted = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
    reddit.redditor("SrGrafo").message("Elapsed time", formatted)
    reddit.redditor("JustCallMePoolitzer").message("Elapsed time", formatted)


def process_item(item, reddit):
    skip = False
    if not item:
        logger.error("some weird shit is happening here " + item)
    else:
        if "unsubscribe" in item.body.lower():
            if databasestuff.remove_redditor(item.author.name):
                content = "Sad to see you go :( Mind telling me if something was wrong on my side? You can do it here on " \
                          "reddit (u/JustCallMePoolitzer) or on telegram (https://t.me/poolitzer)."
                if isinstance(item, Message):
                    item.reply(content)
                else:
                    reddit.redditor(item.author.name).message("Successfully unsubscribed", content)
            else:
                content = "You were already unsubscribed, nothing to worry about :)"
                if isinstance(item, Message):
                    item.reply(content)
                else:
                    reddit.redditor(item.author.name).message("Really successfully unsubscribed", content)
            item.mark_read()
        elif "subscribe" in item.body.lower():
            process_subcription(item, reddit)
        elif "suscribe"in item.body.lower():
            process_subcription(item, reddit)
        elif "sub" in item.body.lower():
            process_subcription(item, reddit)
        else:
            if isinstance(item, Message):
                reddit.redditor("SrGrafo").message("New message " + item.subject, item.body)
            else:
                reddit.redditor("SrGrafo").message("New comment", item.body + "\n\n" + item.context)
            skip = True
            item.mark_read()
        if not skip:
            with open('./database.json', 'w') as outfile:
                json.dump(databasestuff.to_dict(), outfile, indent=4, sort_keys=True)


def process_subcription(item, reddit):
    if databasestuff.add_redditor(item.author.name):
        content = "I will notify you from now on to new post from u/SrGrafo. If you don't want that anymore, " \
                  "just send me a PM with _unsubscribe_ in it. If you got anything to say to my developer, " \
                  "PM u/JustCallMePoolitzer here or on [telegram](https://t.me/poolitzer). "
        if isinstance(item, Message):
            item.reply(content)
        else:
            reddit.redditor(item.author.name).message("Successfully subscribed", content)
    else:
        content = "You were already subscribed, nothing to worry about :)"
        if isinstance(item, Message):
            item.reply(content)
        else:
            reddit.redditor(item.author.name).message("Really successfully subscribed", content)
    item.mark_read()


if __name__ == '__main__':
    main()
