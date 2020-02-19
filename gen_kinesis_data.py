#!/usr/bin/env python3
#vim: ts=4

import sys
import csv
import json
import argparse
from collections import OrderedDict
import base64

import boto3

SCHEMA_CONV_TOOL = {
    "Invoice": int,
    "StockCode": str,
    "Description": str,
    "Quantity": int,
    "InvoiceDate": str,
    "Price": float,
    "Customer_ID": str,
    "Country": str
}

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-I', '--input-file', help='input file path ex) ./resources/online_retail_II.csv')
    parser.add_argument('--out-format', default='csv', choices=['csv', 'json'])
    parser.add_argument('--delivery-stream-name', help='The name of the delivery stream for kinesis firehose')

    options = parser.parse_args()
    with open(options.input_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        client = boto3.client('firehose')
        for row in reader:
            if options.out_format == 'csv':
               data = ','.join([e for e in row.values()])
            else:
              data = json.dumps(OrderedDict([(k, SCHEMA_CONV_TOOL[k](v)) for k, v in row.items()]))
            #TODO: insert into kinesis or kinesis firehose
            response = client.put_record(
                DeliveryStreamName=options.delivery_stream_name,
                Record={
                  'Data': '{}\n'.format(data)
                }
            )

if __name__ == '__main__':
    main()
