from kafka import KafkaConsumer 
from kafka import KafkaProducer 
import threading
import json
import random
import boto3
from botocore.config import Config
from json import dumps
#from aws_xray_sdk.core import xray_recorder
#from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

#app = Flask(__name__)
#api = Api(app)
#xray_recorder.configure(service='creditmanager')
#XRayMiddleware(app, xray_recorder)


my_config = Config(
    region_name='us-west-2',
)
#t = get_secret()
#print(DATABASE_CONFIG)
cloudformation_client = boto3.client('cloudformation', config=my_config)
response = cloudformation_client.describe_stacks(
    StackName='MicroserviceCDKVPC'
)
ParameterKey=''
outputs = response["Stacks"][0]["Outputs"]
for output in outputs:
    keyName = output["OutputKey"]
    if keyName == "mskbootstriapbrokers":
        ParameterKey = output["OutputValue"]

print( ParameterKey )
ssm_client = boto3.client('ssm', config=my_config)
response = ssm_client.get_parameter(
    Name=ParameterKey
)
BOOTSTRAP_SERVERS = response['Parameter']['Value'].split(',')

class CreditManager():
    producer = KafkaProducer(acks=0, compression_type='gzip',bootstrap_servers=BOOTSTRAP_SERVERS, security_protocol="SSL", value_serializer=lambda v: json.dumps(v, sort_keys=True).encode('utf-8'))    
    ret_fin = 0
    ret_message = ''

    def register_kafka_listener(self, topic):
        # Poll kafka
        def poll():
            # Initialize consumer Instance
            consumer = KafkaConsumer(topic,security_protocol="SSL", bootstrap_servers=BOOTSTRAP_SERVERS, auto_offset_reset='earliest', enable_auto_commit=True, 
                                        group_id='my-mc' )

            print("About to start polling for topic:", topic)
            consumer.poll(timeout_ms=6000)
            print("Started Polling for topic:", topic)
            for msg in consumer:
                self.kafka_listener(msg)
        print("About to register listener to topic:", topic)
        t1 = threading.Thread(target=poll)
        t1.start()
        print("started a background thread")

    def on_send_success(self, record_metadata):
        print("topic: %s" % record_metadata.topic)
        self.ret_fin = 200
        self.ret_message = "successkafkaproduct"

    def on_send_error(self, excp):
        print("error : %s" % excp)
        self.producer.flush() 
        self.ret_fin = 400
        self.ret_message = "failkafkaproduct"

    def sendkafka(self, topic,data, status):
        data['status'] = status
        self.producer.send( topic, value=data).add_callback(self.on_send_success).add_errback(self.on_send_error) 
        self.producer.flush() 


    def kafka_listener(self, data):
        #check product name
        json_data = json.loads(data.value.decode("utf-8"))
        success_credit = random.randrange(0,99)
        if success_credit > 5:
            self.sendkafka("orderkafka", json_data, "success-kafka-credit")           
        else :
            self.sendkafka("orderkafka", json_data, "fail-kafka-credit")           

        print( {'message': json_data }, self.ret_fin )
         

         
if __name__ == '__main__':
#    OrderManager.register_kafka_listener('orderkafka')
#   app.run(host="0.0.0.0", port=5052,debug=True)
    productmanager1 = CreditManager()
    productmanager1.register_kafka_listener('creditkafka')
