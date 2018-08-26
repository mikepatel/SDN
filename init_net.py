#!/usr/bin/python

# set up initial ping connectivity
# set up original path using in/out ports on switches
# based on geni slice:

# IMPORTs
from pox.core import core # main POX object
import pox.openflow.libopenflow_01 as of # OpenFlow 1.0 Library
import pox.lib.packet as pkt # packet parsing
from pox.lib.util import dpidToStr, strToDPID
from pox.lib.recoco import Timer
from pox.openflow.of_json import *
import json

#####
# GLOBALs
log = core.getLogger()
network = json.load(open("/root/pox/ext/topology.json")) 

#####
# CONSTANTs
DEFAULT_PRIORITY = 32768
ARP_DL_TYPE = 0x0806
IPV4_DL_TYPE = 0x0800

FIX_TIME = 15

#####
# FUNCTIONs
# initialize network topology
def init_network(event):
	global network
	
	for node in network:
		if(dpidToStr(event.dpid) == network[node]["MAC"]): # find which switch
			for link in network[node]["link"]:
				
				# initialize ARP
				msg = of.ofp_flow_mod()
				msg.priority = DEFAULT_PRIORITY
				msg.match.in_port = link["in_port"]
				msg.match.dl_type = ARP_DL_TYPE
				msg.actions.append(of.ofp_action_output(port=link["out_port"]))
				#msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
				event.connection.send(msg)
				
				
				# initialize IPv4				
				msg = of.ofp_flow_mod()
				msg.priority = DEFAULT_PRIORITY
				msg.match.in_port = link["in_port"]
				msg.match.dl_type = IPV4_DL_TYPE		
				msg.match.nw_dst = IPAddr(link["nw_dst"], 30)
				msg.actions.append(of.ofp_action_output(port=link["out_port"]))
				#msg.actions.append(of.ofp_action_output(port=of.OFPP_ALL))
				event.connection.send(msg)
				
#
def _handle_PacketIn(event):
	packet = event.parsed
	log.debug(packet)
	log.debug(event.ofp)

# flush flow tables on all switches
def flush_tables():
	msg = of.ofp_flow_mod(command=of.OFPFC_DELETE)
	
	for conn in core.openflow.connections:
		conn.send(msg)
		
# add ARP 
def fix():
	msg = of.ofp_flow_mod()
	msg.priority = DEFAULT_PRIORITY	
	msg.match.in_port = 5
	msg.match.dl_type = ARP_DL_TYPE
	msg.actions.append(of.ofp_action_output(port=3))
	msg.actions.append(of.ofp_action_output(port=2))
	core.openflow.sendToDPID(strToDPID("62-a1-74-3c-51-43"), msg)
	
	'''
	msg = of.ofp_flow_mod()
	msg.priority = DEFAULT_PRIORITY	
	msg.match.in_port = 5
	msg.match.dl_type = ARP_DL_TYPE
	msg.actions.append(of.ofp_action_output(port=2))
	core.openflow.sendToDPID(strToDPID("62-a1-74-3c-51-43"), msg)
	'''
	
def timer_fn():
	fix()
	
#####
# launch module
def launch():
	flush_tables()	
	core.openflow.addListenerByName("ConnectionUp", init_network)
	#fix()
	#core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
	Timer(FIX_TIME, timer_fn, recurring=False)
