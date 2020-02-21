### 전체 과정
 - Kinesis Firehose 및 s3 버킷 생성
 - KFH를 이용해서 데이터 넣기
 - Athena 데이터베이스 및 테이블 생성
 - (optional) Glue를 이용한 스키마 변경
 - (optional) Athena를 이용한 작은 파일들 머지하는 작업
 - QuickSight에서 Athena 데이터 읽어서 보여주기 (?)
 - ElasticSearch 클러스터 생성하기
 - Lambda function을 이용해서 Elasticsearch에 넣기
 - Kibana에서 쿼리해보기
 - Kibana에서 dashboard 만들어 보기
 
### 준비 작업
 - 데이터를 넣어줄 ec2 장비를 생성함
 - 랩가이드가 있는 github에서 클론을 해서 설치함

### Kinesis Firehose 생성
Kinesis Firehose를 이용해서 실시간으로 데이터를 S3, Redshift, ElasticSearch 등의 목적지에 수집할 수 있습니다.
AWS Management Console에서 Kinesis 서비스를 선택합니다.

1. Get Started 버튼을 클릭합니다.
2. Deliver streaming data with Kinesis Firehose delivery streams 메뉴의 Create delivery stream 을 클릭하여
새로운 Firehose 전송 스트림 생성을 시작합니다.
3. Delivery stream name에 Source 를 입력합니다.
4. **Choose a source** 에서 `Direct PUT or other sources` 를 선택한 뒤, **Next**를 클릭합니다.
5. **Transform source records with AWS Lambda / Convert record format** 은 default인 `Disabled`로 두고 **Next**를 클릭합니다.
6. Destination은 Amazon S3를 선택하고, `Create new` 를 클릭해서 S3 bucket을 생성합니다. 
    S3 prefix를 입력합니다. (참고: https://docs.aws.amazon.com/firehose/latest/dev/s3-prefixes.html)
    예를 들어서 다음과 같이 입력 합니다.
    ```buildoutcfg
    00-retail-trans/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/
    ```
    S3 error prefix를 입력합니다.
    예를 들어서 다음과 같이 입력 합니다.
    ```buildoutcfg
    00-error/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/!{firehose:error-output-type}
    ```
    S3 prefix와 3 error prefix 입력을 완료한 후에, Next를 클릭합니다.
7. (Step 4: Configure settings) S3 buffer conditions에서 Buffer size는 1MB, Buffer interval은 60 seconds로 설정합니다.
8. 아래 IAM role에서 Create new, or Choose 버튼을 클릭합니다.
9. 새로 열린 탭에서 필요한 정책이 포함된 IAM 역할 firehose_delivery_role을 자동으로 생성합니다. Allow 버튼을 클릭하여 진행합니다.
10. 새롭게 생성된 역할이 추가된 것을 확인한 뒤 Next 버튼을 클릭합니다.
11. (Step 5: Review) Review에서 입력한 정보를 확인한 뒤 틀린 부분이 없다면 Create delivery stream 버튼을 클릭하여 Firehose 생성을 완료합니다.

### 데이터를 Kinesis Firehose를 이용해서 수집하기
생성한 Firehose가 정상적으로 데이터를 수집하는지 확인해봅니다.
1. 앞서 생성한 EC2 인스턴스에 SSH 접속을 합니다.
2. gen_kinesis_data.py을 실행합니다.
```shell script
$ python3 gen_kinesis_data.py --help
usage: gen_kinesis_data.py [-h] [-I INPUT_FILE] [--out-format {csv,tsv,json}]
                           [--service-name {kinesis,firehose}]
                           [--stream-name STREAM_NAME] [--max-count MAX_COUNT]
                           [--dry-run]

optional arguments:
  -h, --help            show this help message and exit
  -I INPUT_FILE, --input-file INPUT_FILE
                        The input file path ex)
                        ./resources/online_retail_II.csv
  --out-format {csv,tsv,json}
  --service-name {kinesis,firehose}
  --stream-name STREAM_NAME
                        The name of the stream to put the data record into.
  --max-count MAX_COUNT
                        The max number of records to put.
  --dry-run

$ python3 gen_kinesis_data.py -I resources/online_retail_II.csv \
--service-name firehose \
--out-format json \
--stream-name uk-online-retail-trans
```
3. 매 초 데이터가 발생하는 것을 확인합니다. 충분한 데이터 수집을 위해 실행 중인 상태로 다음 단계를 진행합니다.
4. 몇 분 뒤 생성한 S3 bucket에 가보면 생성된 원본 데이터가 Firehose를 통해 S3에 저장되는 것을 확인할 수 있습니다. 

### Athena 테이블 생성



