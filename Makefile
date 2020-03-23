install:
	./install.sh

deploy-prod:
	./deploy.py -t /tmp/drift_detector -b pattern-match-drift-detector

deploy-dev:
	./deploy.py -t /tmp/drift_detector -b pattern-match-drift-detector-dev

publish:
	sam publish --template /tmp/drift_detector/drift-detector-cf-us-east-1.yaml --region us-east-1