# pmacct-kafka-vm
**pmacct-kafka-vm** is a python script designed to read flow statistics from [Kafka], to process it and to store it into [Victoria Metrics].\
Flow statistics is expected to be produced  by [Pmacct] flow collector kafka plugin.\
Script calls import api of [Victoria Metrics] to store data.\
Prometheus client is used to expose total count of sample processed. Metrics can be scraped at "/metrics" path. Default port is "9003".

Scripts uses `stamp_updated` as a timestamp for metric in [Victoria Metrics].\
You have to set `kafka_history` and `kafka_history_roundoff` options in sfacct.conf or nfacct.conf.

Example:
```
plugins: kafka[kafka]
kafka_history[kafka]: 5m
kafka_history_roundoff[kafka]: m
```

### Runnig the script

Just run:
```
pmacct-kafka-vm.py
```
Script gets its  configuration from environment variables or from .env file(see .env.example).

### Running script in docker:

```
docker run --env-file .env --name pmacct-kafka-vm -p 9003:9003 kvitex/pmacct-kafka-vm 
```

### Variables:

Variable | Description | Example
--- | --- | ---
`KAFKA_BOOTSTRAP_SERVERS` | Kafka botstrap server in host:port format. Where can be several ones, separated by coma  |  **mykafka1:9094**
`KAFKA_TOPIC` | Kafka topic to read from.|  **pmacct.sfacct**
`KAFKA_CONSUMER_GROUP_ID` | Kafka consumer group id. Default value is   | kafka2vm
`VM_URL` | URL to [Victoria Metrics] server. | **http://your.victoria-metrics.server:8428**
`VM_SSL_VERIFY` | Verify SSL certifcate if HTTPS protocol is used in VM_URL. Could be 'YES' or 'NO'. Default value is 'YES'|  YES
`VM_IMPORT_PATH` | Path to import API  of [Victoria Metrics] server. Default value is '/api/v1/import'  | /api/v1/import
`VM_INSTANCE` | 'instance' label value to be used in metric at [Victoria Metrics]. | **pmacct.my.domain**
`VM_JOB` | 'job' label value to be used in metric at [Victoria Metrics]. | **sfacct**
`VM_METRIC_NAME` | Metric name in [Victoria Metrics]. Default value is 'bytes' | bytes
`VM_AVOID_LABELS` | List of labels separated by coma, that shoud not be exported to [Victoria Metrics]. Default values is 'bytes,stamp_updated'| bytes,stamp_updated 
`VM_MAX_SAMPLES_PER_SEND` | Maximum number of samples that script caches before store them in  [Victoria Metrics]. Defaul value is '1000'  | 1000
`VM_MAX_TIME_TO_SEND` | Maximum time in seconds, between sending samples to  [Victoria Metrics]. Default value is 10 | 10
`PROMETHEUS_CLIENT_PORT` | Prometheus client http server port. Default value is '9003' | 9003

Script is polling Kafka for new messages in topic and store them in memory. It looks for amount of samples were read and time passed from last insert to [Victoria Metrics] operation.\
If amount of samples is greater then `VM_MAX_SAMPLES_PER_SEND`  or time has passed from last insert to [Victoria Metrics] is greater then `VM_MAX_TIME_TO_SEND` or both, then cached samples are stored in [Victoria Metrics], cached samples counter is reset to 0 and timer is set to current timestamp.




[//]:#

[pmacct]: <http://www.pmacct.net/>
[victoria metrics]: <https://victoriametrics.github.io/> 
[kafka]: <https://kafka.apache.org/>
