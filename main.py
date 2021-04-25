from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient  # AWS IOT 라이브러리

import logging
import time
import json
import argparse                 # 변수 전달용, aws IOT키 
import RPi.GPIO as GPIO         # 라즈베리파이 핀 ( 현재사용 x)
import serial                   # 아두이노 통신용 

ser = serial.Serial("/dev/serial0", 9600, timeout=1)    # 아두이노랑 통신

# Shadow JSON schema:
#
# {
#   "state": {
#       "desired":{
#           "moisture":<INT VALUE>,
#           "temp":<INT VALUE>            
#       }
#   }
# }

GPIO.setmode(GPIO.BCM)
GPIO.setup([4, 23, 24], GPIO.IN)

def customShadowCallback_Update(payload, responseStatus, token):    # 데이터 업데이트 및 불러오기

    # Display status and data from update request
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")

    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Update request with token: " + token + " accepted!")
        print("gas: " + str(payloadDict["state"]["reported"]["gas"]))
        print("MQ: " + str(payloadDict["state"]["reported"]["MQ"]))
        print("CO2: " + str(payloadDict["state"]["reported"]["CO2"]))
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")

    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")


# Function called when a shadow is deleted
def customShadowCallback_Delete(payload, responseStatus, token):
#섀도우 삭제용
     # Display status and data from delete request
    if responseStatus == "timeout":
        print("Delete request " + token + " time out!")

    if responseStatus == "accepted":
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Delete request with token: " + token + " accepted!")
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")

    if responseStatus == "rejected":
        print("Delete request " + token + " rejected!")


# Read in command-line parameters
def parseArgs():
# 프로그램 실행시 인자 전달
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
    parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
    parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
    parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
    parser.add_argument("-p", "--port", action="store", dest="port", type=int, help="Port number override")
    parser.add_argument("-n", "--thingName", action="store", dest="thingName", default="Bot", help="Targeted thing name")
    parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="basicShadowUpdater", help="Targeted client id")

    args = parser.parse_args()
    return args


# Configure logging
# AWSIoTMQTTShadowClient writes data to the log
def configureLogging():

    logger = logging.getLogger("AWSIoTPythonSDK.core")
    logger.setLevel(logging.DEBUG)
    streamHandler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)


# Parse command line arguments
args = parseArgs()

if not args.certificatePath or not args.privateKeyPath:
    parser.error("Missing credentials for authentication.")
    exit(2)

# If no --port argument is passed, default to 8883
if not args.port: 
    args.port = 8883


# Init AWSIoTMQTTShadowClient
myAWSIoTMQTTShadowClient = None
myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(args.clientId)
myAWSIoTMQTTShadowClient.configureEndpoint(args.host, args.port)
myAWSIoTMQTTShadowClient.configureCredentials(args.rootCAPath, args.privateKeyPath, args.certificatePath)

# AWSIoTMQTTShadowClient connection configuration
myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10) # 10 sec
myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5) # 5 sec


# Connect to AWS IoT
myAWSIoTMQTTShadowClient.connect()

# Create a device shadow handler, use this to update and delete shadow document
deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(args.thingName, True)

# Delete current shadow JSON doc
deviceShadowHandler.shadowDelete(customShadowCallback_Delete, 5)

# Read data from moisture sensor and update shadow
while True:
    
    #gas = GPIO.input(4)
    #MQ = GPIO.input(23)
    #CO2 = GPIO.input(24)

    data = ser.readlines()      # 시리얼로 아두이노에서 데이터 전달받는 코드

    # Display moisture and temp readings
    print("gas: {}".format(gas))
    print("MQ: {}".format(MQ))
    print("CO2: {}".format(CO2))

    # Create message payload
    payload = {"state":{"reported":{"gas":str(gas),"MQ":str(MQ),"CO2":str(CO2)}}}       # 전달할 데이터 JSON으로 변환
    
    deviceShadowHandler.shadowUpdate(json.dumps(payload), customShadowCallback_Update, 5)       # 업데이트 핸들러추가
    time.sleep(1)       # 1초마다WHILE 문 반복
