#!/usr/bin/python
import dpkt
import pandas as pd
import sys
import socket
import struct
import operator
import numpy as np
import cmath
import argparse

def parse_args():
        parser = argparse.ArgumentParser(
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('pcap', type=argparse.FileType('r'), help='Pcap file')
        parser.add_argument('csv', nargs='?', type=argparse.FileType('w'),
                            help='Output CSV file')
        parser.add_argument('--version', action='version', version='%(prog)s 1.1')
        args = parser.parse_args()
        if args.csv is None:
                args.csv = open(sys.argv[1].replace(".pcap", ".csv"), "w")
        return args

def grab_csi_data(packet):
        eth = dpkt.ethernet.Ethernet(packet)
        ip = eth.data
        udp = ip.data
        return udp.data

def grab_udp_condition(packet):
	capture = False
	eth = dpkt.ethernet.Ethernet(packet)
	ip = eth.data
	if type(ip) == dpkt.ip.IP:
		udp = ip.data
		if type(udp) == dpkt.udp.UDP:
			capture = True
	return capture

def grab_udp(packets):
	return [(time, grab_csi_data(packet))
                for (time, packet) in packets if grab_udp_condition(packet)]

def order_packets(packets):
	packets.sort(key=operator.itemgetter(0))

def parse_binary(csi):
	channel = np.empty([255], dtype='complex')
	csi = csi[14:]
	for index in range(0, len(csi), 4):
		real = struct.unpack('>h', csi[index:index + 2])[0]
		imag = struct.unpack('>h', csi[index + 2:index + 4])[0]
		val = complex(real, imag)
		channel[index/4] = abs(val)
	return channel
		

def print_csv(packets, csv_file):
	df = pd.DataFrame()
	csi = pd.DataFrame()
	df = df.append([time for time, packet in packets])
	packets = [packet for time, packet in packets]
	for packet in packets:
		channel = parse_binary(packet)
		csi = csi.append(pd.DataFrame(channel).T)
	csi.index = range(len(csi.index))
	csi.columns = [index for index in range(1, len(csi.columns)+1, 1)]
	df = df.join(csi)
	df.to_csv(csv_file)

def pcap_to_csv(pcap_file, csv_file):
	pcap = dpkt.pcap.Reader(pcap_file)
	packets = pcap.readpkts()
	udp_packets = grab_udp(packets)
        if len(udp_packets) == 0:
                raise ValueError("No UDP packets found.")
	order_packets(udp_packets)
	print_csv(udp_packets, csv_file)

if __name__ == "__main__":
        args = parse_args()
	pcap_to_csv(args.pcap, args.csv)
