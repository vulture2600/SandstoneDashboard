# Alerting

### Slack alerts

https://api.slack.com/apps > Grafana Alerts > Incoming Webhooks

Sample curl request to post to the #alerts channel. Get the full URL from the link above.

```shell
curl -X POST -H 'Content-type: application/json' --data '{"text":"Hello, World!"}' https://hooks.slack.com/services/<REMOVED>
```

In Grafana:
1) Go to Alerting → Contact points
2) Add a new contact point of type Slack
3) Paste the webhook URL: 
```https://hooks.slack.com/services/<REMOVED>```
4) Save it

After this create alerts from the panels in the Grafana dashboard.

See [Issues](issues.md) for current issues.
