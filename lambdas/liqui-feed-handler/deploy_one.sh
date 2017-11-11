#!/bin/bash -e -x

EXCHANGE=LIQUI
TOKEN=$2
CURRENCY=$3
NAME=$EXCHANGE-$TOKEN-$CURRENCY

echo "creating function" $NAME

aws lambda delete-function --function-name $NAME 2>/dev/null || echo "function non-existant"
aws lambda create-function \
  --region us-east-1 \
  --runtime nodejs6.10 \
  --role arn:aws:iam::554285174758:role/dynamodb-writer \
  --handler bin/lambda.handler \
  --code S3Bucket=dewmrax-lambdas-2,S3Key=liqui-feed-handler.zip \
  --memory-size 128 \
  --timeout 15 \
  --function-name $NAME \
  --environment "Variables={EXCHANGE=$EXCHANGE,TOKEN=$TOKEN,CURRENCY=$CURRENCY}"
