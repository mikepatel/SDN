# SDN
Software-Defined Networking project to perform traffic balancing

Used POX controller and Ubuntu 16.04 VMs

## SDN part
This section will show the way to simulate SDN on Linux Virtual Machine.

### Environment

Ubuntu 16.04 - hosts, switches, controller
POX - flavor of SDN controller

### Tools
* ping
* iperf
* tcpdump

### Deployment

#### Switch

Install ovs packages
``` 
apt-get update
apt-get install openvswitch-switch
```

Add bridge
```
ovs-vsctl add-br <br>
```

Add ports
```
ovs-vsctl add-port <br> <port>
```

Point to controller
```
ovs-vsctl set-controller <br> tcp:<public IP address of controller>:6633
```

#### Controller

Get POX
```
git clone http://github.com/noxrepo/pox
```

Change directory
```
cd pox
```

Develop own Python modules in "ext" directory

### Test

#### Connectivity
```
./pox.py log.level --DEBUG init_net
```

#### Detecting congestion
```
./pox.py log.level --DEBUG init_net detect_cong
```

#### Easing congestion
```
./pox.py log.level --DEBUG init_net ease_cong
```
