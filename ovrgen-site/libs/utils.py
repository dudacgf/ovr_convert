# utilities for formatting output and validating user input
#
# dudacgf - 2021
#

import re
import netaddr
from netaddr import AddrFormatError

from defusedxml import ElementTree as Et
from defusedxml.ElementTree import ParseError as ParseError

def size_format(b):
    if b < 1000:
        return '%i' % b + 'B'
    elif 1000 <= b < 1000000:
        return '%.1f' % float(b/1000) + 'KB'
    elif 1000000 <= b < 1000000000:
        return '%.1f' % float(b/1000000) + 'MB'
    elif 1000000000 <= b < 1000000000000:
        return '%.1f' % float(b/1000000000) + 'GB'
    elif 1000000000000 <= b:
        return '%.1f' % float(b/1000000000000) + 'TB'

def valid_xml(filename):
    try:
        root = Et.parse(filename).getroot()
    except ParseError:
        return False
    
    return root.tag == 'report' and root.get('content_type') == 'text/xml' 

def valid_network(ip):
    if '-' in ip:
        try:
            _start_ip, _end_ip = ip.split('-')
            ip_range = netaddr.IPRange(_start_ip, _end_ip)
        except (ValueError, AddrFormatError):
            return False
    else:
        try:
            network = netaddr.IPNetwork(ip)
        except AddrFormatError:
            return False
    return True

def valid_regex(regex_entry):
    try:
        re.compile(regex_entry, re.IGNORECASE)
    except re.error:
        return False
    return True

def valid_cve(cve_entry):
    return re.match("^CVE-\d\d\d\d-\d+$", cve_entry)

def make_data_table(lines=None, header=None):
    if lines is None or header is None:
        return({})
    
    i = 1    
    dataTable = []
    for l in lines:
        dataTable.append({'id': i, header: l})
        i = i + 1
    return dataTable