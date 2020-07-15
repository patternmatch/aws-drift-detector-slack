# CloudFormation drift detector to Slack

## How it works

 1. CloudWatch triggers Lambda function.
 2. Lambda scans deployed stacks and reports drifted resources through Slack webhook.

![diagram](https://github.com/patternmatch/aws-drift-detector-slack/blob/master/assets/drift-detector.png?raw=true)

## Parameters

 * SlackWebhook - Webhook URL for pushing messages to Slack.
 * Cron - How often drift detection should be run (eg. every twelve hours `0 0 */12 * ? *` more info [here](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html)).
 * ShowInSyncResources - Skip reporting of resources with no drift (reduces Slack message output).
 * StackRegex - Defines which stacks should be scanned for resource drift.

More details can be found at https://driftdetector.com
