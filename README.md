This is a crypto arbitrage bot I wrote during the latter half of 2017 and early part of 2018

Book data is polled and retrieved using functions designed to run on AWS lambdas. Incoming book data was normalized, sanity checked, and then saved to an AWS DB.
The triggering of the AWS lambda functions is managed by a python script called feed_manager, done intelligently so that trade pairs likely to present an arb opportunity soon is polled with more frequency.

Trading decisions are managed and invoked by the python script trader.py

This code is provided as-is, with no warranty, and no assumption of use. Author of code is not responsible for any losses incurred trading with this program. Author emphasizes that this code is not up to date with various recent protocol changes such as websockets, and as such is intended for educational and case-study purposes only. Anyone attempting to trade on a similar algorithm today should strongly consider a complete rebuild as websockets change the architecture of the system dramatically.
