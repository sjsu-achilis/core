# -*- coding: utf-8 -*-
import os
import sys
import collections
import datetime

import requests
from flask import Flask, request, Response
from flask_cors import CORS
import pprint
import json

import query
import templates
from achlib.config import file_config
from achlib.util import logger
from achlib.util.dbutil import db_fetch, db_insup, generate_device_key
from helpers import pretty_print_POST, get_user_details

config = file_config()
log = logger.getLogger(__name__)

application = Flask(__name__)
CORS(application)

HEADER = {'Access-Control-Allow-Origin': '*'}

@application.route('/', methods=['GET'])
def verify():
    log.info('service health')
    return 'service is up'


@application.route('/get_metric', methods=['GET'])
def get_metric(*args, **kwargs):
    '''
    userid, start_timestamp, end_timestamp, metric_label
    '''
    log.info("/get_metric")
    args = request.args.to_dict()
    statement = query.get_metric.format(str(args['userid']),args\
                ['metric_label'],args['start_timestamp'],args['end_timestamp'])

    send_data = {
      u"label": args['metric_label'],
      u"values": []
      }
    log.info('query:  {}'.format(statement))
    result = db_fetch(statement)
    log.info(result)
    for res in result:
        temp = templates.get_metric.copy()
        if res[0]:
            temp["event_timestamp"] = str(res[0])
        if res[1]:
            temp["metric_value"] = str(res[1])
        send_data["values"].append(temp)
    log.info("sent response \n{}".format(pprint.pformat(send_data)))

    return Response(json.dumps(send_data), headers=HEADER, status=200, mimetype='application/json')


@application.route('/get_max_metric', methods=['GET'])
def get_max_metric(*args, **kwargs):
    '''
    userid, start_timestamp, end_timestamp, metric_label
    '''
    log.info("/get_max_metric")
    args = request.args.to_dict()
    statement = query.get_max_metric.format(str(args['userid']),args\
                ['metric_label'],args['start_timestamp'],args['end_timestamp'])

    send_data = {
      u"label": args['metric_label'],
      u"values": []
      }
    log.info('query:  {}'.format(statement))
    result = db_fetch(statement)
    log.info(result)
    for res in result:
        temp = templates.get_max_metric.copy()
        if res[0]:
            temp["event_timestamp"] = str(res[0])
        if res[1]:
            temp["max_metric_value"] = str(res[1])
        send_data["values"].append(temp)
    log.info("sent response \n{}".format(pprint.pformat(send_data)))

    return Response(json.dumps(send_data), headers=HEADER, status=200, mimetype='application/json')


@application.route('/get_questions', methods=['GET'])
def get_questions():
    log.info("/get_questions")
    statement = query.get_questions
    result = db_fetch(statement)
    send_data = []
    for r in result:
        send_data.append(collections.OrderedDict({u"q_id": r[0], u"qst": r[1]}))

    return Response(json.dumps(send_data), headers=HEADER, status=200, mimetype='application/json')


@application.route('/get_sports', methods=['GET'])
def get_sports():
    log.info('/get_sports')
    statement = query.get_sports
    result = db_fetch(statement)
    send_data = []
    for r in result:
        send_data.append(collections.OrderedDict({u"s_id": r[0], u"s_nsme": r[1], u"s_type":r[2]}))

    return Response(json.dumps(send_data), headers=HEADER, status=200, mimetype='application/json')


@application.route('/is_uid_available', methods=['GET'])
def is_uid_available():
    log.info('/is_uid_available')
    args = (request.args.to_dict()["userid"],)
    statement = query.is_uid_available
    result = set(db_fetch(statement))
    send_data = {"avl": args not in result}

    return Response(json.dumps(send_data), headers=HEADER, status=200, mimetype='application/json')


@application.route('/login_info', methods=['OPTIONS','POST'])
def login_info():
    log.info('/login_info')
    pretty_print_POST(request)
    response = json.loads(request.data)
    for_users_table_vals = "('{}','{}','{}','{}','{}')".format(response["name"],response["email"],response\
                                                   ["userid"],response["password"],generate_device_key())
    statement = query.login_info.format(for_users_table_vals)
    log.info("query: {}".format(statement))
    ok = db_insup(statement)

    return Response(json.dumps({"msg": ok}), headers=HEADER, status=200, mimetype='application/json')


