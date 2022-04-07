import boto3
import os
import shutil
import time
import glob
import click
from datetime import datetime
from yaspin import yaspin
from yaspin.spinners import Spinners

counter = 1

# Recursive download for S3 buckets from
# https://stackoverflow.com/questions/31918960/boto3-to-download-all-files-from-a-s3-bucket
def download_dir(client, resource, dist, sp, total_num, bucket, local='logs'):
    global counter
    paginator = client.get_paginator('list_objects')
    for result in paginator.paginate(Bucket=bucket, Delimiter='/', Prefix=dist):
        if result.get('CommonPrefixes') is not None:
            for subdir in result.get('CommonPrefixes'):
                download_dir(client, resource, subdir.get('Prefix'), sp, total_num, bucket, local)
        for file in result.get('Contents', []):
            dest_pathname = os.path.join(local, file.get('Key'))
            if not os.path.exists(os.path.dirname(dest_pathname)):
                os.makedirs(os.path.dirname(dest_pathname))
            if not file.get('Key').endswith('/'):
                resource.meta.client.download_file(bucket, file.get('Key'), dest_pathname)
                sp.write(f"> Downloaded file {counter} of {total_num}")
                counter += 1

def concat_files(outfilename, prefix):
    with open(outfilename, 'wb') as outfile:
        for filename in glob.glob(pathname='logs/' + prefix + '/**', recursive=True):
            if filename == outfilename:
                # don't want to copy the output into the output
                continue
            if os.path.isdir(filename):
                # ignore directories
                continue
            with open(filename, 'rb') as readfile:
                if readfile.readable():
                    shutil.copyfileobj(readfile, outfile)
                    print(f"Added {readfile.name} to {outfilename}")

@click.command()
@click.argument("bucket")
@click.option("--prefix", default="", help="Prefix you want to start downloading from, e.g. 2022/04/07")
@click.option("--grep", default=None, help="Grep for specific parts of log")
def run(bucket, prefix, grep):
    client = boto3.client('s3')
    resource = boto3.resource('s3')

    bucketS3 = resource.Bucket(bucket)
    object_count = sum(1 for _ in bucketS3.objects.all())

    with yaspin(Spinners.aesthetic, text="Downloading logs") as spinner:
        download_dir(client, resource, prefix, spinner, object_count, bucket, local='logs')
        spinner.ok("✅ Logs downloaded!")

    outfilename = 'all_' + str((int(time.time())))

    with yaspin(Spinners.aesthetic, text="Creating master log") as spinner:
        concat_files(outfilename, prefix)
        spinner.ok(f"✅ Logs are at {outfilename}!!!")

# Example usage:
# python3 finder.py wafstack-waflogsf9f75746-z1g8cih4ao88 --prefix=2022/04/07
if __name__ == '__main__':
    run()