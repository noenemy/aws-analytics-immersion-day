#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import sys
import json
import os
import base64
import traceback
import hashlib

import boto3
from elasticsearch import Elasticsearch
from elasticsearch import RequestsHttpConnection
from requests_aws4auth import AWS4Auth

ES_INDEX, ES_TYPE = (os.getenv('ES_INDEX', 'retail'), os.getenv('ES_TYPE', 'trans'))
ES_HOST = os.getenv('ES_HOST')
REQUIRED_FIELDS = os.getenv('REQUIRED_FIELDS', '').split(',')

AWS_REGION = os.getenv('REGION_NAME', 'us-east-1')

session = boto3.Session(region_name=AWS_REGION)
credentials = session.get_credentials()
credentials = credentials.get_frozen_credentials()
access_key = credentials.access_key
secret_key = credentials.secret_key
token = credentials.token

aws_auth = AWS4Auth(
    access_key,
    secret_key,
    AWS_REGION,
    'es',
    session_token=token
)

es_client = Elasticsearch(
    hosts = [{'host': ES_HOST, 'port': 443}],
    http_auth=aws_auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)
print('[INFO] ElasticSearch Service', json.dumps(es_client.info(), indent=2), file=sys.stderr)


def lambda_handler(event, context):
  import collections

  counter = collections.OrderedDict([('reads', 0),
      ('writes', 0),
      ('invalid', 0),
      ('errors', 0)])

  doc_list = []
  for record in event['Records']:
    try:
      counter['reads'] += 1
      payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
      json_data = json.loads(payload)

      if not all([json_data.get(k, None) for k in REQUIRED_FIELDS]):
        counter['invalid'] += 1
        continue

      doc_id = ':'.join([json_data.get(k, '') for k in REQUIRED_FIELDS])
      json_data['doc_id'] = hashlib.md5(doc_id.encode('utf-8')).hexdigest()[:8]

      es_index_action_meta = {"index": {"_index": ES_INDEX, "_type": ES_TYPE, "_id": json_data['doc_id']}}
      doc_list.append(es_index_action_meta)
      doc_list.append(doc)

      counter['writes'] += 1
    except Exception as ex:
      counter['errors'] += 1
      traceback.print_exc()

  print('[INFO]', ', '.join(['{}={}'.format(k, v) for k, v in counter.items()]), file=sys.stderr)

  try:
    es_bulk_body = '\n'.join([json.dumps(e) for e in doc_list])
    res = es_client.bulk(body=es_bulk_body, index=ES_INDEX, refresh=True)
  except Exception as ex:
    traceback.print_exc()


if __name__ == '__main__':
  kinesis_data = [
    '''{"Invoice": "489434", "StockCode": "85048", "Description": "15CM CHRISTMAS GLASS BALL 20 LIGHTS", "Quantity": 12, "InvoiceDate": "2009-12-01 07:45:00", "Price": 6.95, "Customer_ID": "13085.0", "Country": "United Kingdom"}''',
    '''{"Invoice": "489435", "StockCode": "22350", "Description": "CAT BOWL ", "Quantity": 12, "InvoiceDate": "2009-12-01 07:46:00", "Price": 2.55, "Customer_ID": "13085.0", "Country": "United Kingdom"}''',
    '''{"Invoice": "489436", "StockCode": "48173C", "Description": "DOOR MAT BLACK FLOCK ", "Quantity": 10, "InvoiceDate": "2009-12-01 09:06:00", "Price": 5.95, "Customer_ID": "13078.0", "Country": "United Kingdom"}'''
  ]

  records = [{
    "eventID": "shardId-000000000000:49545115243490985018280067714973144582180062593244200961",
    "eventVersion": "1.0",
    "kinesis": {
      "approximateArrivalTimestamp": 1428537600,
      "partitionKey": "partitionKey-1",
      "data": base64.b64encode(e.encode('utf-8')),
      "kinesisSchemaVersion": "1.0",
      "sequenceNumber": "49545115243490985018280067714973144582180062593244200961"
    },
    "invokeIdentityArn": "arn:aws:iam::EXAMPLE",
    "eventName": "aws:kinesis:record",
    "eventSourceARN": "arn:aws:kinesis:EXAMPLE",
    "eventSource": "aws:kinesis",
    "awsRegion": "us-east-1"
    } for e in kinesis_data]
  event = {"Records": records}
  lambda_handler(event, {})