@application.route('/register_user_info', methods=['OPTIONS','POST'])
def register_user_info():
    log.info("/register_user_info")
    pretty_print_POST(request)
    response = json.loads(request.data)
    for_users_info_table_vals = "('{}',{},'{}',{},{},'{}','{}',{})".\
                                format(response["userid"],response["age"],\
                                response["gender"],response["height"],response["weight"],\
                                response["s_id"],response["org"],response["role"])
    statement = query.register_user_info.format(for_users_info_table_vals)
    log.info("query: {}".format(statement))
    ok = db_insup(statement)

    return Response(json.dumps({"register": ok}), headers=HEADER, status=200, mimetype='application/json')


@application.route('/save_response', methods=['OPTIONS','POST'])
def save_response():
    log.info("/save_response")
    pretty_print_POST(request)
    response = json.loads(request.data)
    uid = response["user_id"]
    val = ""
    for a in response["answers"]:
        val += ",('{}','{}','{}','{}')".format(uid,a["qid"],a["ans"],str(datetime.datetime.now()).split('.')[0])
    log.info("query: {}".format(query.save_response_ins.format(val[1:])))
    ok = db_insup(query.save_response_ins.format(val[1:]))

    return Response(json.dumps({"msg": ok}), headers=HEADER, status=200, mimetype='application/json')


@application.route('/edit_qstn_response', methods=['OPTIONS','POST'])
def edit_qstn_response():
    pretty_print_POST(request)
    log.info("/edit_qstn_response")
    response = json.loads(request.data)
    uid = response["user_id"]
    send_response = []
    for a in response["answers"]:
        statement = query.edit_qstn_response.format(a["ans"],uid,a["qid"])
        log.info("query: {}".format(statement))
        ok = db_insup(statement)
        if ok:
            send_response.append(a["qid"])

    return Response(json.dumps({"updated_qids":send_response}), headers=HEADER, status=200, mimetype='application/json')



@application.route('/register_injury', methods=['OPTIONS','POST'])
def register_injury():
    log.info("/register_injury")
    pretty_print_POST(request)
    response = json.loads(request.data)
    if response["date"]:
        date = response["date"]
    else:
        date = str(datetime.datetime.now()).split('.')[0]
    val = "('{}','{}','{}','{}','{}','{}',{})".format(response["userid"],response["desc"],\
          date,response["type"],response["location"],response["region"],response["intensity"])
    statement = query.register_injury.format(val)
    log.info("query: {}".format(statement))
    ok = db_insup(statement)

    return Response(json.dumps({"msg": ok}), headers=HEADER, status=200, mimetype='application/json')


@application.route('/get_user_info', methods=['OPTIONS','POST'])
def get_user_info_post():
    log.info('/get_user_info')
    pretty_print_POST(request)
    response = json.loads(request.data)
    statement_validate = query.get_user_info_validate_user.format(response["userid"])
    log.info("query: {}".format(statement_validate))
    result = db_fetch(statement_validate)
    if len(result) == 0:
        return Response(json.dumps({"error": "user not registered"}), headers=HEADER, status=200, mimetype='application/json')
    if result[0][0] != response["password"]:
        return Response(json.dumps({"error": "password invalid"}), headers=HEADER, status=200, mimetype='application/json')
    user_data = get_user_details(response["userid"])

    return Response(json.dumps(user_data), headers=HEADER, status=200, mimetype='application/json')


@application.route('/update_user_info', methods=['OPTIONS','POST'])
def update_user_info():
    pretty_print_POST(request)
    log.info("/update_user_info")
    response = json.loads(request.data)
    uid = response["userid"]
    statement_update_users = query.update_user_info_1.format(response["name"],response["email"],uid)
    log.info("query: {}".format(statement_update_users))
    ok_users = db_insup(statement_update_users)

    statement_update_user_info = query.update_user_info_2.format(response["age"],response["gender"],\
                                 response["height"],response["weight"],response["sport_id"],\
                                 response["organization"],response["role"],uid)
    log.info("query: {}".format(statement_update_user_info))
    ok_user_information = db_insup(statement_update_user_info)
    ok = ok_users and ok_user_information

    return Response(json.dumps({"update":ok}), headers=HEADER, status=200, mimetype='application/json')


