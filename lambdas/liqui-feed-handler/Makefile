clean:
	rm -rf build
	rm -rf node_modules

compile:
	npm install
	@find src -name '*.coffee' | xargs ./node_modules/.bin/iced -c -o build/

upload: clean compile
	zip -r -X build/bundle.zip build/*.js node_modules/
	aws s3 cp build/bundle.zip s3://dewmrax-lambdas-2/liqui-feed-handler.zip
