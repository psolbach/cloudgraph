#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import time
import os
import sys
import logging
import datetime
import pickle
import struct

import boto.ec2.cloudwatch


class CloudGraph(object):
    """Interface with Carbon Cache and offload time-series metrics
    converted from AWS CloudWatch to Socket Connection.
    Supports both Plain Text and Pickle Methods.
    Instance needs access as per IAM role"""

    class InvalidIAMPerms(EnvironmentError):
        pass

    def __init__(self, namespace=None, method="plain",
                target="cloudwatch", EC2_REGION="us-west-1",
                CARBON_PORT=2003, CARBON_PICKLE_PORT=2004,
                CARBON_SERVER="0.0.0.0"):
        
        self.method = method
        self.target = target
        self.namespace = namespace

        self.sock = socket.socket()
        self.sock.connect((CARBON_SERVER, 
            (CARBON_PICKLE_PORT if method == "pickle"
                else CARBON_PORT)))

        try: self.c = boto.ec2.cloudwatch.connect_to_region(EC2_REGION)
        except: raise InvalidIAMPerms('IAM role for the instance set?')

        self.metrics = sorted(self.c.list_metrics(
            namespace=namespace),
            key=str)

        logging.basicConfig(level=logging.INFO)
        self.log = logging.getLogger("cloudgraph")


    def __enter__(self):
        return self


    def __exit__(self, type, value, traceback):
        self.sock.close()


    def _find_metrics(self, **kwargs):
        """Map requested metrics to a BOOL: If kwargs subset
        of available metric labels. Add results to query-list.
        """

        self.querylist = []
        for k,v in kwargs.items():
            kwargs[k] = [v]

        for m in self.metrics:
            if all(item in m.dimensions.items() for item in kwargs.items()):
                self.querylist.append(m)


    def _graphite_m(self, name):
        """Plain Old Graphite dot-Notation"""

        return "{0}.{1}.{2}".format(self.target,
            ".".join(self.dimensions.values()),
            name.lower())


    def _timestamp(self, datetime):
        """Plain Old Unix Timestamp"""
        return time.mktime(datetime.timetuple())


    def _tuple(self, d, i):
        """Datapoint: MetricName Value Time"""

        name = self.querylist[i].name
        graphite_m = self._graphite_m(name)
        unixtime = self._timestamp(d["Timestamp"])
        
        if self.method == "pickle":
            return (unixtime, d[self.statistic])
        
        return ('%s %s %d\n' % (graphite_m, 
                                d[self.statistic],
                                unixtime))


    def get_metrics(self, **kwargs):
        """All your metrics are belong"""

        self.dimensions = kwargs
        self._find_metrics(**kwargs)

        if not self.querylist:
            raise Exception("Invalid dimensions.")


    def query_metrics(self, *args, **kwargs):
        """Options:
        Stat => 'Minimum', 'Maximum', 'Sum', 'Average', 'SampleCount'
        Unit => 'Seconds', 'Microseconds', 'Milliseconds', 'Bytes' ...
        cf. http://boto.readthedocs.org/en/latest/ref/cloudwatch.html
        """

        self.response = []
        self.statistic = args[2]   
        for m in self.querylist:
            data = m.query(*args, **kwargs)

            if data:
                self.response.append(data)

        if not self.response:
            self.log.info('[-] no metrics')
            return


    def send_pickle(self):
        """Generate Tuples from multiple Query results
        and submit in one batch. Pickled payload needs
        to be preceeded by a custom C type header.
        """

        metrics = []

        for i, m in enumerate(self.response):
            name = self.querylist[i].name
            datapoints = [self._tuple(d, i) for d in m]

            metrics.append((self._graphite_m(name), 
                            datapoints[0]))
        
        payload = pickle.dumps(metrics)
        header = struct.pack("!L", len(payload))

        self.log.info('[+] {0} metrics'.format(len(metrics)))
        self.sock.sendall(header + payload)


    def send_plain(self):
        """Send exactly one metric tuple"""

        payload = self._tuple(self.response[0][0], 0)
        self.log.info('[+] sending 1 metric')
        self.sock.sendall(payload)

