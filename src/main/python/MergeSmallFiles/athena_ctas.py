#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import sys
import os
import datetime

import boto3

DATABASE = os.getenv('ATHENA_DATABASE')
OLD_TABLE_NAME = os.getenv('OLD_TABLE_NAME')
NEW_TABLE_NAME = os.getenv('NEW_TABLE_NAME')
WORK_GROUP = os.getenv('WORK_GROUP', 'primary')
OUTPUT_PREFIX = os.getenv('OUTPUT_PREFIX')

AWS_REGION = os.getenv('REGION_NAME', 'us-east-1')

OUTPUT_LOC_FMT = '''{output_prefix}/year={year}/month={month:02}/day={day:02}/hour={hour:02}'''

QUERY_FMT = '''CREATE TABLE {new_table_name}
WITH (
  format = 'PARQUET',
  parquet_compression = 'SNAPPY')
AS SELECT *
FROM {old_table_name};
WHERE year={year} AND month={month} AND day={day} AND hour={hour}
'''


def lambda_handler(event, context):
  event_dt = datetime.datetime.strptime(event['time'], "%Y-%m-%dT%H:%M:%SZ")
  basic_dt = event_dt - datetime.timedelta(hours=1)
  year, month, day, hour = (basic_dt.year, basic_dt.month, basic_dt.day, basic_dt.hour)

  output_location = OUTPUT_LOC_FMT.format(output_prefix=OUTPUT_PREFIX,
    year=year, month=month, day=day, hour=hour)

  query = QUERY_FMT.format(new_table_name=NEW_TABLE_NAME, old_table_name=OLD_TABLE_NAME,
    year=year, month=month, day=day, hour=hour)

  print('[INFO] QueryString={}'.format(query), file=sys.stderr)
  print('[INFO] ExternalLocation={}'.format(output_location), file=sys.stderr)

  client = boto3.client('athena')
  response = client.start_query_execution(
    QueryString=query,
    QueryExecutionContext={
      'Database': DATABASE
    },
    ResultConfiguration={
      'OutputLocation': output_location
    },
    WorkGroup=WORK_GROUP
  )
  print('[INFO] QueryExecutionId={}'.format(response['QueryExecutionId']), file=sys.stderr)


if __name__ == '__main__':
  event = {
    "id": "cdc73f9d-aea9-11e3-9d5a-835b769c0d9c",
    "detail-type": "Scheduled Event",
    "source": "aws.events",
    "account": "{{{account-id}}}",
    "time": datetime.datetime.today().strftime('%Y-%m-%dT%H:05:00Z'),
    "region": "us-east-1",
    "resources": [
      "arn:aws:events:us-east-1:123456789012:rule/ExampleRule"
    ],
    "detail": {}
  }
  print('[DEBUG] event:\n', event, file=sys.stderr)
  lambda_handler(event, {})
