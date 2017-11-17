#!/bin/bash -e -x

cat ../../markets.csv | while IFS=, read -r exchange token currency
do
  ./deploy_one.sh $exchange $token $currency
done
