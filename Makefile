install:
	./install.sh

deploy-prod:
	./deploy.py -t /tmp/drift_detector -b pattern-match-drift-detector

deploy-dev:
	./deploy.py -t /tmp/drift_detector -b pattern-match-drift-detector-dev