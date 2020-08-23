#!/usr/bin/env python3
from prometheus_client import start_http_server, Counter
from kafka import KafkaConsumer
from json import loads
from json import dumps
from dotenv import load_dotenv
from datetime import datetime
import requests
import pytz
import os


load_dotenv()
kafka_bootstrap_servers  = os.environ['KAFKA_BOOTSTRAP_SERVERS']
kafka_topic              = os.environ['KAFKA_TOPIC']
kafka_consumer_group_id  = os.environ.get('KAFKA_CONSUMER_GROUP_ID','kafka2vm')
vm_url                   = os.environ['VM_URL']
ssl_verify_str           = {'False', 'false', 'FALSE', 'no', 'No', 'NO'}
ssl_verify               = not os.environ.get('VM_SSL_VERIFY','True') in ssl_verify_str
vm_import_path           = os.environ.get('VM_IMPORT_PATH','/api/v1/import')
vm_instance              = os.environ['VM_INSTANCE']
vm_job                   = os.environ['VM_JOB']
vm_metrics_names_str     = os.environ.get('VM_METRICS_NAMES','bytes,packets')
avoid_lables_str         = os.environ.get('VM_AVOID_LABELS','bytes,packets,stamp_updated')
vm_max_samples_per_send  = int(os.environ.get('VM_MAX_SAMPLES_PER_SEND','1000'))
vm_max_time_to_send      = int(os.environ.get('VM_MAX_TIME_TO_SEND','10'))
prometheus_client_port   = int(os.environ.get('PROMETHEUS_CLIENT_PORT','9003'))


vm_metrics_set           = set(vm_metrics_names_str.split(','))
avoid_labels             = set(avoid_lables_str.split(',')) 
timestmap_template       = '%Y-%m-%d %H:%M:%S'

def nowstamp():
    return str(datetime.now())

def main():
    print(f'{nowstamp()} Connecting to Kafka broker. Bootstrap servers {kafka_bootstrap_servers}')
    consumer = KafkaConsumer(
        kafka_topic, 
        bootstrap_servers=kafka_bootstrap_servers.split(','),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=kafka_consumer_group_id,
        value_deserializer=lambda x: loads(x.decode('utf-8'))
        )
    print(f'{nowstamp()} Connected')
    samples_counter = Counter('samples_count_total', 'Total number of samples ')
    print(f'{nowstamp()} Starting Prometheus client http server')
    start_http_server(prometheus_client_port)
    vm_records = []
    samples_timer = int(datetime.now().timestamp())
    samples_max_count = 0
    for message in consumer:
        metric_timestamp = int(datetime.strptime(message.value['stamp_updated'],timestmap_template).replace(tzinfo=pytz.utc).timestamp()) * 1000
        for vm_metric_name in vm_metrics_set:
            metric_value = message.value[vm_metric_name]
            vm_records.append(
                dumps(
                        {'metric': {
                                    **{'__name__': vm_metric_name,
                                    'job': vm_job,
                                    'instance': vm_instance,
                                    },
                                    **{k:str(message.value[k]) for k in message.value if k not in avoid_labels}
                                    },
                        'values'    : [metric_value],
                        'timestamps': [metric_timestamp]
                        }
                    )
                )
        samples_counter.inc()
        samples_max_count += 1
        if (samples_max_count > vm_max_samples_per_send) or ((int(datetime.now().timestamp()) - samples_timer) > vm_max_time_to_send):
          r = requests.post(f'{vm_url}/{vm_import_path}', data=bytes('\n'.join(vm_records), encoding = 'utf-8'))
          print(f'{nowstamp()} {r}')
          print(f'{nowstamp()} Sent {samples_max_count} samples')
          samples_timer = int(datetime.now().timestamp())
          samples_max_count = 0
          vm_records = []
    return

if __name__ == "__main__":
    main()