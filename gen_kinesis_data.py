#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import sys
import csv
import json
import argparse
from collections import OrderedDict
import base64
import traceback
import random
import time

import boto3

random.seed(47)

SCHEMA_CONV_TOOL = {
  "Invoice": str,
  "StockCode": str,
  "Description": str,
  "Quantity": int,
  "InvoiceDate": str,
  "Price": float,
  "Customer_ID": str,
  "Country": str
}

DELIMETER_BY_FORMAT = {
  'csv': ',',
  'tsv': '\t'
}


def gen_records(options, reader):
  record_list = []
  for row in reader:
    if options.out_format in DELIMETER_BY_FORMAT:
       delimeter = DELIMETER_BY_FORMAT[options.out_format]
       data = delimeter.join([e for e in row.values()])
    else:
      try:
        data = json.dumps(OrderedDict([(k, SCHEMA_CONV_TOOL[k](v)) for k, v in row.items()]), ensure_ascii=False)
      except Exception as ex:
        traceback.print_exc()
        continue
    if options.max_count == len(record_list):
      yield record_list
      record_list = []
    record_list.append(data)

  if record_list:
    yield record_list


def put_records_to_firehose(options, records):
  MAX_RETRY_COUNT = 3

  for data in records:
    for _ in range(MAX_RETRY_COUNT):
      try:
        response = client.put_record(
          DeliveryStreamName=options.stream_name,
          Record={
            'Data': '{}\n'.format(data)
          }
        )
        break
      except Exception as ex:
        traceback.print_exc()
        time.sleep(random.randint(1, 10))
    else:
      raise RuntimeError('[ERROR] Failed to put_records into stream: {}'.format(options.stream_name))


def put_records_to_kinesis(options, records):
  MAX_RETRY_COUNT = 3

  payload_list = []
  for data in records:
    partition_key = 'part-{:05}'.format(random.randint(1, 1024))
    payload_list.append({'Data': data, 'PartitionKey': partition_key})

  for _ in range(MAX_RETRY_COUNT):
    try:
      response = client.put_records(Records=payload_list, StreamName=options.stream_name)
      break
    except Exception as ex:
      traceback.print_exc()
      time.sleep(random.randint(1, 10))
  else:
    raise RuntimeError('[ERROR] Failed to put_records into stream: {}'.format(options.stream_name))


def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('-I', '--input-file', help='The input file path ex) ./resources/online_retail_II.csv')
  parser.add_argument('--out-format', default='csv', choices=['csv', 'tsv', 'json'])
  parser.add_argument('--service-name', default='kinesis', choices=['kinesis', 'firehose'])
  parser.add_argument('--stream-name', help='The name of the stream to put the data record into.')
  parser.add_argument('--max-count', default=10, type=int, help='The max number of records to put.')

  options = parser.parse_args()
  with open(options.input_file, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    client = boto3.client(options.service_name)
    for records in gen_records(options, reader):
      if options.service_name == 'kinesis':
        put_records_to_kinesis(options, records)
      elif options.service_name == 'firehose':
        put_records_to_firehose(options, records)
      else:
        pass
      time.sleep(random.choices([0.01, 0.03, 0.05, 0.07, 0.1])[-1])


if __name__ == '__main__':
  main()
