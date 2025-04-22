# README

## Overview

This is a Sceptre hook that you can use to empty an S3 bucket.
This hook is especially useful when you need to delete a CloudFormation
stack that creates S3 Bucket(s) as the S3 bucket needs to be empty
before you can delete it.

You must supply the S3 bucket name to the `bucket_name` parameter.

## Installation

Installation instructions

To install from the git repo
```shell
pip install git+https://github.com/harisfauzi/sceptre-hook-empty-s3-bucket.git
```

## Usage/Examples

Use the hook with a [hook point](https://docs.sceptre-project.org/latest/docs/hooks.html#hook-points)
Best is to use with `before_delete` hook:

```yaml
hooks:
  hook_point:
    - !sceptre_empty_s3_bucket
      bucket_name: <bucket name>
```

## Example

```yaml
hooks:
  before_delete:
    - !sceptre_empty_s3_bucket
      bucket_name: sample-bucket-111111111111
```

or if your stack lets CloudFormation to generate the bucket name for you
and you put the bucket name as part of the stack output, e.g. with the
stack name `myproject-s3stack` and the stack output for the bucket name
is `mybucketname`:

```yaml
hooks:
  before_delete:
    - !sceptre_empty_s3_bucket
      bucket_name: !stack_output_external myproject-s3stack::mybucketname
```