@application.route('/get_user_info', methods=['GET'])
def get_user_info_get():
    log.info('/get_user_info')
    args = request.args.to_dict()["userid"]
    user_data = get_user_details(args)

    return Response(json.dumps(user_data), headers=HEADER, status=200, mimetype='application/json')


@application.route('/get_injury_history', methods=['GET'])
def get_injury_history():
    log.info('/get_injury_history')
    args = request.args.to_dict()["userid"]
    statement = query.get_injury_history.format(args)
    log.info("query: {}".format(statement))
    result = db_fetch(statement)
    send_data = []
    for res in result:
        injury_data = templates.get_injury_data.copy()
        injury_data["desc"],injury_data["date"],injury_data["type"],\
        injury_data["location"],injury_data["region"],injury_data["intensity"]\
        = res[1],str(res[2]),res[3],res[4],res[5],res[6]
        send_data.append(injury_data)

    return Response(json.dumps(send_data), headers=HEADER, status=200, mimetype='application/json')


@application.route('/register_device_key', methods=['OPTIONS','POST'])
def register_device_key():
    log.info("/register_device_key")
    pretty_print_POST(request)
    response = json.loads(request.data)
    statement = query.register_device_key.format(response["device_key"],response["user_id"])
    log.info("query: {}".format(statement))
    ok = db_insup(statement)

    return Response(json.dumps({"msg": ok}), headers=HEADER, status=200, mimetype='application/json')


@application.route('/get_device_key', methods=['GET'])
def get_device_key():
    log.info('/get_device_key')
    args = request.args.to_dict()["userid"]
    statement = query.get_device_key.format(args)
    log.info("query: {}".format(statement))
    result = db_fetch(statement)

    return Response(json.dumps({"device_key":result[0][0]}), headers=HEADER, status=200, mimetype='application/json')


@application.route('/get_id_from_device_key', methods=['GET'])
def get_id_from_device_key():
    log.info('/get_id_from_device_key')
    args = request.args.to_dict()["device_key"]
    statement = query.get_id_from_device_key.format(args)
    log.info("query: {}".format(statement))
    result = db_fetch(statement)
    send_data = "device_key does not exist"
    if len(result)>0:
        send_data = result[0][0]
    
    return Response(json.dumps({"user_id":send_data}), headers=HEADER, status=200, mimetype='application/json')


@application.route('/get_question_response', methods=['GET'])
def get_question_response():
    log.info('/get_question_response')
    args = request.args.to_dict()["userid"]
    statement = "SELECT qid,question from questionnaire"
    log.info("query: {}".format(statement))
    result = db_fetch(statement)
    lookup = dict(result)
    
    statement = query.get_question_response.format(args)
    log.info("query: {}".format(statement))
    result = db_fetch(statement)

    send_ans = []
    for res in result:
        send_ans.append({"qid": res[0], "qstn":lookup[res[0]], "response":res[1]})
    
    return Response(json.dumps({"user_id":args, "answers":send_ans}), headers=HEADER, status=200, mimetype='application/json')


@application.route('/post_event', methods=['OPTIONS','POST'])
def post_event():
    log.info("/post_event")
    pretty_print_POST(request)
    response = json.loads(request.data)
    start_date = '-'.join([response["start"]["year"],response["start"]["month"],response["start"]["day"]])
    start_time = ':'.join([response["start"]["hours"],response["start"]["minutes"],response["start"]["seconds"]])
    start = ' '.join([start_date,start_time])
    end_date = '-'.join([response["end"]["year"],response["end"]["month"],response["end"]["day"]])
    end_time = ':'.join([response["end"]["hours"],response["end"]["minutes"],response["end"]["seconds"]])
    end = ' '.join([end_date,end_time])
    created = str(datetime.datetime.now()).split('.')[0]
    
    vals = "('{}','{}','{}','{}','{}','{}')".format(start,created,response["desc"],response["title"],end,response["userid"])
    statement = query.post_event.format(vals)
    log.info("query: {}".format(statement))
    ok = db_insup(statement)

    return Response(json.dumps({"event_created": ok}), headers=HEADER, status=200, mimetype='application/json')


