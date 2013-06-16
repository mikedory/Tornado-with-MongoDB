#   main.py - Tornado with MongoDB
#
#   Author: Mike Dory
#       10.20.12
#

#!/usr/bin/env python
import os.path
import os
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import json

import pymongo

# import and define tornado-y things
from tornado.options import define, options
define("port", default=5000, help="run on the given port", type=int)
define("mongo_url", default="localhost", help="location of mongodb", type=str)
define("mongo_port", default=27017, help="port mongodb is listening on", type=int)
define("mongo_dbname", default="sampledb", help="name of the database", type=str)


# application settings and handle mapping info
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/([^/]+)?", MainHandler),
            (r"/samples/([^/]+)?", SampleHandler)
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
        )
        conn = pymongo.Connection(options.mongo_url, options.mongo_port)
        self.db = conn[options.mongo_dbname]
        tornado.web.Application.__init__(self, handlers, **settings)


# the main page
class MainHandler(tornado.web.RequestHandler):
    def get(self, q=None):
        # find all posts
        coll = self.application.db.samples
        sample_data = coll.find()

        # render 'em out'
        self.render(
            "main.html",
            page_title='Database funtimes',
            page_heading='Mongo is fun for everyone!',
            page_footer='by @mike_dory',
            sample_data=sample_data
        )


# the API handler for get/post requests
class SampleHandler(tornado.web.RequestHandler):
    def get(self, sample_id=None):
        sample = dict()
        if sample_id:
            # grab the sample that matches
            coll = self.application.db.samples
            sample = coll.find_one({"id": sample_id})

            # write out a response
            self.set_header('Content-Type', 'application/json')
            sample_response = {
                "id": sample["id"],
                "title": sample["title"],
                "text": sample["text"],
                "date_added": sample["date_added"]
            }
            self.write(json.dumps(sample_response))
        else:
            # return a 404 =(
            self.set_status(404)

    def post(self, sample_id=None):
        import time
        coll = self.application.db.samples

        # shape our fields properly
        sample_fields = ['id', 'title', 'text']
        sample = dict()

        # if posting to a specific ID
        if sample_id:
            sample_result = coll.find_one({"id": sample_id})
        elif self.get_argument("id") is not None:
            sample_result = coll.find_one({"id": self.get_argument("id")})
        else:
            sample_result = None
        if sample_result is not None:
            sample = sample_result

        # format the incoming data all nicely
        for key in sample_fields:
            sample[key] = self.get_argument(key, None)

        # if the document exists, update it. otherwise, make a new one.
        if (sample_id == sample["id"]):
            coll.update(sample)
        else:
            sample['date_added'] = int(time.time())
            coll.insert(sample)

        # success!
        self.set_status(200)


# let's do this
def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(os.environ.get("PORT", 5000))

    # start it up
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
