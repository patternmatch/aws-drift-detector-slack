SECRETS=`curl -s -H "x-api-key: $API_KEY_TO_GET_GITLAB_SECRETS" https://gitlabsecrets.pattern-match.com/secrets/driftdetector`
for s in $(echo $SECRETS | jq -r "to_entries|map(\"\(.key)=\(.value|tostring)\")|.[]" ); do
  export $s
done