@application.route('/get_event', methods=['GET'])
def get_event():
    log.info('/get_event')
    args = request.args.to_dict()["userid"]
    statement = query.get_event.format(args)
    log.info("query: {}".format(statement))
    result = db_fetch(statement)
    print result
    send_data = []
    for res in result:
        event_data = templates.get_event.copy()
        start_day_split,start_time_split,end_day_split,end_time_split = \
        str(res[0]).split(' ')[0].split("-"), str(res[0]).split(' ')[1].split(":"),\
        str(res[1]).split(' ')[0].split("-"), str(res[1]).split(' ')[1].split(":")

        start,end = templates.get_event_sched.copy(), templates.get_event_sched.copy()

        start["year"],start["month"],start["day"],start["hours"],start["minutes"],start["seconds"] = \
        start_day_split[0],start_day_split[1],start_day_split[2],start_time_split[0],start_time_split[1],\
        start_time_split[2]

        end["year"],end["month"],end["day"],end["hours"],end["minutes"],end["seconds"] = \
        end_day_split[0],end_day_split[1],end_day_split[2],end_time_split[0],end_time_split[1],\
        end_time_split[2]

        event_data["start"],event_data["end"],event_data["description"], event_data["title"] = \
        start,end,res[2],res[3]

        send_data.append(event_data)


    return Response(json.dumps({"userid":args, "events":send_data}), headers=HEADER, status=200, mimetype='application/json')


@application.route('/register_app_instance', methods=['OPTIONS','POST'])
def register_app_instance():
    log.info("/register_app_instance")
    pretty_print_POST(request)
    response = json.loads(request.data)
    statement = query.register_app_instance.format(response["userid"],response["appid"])
    log.info("query: {}".format(statement))
    ok = db_insup(statement)

    return Response(json.dumps({"event_created": ok}), headers=HEADER, status=200, mimetype='application/json')


@application.route('/get_coach_types', methods=['GET'])
def get_coach_types():
    log.info('/get_coach_types')
    statement = query.get_coach_types
    log.info("query: {}".format(statement))
    result = db_fetch(statement)
    send_data = []
    for r in result:
        send_data.append(collections.OrderedDict({u"type_id": r[0], u"type": r[1]}))

    return Response(json.dumps(send_data), headers=HEADER, status=200, mimetype='application/json')


@application.route('/get_athelete_ids', methods=['GET'])
def get_athelete_ids():
    log.info('/get_athelete_ids')
    args = request.args.to_dict()["coachid"]
    statement1 = query.get_athelete_ids1.format(args)
    log.info("query: {}".format(statement1))
    result = db_fetch(statement1)
    send_data = []
    if len(result)>0:
        statement2 = query.get_athelete_ids2.format(result[0][0])
        log.info("query: {}".format(statement2))
        result = db_fetch(statement2)
        for r in result:
            if r[0] != args:
                send_data.append(r[0])

    return Response(json.dumps({"athelete_ids":send_data}), headers=HEADER, status=200, mimetype='application/json')


@application.route('/register_coach_student', methods=['OPTIONS','POST'])
def register_coach_student():
    log.info("/register_coach_student")
    pretty_print_POST(request)
    response = json.loads(request.data)
    send_data = []
    for ath in response["athlete_ids"]:
        statement = query.register_coach_student.format(ath,response["userid"],\
                    str(datetime.datetime.now()).split('.')[0],response["type_id"])   
        log.info("query: {}".format(statement))
        if db_insup(statement):
            send_data.append(ath)

    return Response(json.dumps({"inserted": send_data}), headers=HEADER, status=200, mimetype='application/json')



if __name__ == '__main__':
    application.run(host='0.0.0.0', debug=True)
