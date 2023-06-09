#!/usr/bin/env python

from __future__ import print_function
import sys
import os
import time
from abc import abstractmethod

from blue_st_sdk.manager import Manager
from blue_st_sdk.manager import ManagerListener
from blue_st_sdk.node import NodeListener
from blue_st_sdk.feature import FeatureListener
from blue_st_sdk.features.audio.adpcm.feature_audio_adpcm import FeatureAudioADPCM
from blue_st_sdk.features.audio.adpcm.feature_audio_adpcm_sync import FeatureAudioADPCMSync

import paho.mqtt.publish as publish

INTRO = """##################
# SensorTile data logger #
##################"""

SCANNING_TIME_s = 1

def print_intro():
    print('\n' + INTRO + '\n')

class MyManagerListener(ManagerListener):

    def on_discovery_change(self, manager, enabled):
        print('Discovery %s.' % ('started' if enabled else 'stopped'))
        if not enabled:
            print()

    def on_node_discovered(self, manager, node):
        print('New device discovered: %s.' % (node.get_name()))


class MyNodeListener(NodeListener):

    def on_connect(self, node):
        print('Device %s connected.' % (node.get_name()))

    def on_disconnect(self, node, unexpected=False):
        print('Device %s disconnected%s.' % \
            (node.get_name(), ' unexpectedly' if unexpected else ''))
        if unexpected:
            # Exiting.
            print('\nExiting...\n')
            sys.exit(0)


def connect_ble(MAC):
    manager = Manager.instance()
    manager_listener = MyManagerListener()
    manager.add_listener(manager_listener)

    while True:
        print('Scanning Bluetooth devices...\n')
        manager.discover(SCANNING_TIME_s)

        discovered_devices = manager.get_nodes() 
        if not discovered_devices:
            print('No Bluetooth devices found. Exiting...\n')
            sys.exit(0)

        device = None
        for discovered in discovered_devices:
            if discovered.get_tag() == MAC:
                device = discovered
                break
        if not device:
            print('Device not found...\n')
            sys.exit(0)

        node_listener = MyNodeListener()
        device.add_listener(node_listener)
        print('Connecting to %s...' % (device.get_name()))
        if not device.connect():
            print('Connection failed.\n')
            sys.exit(0)
        print('Connection done.')
        return device

def listfeatures(device):
    features = device.get_features() 
    
    print('\nFeatures:')
    i = 0
    for feature in features: 
        print('%d) %s' % (i, feature.get_name()))
        i+=1
    return features

def readsensorTemperature(device, sensor):
    device.enable_notifications(sensor)
    dado='0'
    if device.wait_for_notifications(3):
        dado = str(sensor)
    device.disable_notifications(sensor)
    return dado

def readsensorHumidity(device, sensor):
    device.enable_notifications(sensor)
    dado='0'
    if device.wait_for_notifications(3):
        dado = str(sensor)
    device.disable_notifications(sensor)
    return dado

def readsensorPressure(device, sensor):
    device.enable_notifications(sensor)
    dado='0'
    if device.wait_for_notifications(3):
        dado = str(sensor)
    device.disable_notifications(sensor)
    return dado
    
def logdata(data, logger, logsize, path, starttime, mqtt):
    cache = str(data)
    if len(logger) < logsize :
        logger.append(cache)
        #publish.single(mqtt, data, hostname="172.16.2.103", port=1883)
        publish.single(mqtt, data, hostname="192.168.1.59", port=1883)
    else:
        i=0
        while i < logsize-1:
            logger[i] = logger[i+1]
            i=i+1
        logger[logsize-1] = cache
        #publish.single(mqtt, logger[i], hostname="172.16.2.103", port=1883)
        publish.single(mqtt, logger[i], hostname="192.168.1.59", port=1883)
    log = open(path, "w")
    
    for line in logger:
        log.write(line)
        log.write('\n')
    log.close()
    return logger
            
    
    
def main(argv):
    try:
        SENSORTILE_MAC = 'c0:50:21:32:02:56'
        device = connect_ble(SENSORTILE_MAC)
        
        features = listfeatures(device)
        temperature = features[0]
        humidity = features[2]
        pressure = features[3]
        
        logger = []
        logsize = 1000000000000
        starttime = time.time()
        path = "/home/pi/Desktop/data2.csv"
        
        while True:
            dataTemperature = readsensorTemperature(device, temperature)
            dataHumidity = readsensorHumidity(device, humidity)
            dataPressure = readsensorPressure(device, pressure)
            print(dataTemperature + " " + dataHumidity + " " + dataPressure)
            loggerTemperature = logdata(dataTemperature,logger,logsize,path,starttime, "sensor/temperature")
            loggerHumidity = logdata(dataHumidity,logger,logsize,path,starttime, "sensor/humidity")
            loggerPressure = logdata(dataPressure,logger,logsize,path,starttime, "sensor/pressure")

            time.sleep(120)
    except KeyboardInterrupt:
        try:
            print('\nExiting...\n')
            sys.exit(0)
        except SystemExit:
            os._exit(0)


if __name__ == "__main__":

    main(sys.argv[1:])
