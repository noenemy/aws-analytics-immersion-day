# 실습 준비 작업
실습을 시작 하기 전에 필요한 IAM User, EC2를 생성하고 및 구성합니다.

### IAM User 생성
실습 하는 동안 사용할 IAM User를 생성합니다.

1. AWS Management Console에 로그인 한 뒤 IAM 서비스에 접속합니다.
2. 왼쪽 메뉴에서 Users를 선택합니다.
3. Add user 버튼을 클릭하여 사용자 추가 페이지로 들어갑니다.
4. User name에 <원하는 사용자 이름> 을 입력하고, Access type에 Programmatic access와
AWS Management Console access 둘 모두를 선택합니다. Console password에 <원하는 패스워드> 를 입력하고,
마지막 Require password reset의 체크는 해제합니다.
5. Next: Permissions 버튼을 클릭하고 Attach existing policies directly를 선택한 뒤 AdministratorAccess 권한을 추가해줍니다.
6. Next: Review 버튼을 클릭하고 정보를 확인한 뒤 Create user 버튼을 클릭하여 사용자 생성을 완료합니다.
7. Download.csv 버튼을 클릭하여 생성한 사용자의 정보를 다운 받습니다. EC2 설정에 꼭 필요한 파일이므로 기억하기 쉬운 위치에 저장합니다.

### EC2 생성
실습에 필요한 데이터를 실시간으로 발생시킬 EC2 인스턴스를 생성합니다.
1. AWS Management Console에서 EC2 서비스에 접속합니다.
2. 우측 상단에서 Region은 US West (Oregon)를 선택합니다.
3. Launch Instance를 선택하여 새로운 인스턴스 생성을 시작합니다.
4. Step 1: Choose an Amazon Machine Image (AMI) 화면에서 Amazon Linux AMI 2018.03.0 (HVM), SSD Volume Type - ami-14c5486b 를 선택합니다.
5. Step 2 : Choose an Instance Type 화면에서 인스턴스 타입은 t2.micro를 선택합니다. Next: Configure Instance Details 을 클릭합니다.
6. Step 3: Configure Instance Details 화면에서 Advanced Details을 클릭하고 아래 userdata를 복사하여 붙여 넣습니다.
    ```shell script
    #include
    https://s3.amazonaws.com/analytics-immersion-day-v20200228/userdata.sh
    ```
7. Step 4: Add Storage 화면에서 기본값을 그대로 두고 Next: Add Tags를 클릭합니다.
8. Step 5: Add Tags 화면에서 Next: Configure Security Group 을 클릭합니다.
9. Step 6: Configure Security Group 화면에서 Security Group에 필요한 정보를 입력한 후 Review and Launch를 클릭합니다.
    + Security Group Name : bastion
    + Description : SG for bastion
 
    Security group rules의 **Inbound** 에 아래 내용을 입력합니다.
    + Type : SSH
    + Protocol : TCP
    + Port Range : 22
    + Source : 0.0.0.0/0
10. Step 7: Review Instance Launch 화면에서 Launch를 클릭합니다.
11. EC2 Instance에 접속하기 위한 Key pair를 생성합니다. 
Create a new key pair를 선택하고 Key pair name은 `analytics-hol` 을 입력한 후 Download Key Pair를 클릭합니다.
Key Pair를 PC의 임의 위치에 저장한 후 Launch Instances를 클릭합니다. (인스턴스 기동에 몇 분이 소요될 수 있습니다.)
12. (MacOS 사용자) 다운로드 받은 Key Pair 파일의 File Permission을 400으로 변경합니다.
    ```shell script
    $ chmod 400 ./analytics-hol.pem 
    $ ls -lat analytics-hol.pem 
    -r--------  1 ******  ******  1692 Jun 25 11:49 analytics-hol.pem
    ```

### EC2 설정
생성한 EC2 인스턴스가 다른 AWS 리소스에 접근 및 제어할 수 있도록 다음과 같이 구성합니다.
1. 생성한 인스턴스의 Public IP로 SSH 접속을 합니다.
    ```shell script
    ssh -i “<Key pair name>" ec2-user@<Public IP>
    ```
2. User Data를 통해 필요한 파일들이 잘 다운로드 받아졌는지 확인합니다.
3. AWS의 다른 리소스 접근을 위해 AWS Configure를 진행합니다. 이때 앞서 생성한 IAM User 데이터를 활용합니다.
이전에 다운로드 받은 .csv 파일을 열어 Access key ID와 Secret access key를 확인하고 입력합니다.
    ```shell script
    $ aws configure
    AWS Access Key ID [None]: <Access key ID>
    AWS Secret Access Key [None]: <Secret access key>
    Default region name [None]: us-west-2
    Default output format [None]: 
    ```
4. 설정이 완료 되었다면 다음과 같이 입력하신 정보가 마스킹 되어 보이게 됩니다.
    ```shell script
    $ aws configure
    AWS Access Key ID [****************EETA]:
    AWS Secret Access Key [****************CixY]:
    Default region name [None]: us-west-2
    Default output format [None]: 
    ```

### Elasicsearch Service에서 사용할 Security Groups 생성
실습에서 사용할 EC2와 Elasticsearch Service을 위한 security group을 생성하고 구성합니다.
1. AWS Management Console에서 EC2 서비스에 접속합니다.
2. **NETWORK & SECURITY** 메뉴에서 **Security Groups** 항목을 선택합니다.
3. **\[Create Security Group\]** 을 클릭합니다.
4. Create Security Group 화면에서 Security Group에 필요한 정보를 입력한 후, 새로운 security group을  **\[Create\]** 합니다.
    + Security Group Name : use-es-cluster-sg
    + Description : security group for an es client

    Security group rules의 **Inbound** 은 아무것도 입력하지 않습니다.
5. 다시 **\[Create Security Group\]** 클릭해서 Create Security Group 화면으로 이동합니다.
Security Group에 필요한 정보를 입력한 후, 새로운 security group을 **\[Create\]** 합니다.
    + Security Group Name : es-cluster-sg
    + Description : security group for an es cluster
 
    Security group rules의 **Inbound** 에 아래 내용을 입력합니다.
    + Type : All TCP
    + Protocol : TCP
    + Port Range : 0-65535
    + Source : `use-es-cluster-sg` 의 security group id
