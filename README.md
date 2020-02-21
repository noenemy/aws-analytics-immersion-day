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
Amazon Athena를 이용해서 S3에 저장된 데이터를 기반으로 테이블을 만들고, 테이블을 쿼리한 다음 쿼리 결과를 확인할 수 있습니다.
먼저 데이터를 쿼리하기 위해서 데이터베이스를 생성합니다.

##### 1단계 데이터베이스 생성
1. Athena 콘솔을 엽니다.
2. Athena 콘솔을 처음 방문하면 시작하기 페이지로 이동합니다. **\[Get Started\]** 를 선택해 쿼리 편집기를 엽니다. 
처음 방문하는 경우가 아니라면 Athena 쿼리 편집기가 열립니다.
3. Athena 쿼리 편집기에서 예제 쿼리가 있는 쿼리 창을 볼 수 있습니다. 쿼리 창의 아무 곳에나 쿼리를 입력하기 시작합니다.
4. **mydatabase** 라는 데이터베이스를 생성하려면 다음 CREATE DATABASE 문을 입력한 다음, **\[Run Query\]** 를 선택합니다.
    ```buildoutcfg
    CREATE DATABASE mydatabase
    ```
5. 카탈로그 디스플레이가 새로 고쳐지고 왼쪽 [Catalog] 대시보드의 [DATABASE] 목록에 mydatabase가 표시되는지 확인합니다.

##### 2단계: 테이블 생성
1. **\[DATABASE\]** 에 `mydatabase`가 선택되었는지 확인한 후 **\[New Query\]** 를 선택합니다.
2. 쿼리 창에 다음 CREATE TABLE 문을 입력한 후 \**[Run Query\]** 를 선택합니다.
    ```buildoutcfg
    CREATE EXTERNAL TABLE `mydatabase.retail_trans`(
      `invoice` string COMMENT 'Invoice number', 
      `stockcode` string COMMENT 'Product (item) code', 
      `description` string COMMENT 'Product (item) name', 
      `quantity` int COMMENT 'The quantities of each product (item) per transaction', 
      `invoicedate` string COMMENT 'Invoice date and time', 
      `price` float COMMENT 'Unit price', 
      `customer_id` string COMMENT 'Customer number', 
      `country` string COMMENT 'Country name')
    PARTITIONED BY ( 
      `year` int, 
      `month` int, 
      `day` int, 
      `hour` int)
    ROW FORMAT SERDE 
      'org.openx.data.jsonserde.JsonSerDe' 
    STORED AS INPUTFORMAT 
      'org.apache.hadoop.mapred.TextInputFormat' 
    OUTPUTFORMAT 
      'org.apache.hadoop.hive.ql.io.IgnoreKeyTextOutputFormat'
    LOCATION
      's3://aws-analytics-immersion-day-2020-apne2/00-retail-trans'
    ```
    테이블 retail_trans가 생성되고 데이터베이스의 **\[Catalog\]** 대시보드에 표시됩니다.
3. 테이블을 생성한 이후 **\[New Query(새 쿼리)\]** 를 선택하고 다음을 실행해서, 파티션의 데이터를 로드합니다.
    ```buildoutcfg
    MSCK REPAIR TABLE mydatabase.retail_trans
    ```

##### 3단계: 데이터 쿼리
1. **\[New Query\]** 를 선택하고 쿼리 창의 아무 곳에나 다음 문을 입력한 다음 **\[Run Query\]** 를 선택합니다.
    ```buildoutcfg
    SELECT *
    FROM retail_trans
    LIMIT 10
    ```
다음과 같은 형식의 결과가 반환됩니다.

### Amazon QuickSight
이번에는 Amazon Quicksight를 통해 데이터를 시각화 해 보도록 하겠습니다. Quicksight 콘솔로 이동합니다.