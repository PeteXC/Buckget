import boto3
import os
import shutil
import time
import glob
import gzip
import click
import json
import lzma
import zipfile
from datetime import datetime
from yaspin import yaspin
from yaspin.spinners import Spinners

counter = 1

# Recursive download for S3 buckets from
# https://stackoverflow.com/questions/31918960/boto3-to-download-all-files-from-a-s3-bucket
def download_dir(client, resource, dist, sp, total_num, bucket, local="logs"):
    global counter
    local = local + "/" + bucket
    paginator = client.get_paginator("list_objects")
    for result in paginator.paginate(Bucket=bucket, Delimiter="/", Prefix=dist):
        if result.get("CommonPrefixes") is not None:
            for subdir in result.get("CommonPrefixes"):
                download_dir(
                    client, resource, subdir.get("Prefix"), sp, total_num, bucket, local
                )
        for file in result.get("Contents", []):
            dest_pathname = os.path.join(local, file.get("Key"))
            if os.path.exists(dest_pathname):
                sp.write(f"> Already have file at {dest_pathname}")
                counter += 1
                continue
            if not os.path.exists(os.path.dirname(dest_pathname)):
                os.makedirs(os.path.dirname(dest_pathname))
            if not file.get("Key").endswith("/"):
                # if not folder
                resource.meta.client.download_file(
                    bucket, file.get("Key"), dest_pathname
                )
                sp.write(f"> Downloaded file {counter} of {total_num}")
                counter += 1


def concat_files(outfilename, bucket, prefix):
    with open(outfilename, "wb") as outfile:
        for filename in glob.glob(
            pathname="logs/" + bucket + "/" + prefix + "/**", recursive=True
        ):
            if filename == outfilename:
                # don't want to copy the output into the output
                continue
            if os.path.isdir(filename):
                # ignore directories
                continue
            if filename.endswith(".gz"):
                # check if we need to unzip
                with gzip.open(filename, "rb") as readfile:
                    if readfile.readable():
                        shutil.copyfileobj(readfile, outfile)
                        continue
            with open(filename, "rb") as readfile:
                if readfile.readable():
                    shutil.copyfileobj(readfile, outfile)


# TODO: Grep using parameter
# def grep_for():
# with open("yourfile.txt", "r") as file_input:
#     with open("newfile.txt", "w") as output:
#         for line in file_input:
#             if line.strip("\n") != "nickname_to_delete":
#                 output.write(line)


def time_range(filename, new_file_name, from_time, to_time):
    with open(filename, "r") as f:
        with open(new_file_name, "w") as output:
            for line in f.readlines():
                time = (json.loads(line))["timestamp"]
                if from_time <= time <= to_time:
                    output.write(line)


def compress(in_file_name, alg):
    if alg == "gz":
        with open(in_file_name, "rb") as f_in:
            with gzip.open(f"{in_file_name}.{alg}", "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
    if alg == "xz":
        with open(in_file_name, "rb") as f_in:
            with lzma.open(f"{in_file_name}.{alg}", "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
    # FIXME: To fix this still doesn't work for zip
    # if alg == "zip":
    #     with open(in_file_name, "rb") as f_in:
    #         with zipfile.ZipFile(f"{in_file_name}.{alg}", "x") as f_out:
    #             shutil.copyfileobj(f_in, f_out)


@click.command()
@click.argument("bucket")
@click.option(
    "--prefix",
    default="",
    help="Prefix you want to start downloading from, e.g. 2022/04/07",
)
@click.option(
    "--out",
    default="",
    help="""
    Output unified filename with support for compression e.g. myLogFile.zip
    Compression allowed - zip, gz, xz
    """,
)
@click.option("--grep", default=None, help="Grep for specific parts of log")
def run(bucket, prefix, grep, out):
    client = boto3.client("s3")
    resource = boto3.resource("s3")

    bucketS3 = resource.Bucket(bucket)
    object_count = sum(1 for _ in bucketS3.objects.all())

    with yaspin(Spinners.dots, text="Downloading logs") as spinner:
        download_dir(
            client, resource, prefix, spinner, object_count, bucket, local="logs"
        )
        spinner.ok("✅")

    if out == "":
        outfilename = "all_" + str((int(time.time())))
    else:
        outfilename = out.split(".", 1)[0]

    with yaspin(Spinners.dots, text="Creating unified log") as spinner:
        concat_files(outfilename, bucket, prefix)
        spinner.ok("✅")

    with yaspin(Spinners.dots, text="Compressing") as spinner:
        if out != "":
            outfilename = out.split(".", 1)[0]
            alg = out.split(".", 1)[1]
            if alg in {"gz", "xz", "zip"}:
                compress(outfilename, alg)
                spinner.ok("✅")
            else:
                spinner.fail(
                    "Please provide a --out parameter that ends with: .gz | .xz | .zip"
                )
        else:
            compress(outfilename, "gz")
            spinner.ok("✅")

    # with yaspin(Spinners.dots, text="Creating condensed log") as spinner:
    #     time_range(outfilename, "condensed_logs", from_time, to_time)(
    #         outfilename, prefix
    #     )
    #     spinner.ok(f"✅ Logs are at {outfilename}!!!")

    yaspin().write(f"😄 Logs are at {outfilename}!!!")


# Example usage:
if __name__ == "__main__":
    run()
