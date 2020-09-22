This is a crypto arbitrage bot I wrote during the latter half of 2017 and early part of 2018

Book data is polled and retrieved using functions designed to run on AWS lambdas. Incoming book data was normalized, sanity checked, and then saved to an AWS DB.
The triggering of the AWS lambda functions is managed by a python script called feed_manager, done intelligently so that trade pairs likely to present an arb opportunity soon is polled with more frequency.

Trading decisions are managed and invoked by the python script trader.py

This code is provided as-is, with no warranty, and no assumption of use. Author of code is not responsible for any losses incurred trading with this program. Author emphasizes that this code is not up to date with various recent protocol changes such as websockets, and as such is intended for educational and case-study purposes only. Anyone attempting to trade on a similar algorithm today should extract the logic around trading decisions but rebuild the architecture as websockets change the system dramatically.

Released under MIT license

Copyright 2020 DEWMRAX Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
