
## OS requirements

This has to be installed manually and available in the system before running ./install.sh

* Python 3
* Python virtualenv

## Install

This script creates Python virtualenv and installs all requirements inside for later use ./deploy.py

```./install.sh```

## Deploy

```-t tmp directory
-b prefix for s3 buckets, final name will be [prefix]-region_name

./deploy.py -t /tmp/drift_detector -b pattern-match-drift-detector-dev 
```

Note: This script uses Ansible, with async tasks. Waiting for async tasks to 
be done generates scary outputs like this:

```FAILED - RETRYING: task name...```

It only means Ansible is still waiting for this particular task to complete.


## Use

```https://eu-west-1.console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks/create/review?templateURL=https://s3.eu-west-1.amazonaws.com/pattern-match-drift-detector-dev-eu-west-1/drift-detector-cf.yaml&stackName=cf-drift-detection&param_SlackWebhook=https://hooks.slack.com/services/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&param_Cron=* * * * ? *```

