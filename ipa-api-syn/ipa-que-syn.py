#!/usr/bin/env python

import sys
import os
import sqlite3
import time
import subprocess
import yaml
import logging
from yaml import load, dump, Loader, Dumper

get_acct_qry = "SELECT * FROM accounts ORDER BY timestamp ASC LIMIT 1"
del_acct_qry = "DELETE FROM accounts WHERE hash=?"
ins_acct_qry = "INSERT INTO accounts(hash,timestamp,account,dequeue_time,finish_time,return) VALUES(?,?,?,?,?,?)"
upd_acct_qry = "UPDATE accounts SET finish_time=?, return=? WHERE hash=?" 

conffile = sys.argv[1]
with open(conffile, "r") as f:
    cfg = yaml.load(f, Loader=Loader)

db_input = cfg["db_input"]
db_processed = cfg["db_processed"]
script = cfg["script"]
consumer_log = cfg["consumer_logfile"]

logging.basicConfig(filename=consumer_log,
                    filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')
logging.info("op=quesyn status=started")
while True:
   row_hash=""
   row_time=""
   row_acct=""
   with sqlite3.connect(db_input) as con_input:
       cur = con_input.cursor()
       cur.execute(get_acct_qry)
       rec = cur.fetchone()
       if rec:
           row_hash = rec[0]
           row_time = rec[1]
           row_acct = rec[2]
  
   if row_hash != "":
       logging.info("op=quesyn acct=" + row_acct + " status=processing")
       with sqlite3.connect(db_processed) as con_proc:
           con_proc.execute(ins_acct_qry,(row_hash,row_time,row_acct,time.time(),0,""))
           con_proc.commit()

       logging.info("op=quesyn acct=" + row_acct + " status=account_inserted")
       process = subprocess.Popen(script, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
       stdout, stderr = process.communicate()
       rc = process.returncode
       if stdout != "":
           result = stdout
       else:
           result = stderr
       logging.info("op=quesyn acct=" + row_acct + " status=run_script  exit_code="+rc+" output="+result)
       with sqlite3.connect(db_processed) as con_proc:
          con_proc.execute(upd_acct_qry,(time.time(),stdout,row_hash))
          con_proc.commit()

       logging.info("op=quesyn acct=" + row_acct + " status=exectime_updated")
       deleted = False
       while not deleted:
           with sqlite3.connect(db_input) as con_input:
               con_input.execute(del_acct_qry, (row_hash,))
               con_input.commit()
               deleted = True
               logging.info("op=quesyn acct=" + row_acct + " status=del_inputdb")
           if not deleted:
               time.sleep(2)
       logging.info("op=quesyn acct="+row_acct+" status=finished")
       time.sleep(5)
