from flask_restful import Resource, Api
from flask import jsonify, request, current_app
import sqlite3
import time
import hashlib
import logging
import random
import datetime

class Query(Resource):
    def get(self, userid):
        sqlqry = "SELECT * FROM accounts WHERE account=? ORDER BY timestamp"
        current_app.config.from_pyfile('config/settings.py')
        logging.basicConfig(filename=current_app.config["LOGFILE"], 
                            filemode='w',
                            format='%(asctime)s - %(levelname)s - usr=%(name)s %(message)s',
                            level=logging.INFO,
                            datefmt='%Y-%m-%d %H:%M:%S')
        logging.info("op=qry acct="+userid+" status=recived")
        with sqlite3.connect(current_app.config["DBPROCS"]) as con:
            cur = con.cursor()
            cur.execute(sqlqry,(userid,))
            rec = cur.fetchone()
            if rec:
                logging.info("op=qry acct="+userid+" status=success")
                return jsonify({'retval':"OK",
                                'hash':rec[0],
                                'timestamp':datetime.datetime.fromtimestamp(rec[1]).strftime('%Y-%m-%d %H:%M:%S'),
                                'account':rec[2],
                                'dequeue_time':datetime.datetime.fromtimestamp(rec[3]).strftime('%Y-%m-%d %H:%M:%S'),
                                'finish_time':datetime.datetime.fromtimestamp(rec[4]).strftime('%Y-%m-%d %H:%M:%S'),
                                'result':rec[5]
                                })
            else:
                logging.warning("op=qry acct="+userid+" status=account not found")
                return jsonify({'retval':"Error",
                                'hash':"-",
                                'timestamp':"-",
                                'account':"-",
                                'dequeue_time':"-",
                                'finish_time':"-",
                                'result':"Account not found"
                                })
