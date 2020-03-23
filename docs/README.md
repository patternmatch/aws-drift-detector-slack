# CloudFormation drift detector to Slack

## How it works

Lambda is triggered by CloudWatch rule. Lambda scans all stacks deployed and run drift detection.

Report about drift is sent to Slack.

Integration with Slack is handled by Slack webhook.

![diagram](https://github.com/patternmatch/aws-drift-detector-slack/blob/master/drift-detector.png?raw=true)

## Parameters

* cron - how often drift detection should be run (eg. every twelve hours `0 0 */12 * ? *` more info [here](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html))
* slack webhook - Slack webhook URL to push messages to your Slack

More details can be found at https://driftdetector.com