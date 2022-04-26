# Loginator
 This is a rudimentary tool that will help you extract logs or other files stored in S3

 ## Installation

 ```
 pip install loginator
 ```

 ## Use
 Make sure you are logged in in an AWS account in your environment

 See instructions with:

 ```
 loginator --help
 ```

 ## Examples

 ```
 loginator example_bucket_name --prefix /2022/01/01 --out example_bucket_logs.gz
 ```
