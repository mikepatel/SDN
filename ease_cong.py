#!/usr/bin/python

# based on geni slice:
# poll for stats
# calculate congestion

# IMPORTs
from pox.core import core # main POX object
import pox.openflow.libopenflow_01 as of # OpenFlow 1.0 Library
import pox.lib.packet as pkt # packet parsing
from pox.lib.util import dpidToStr, strToDPID
from pox.lib.recoco import Timer
from pox.openflow.of_json import *
from datetime import datetime
import json

#####
# GLOBALs
log = core.getLogger()
global start_time
network = json.load(open("/root/pox/ext/topology.json"))

#####
# CONSTANTs
DEFAULT_PRIORITY = 32768
ARP_DL_TYPE = 0x0806
IPV4_DL_TYPE = 0x0800

WAIT_FOR_STARTUP = 15

LINK_BW = 10 # in Mbps
CONG_THRESH = 0.85 * LINK_BW
POLL_TIME = 5 # in seconds
MBPS = 8/1000000.0/POLL_TIME # convert tx bytes to Mbps

UDP_PROTO = 17
HIGH_PRIORITY = 65535

#####
# FUNCTIONs
# timer to poll switches for stats
def timer_fn():
	for conn in core.openflow.connections: # for each connected switch
		conn.send(of.ofp_stats_request(body=of.ofp_port_stats_request())) # request per-port stats

# handler for per-port stats
def _handle_port_stats(event):
	global start_time
	global network

	port_stats = flow_stats_to_list(event.stats)
	#log.debug(port_stats)	

	for node in network:
		if(dpidToStr(event.dpid) == network[node]["MAC"]): # find which switch
			for link in network[node]["link"]: # for each link connected to this switch
				try:
					# calculate updated congestion value
					link["cong_value"] = MBPS*(port_stats[link["out_port"]]["tx_bytes"] - link["prev_tx_bytes"])

					# has controller just started up?
					if((datetime.now() - start_time).total_seconds() > WAIT_FOR_STARTUP):
						#log.debug("\nBW on node %s, port %s: (Mbps): %s\n", node, link["out_port"], link["cong_value"])

						if(link["cong_value"] > CONG_THRESH): # congestion detected
							log.debug("\nCongestion on node %s, port %s\n", node, link["out_port"])
							
							if(network[node]["MAC"] == network["R4"]["MAC"]): # Are we at R4?
								# update UDP flow rule for R8
								log.debug("\nUpdate R8 flow table\n")
								
								msg = of.ofp_flow_mod()
								msg.priority = HIGH_PRIORITY
								msg.match.in_port = 3 # hardcoded
								msg.match.dl_type = IPV4_DL_TYPE
								msg.match.nw_proto = UDP_PROTO
								msg.match.nw_dst = IPAddr("172.16.0.5", 30) # hardcoded for S1
								msg.actions.append(of.ofp_action_output(port=1)) # hardcoded
								core.openflow.sendToDPID(strToDPID(network["R8"]["MAC"]), msg)
								
						
					# store tx_bytes for next iteration
					link["prev_tx_bytes"] = port_stats[link["out_port"]]["tx_bytes"]
				
				except IndexError:
					pass

#
def _handle_PacketIn(event):
	packet = event.parsed
	log.debug(packet)
	log.debug(event.ofp)

#####
# launch module
def launch():
	global start_time

	start_time = datetime.now()
	
	#log.debug(start_time)
	#core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
	core.openflow.addListenerByName("PortStatsReceived", _handle_port_stats)

	Timer(POLL_TIME, timer_fn, recurring=True)
