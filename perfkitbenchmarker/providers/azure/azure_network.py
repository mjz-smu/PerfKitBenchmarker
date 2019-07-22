# Copyright 2014 PerfKitBenchmarker Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module containing classes related to Azure VM networking.

The Firewall class provides a way of opening VM ports. The Network class allows
VMs to communicate via internal ips and isolates PerfKitBenchmarker VMs from
others in
the same project. See http://msdn.microsoft.com/library/azure/jj156007.aspx
for more information about Azure Virtual Networks.
"""

#TODO add CIDR options like in GCP

import json
import threading
import logging
import collections

from perfkitbenchmarker import context
from perfkitbenchmarker import errors
from perfkitbenchmarker import flags
from perfkitbenchmarker import network
from perfkitbenchmarker import providers
from perfkitbenchmarker import resource
from perfkitbenchmarker import vm_util
from perfkitbenchmarker.providers import azure
from perfkitbenchmarker.providers.azure import util

FLAGS = flags.FLAGS
SSH_PORT = 22

DEFAULT_LOCATION = 'eastus2'


def GetResourceGroup(zone=None):
  """Get the resource group for the current benchmark."""
  spec = context.GetThreadBenchmarkSpec()
  # This is protected by spec.networks_lock, so there's no race
  # condition with checking for the attribute and then creating a
  # resource group.
  try:
    return spec.azure_resource_group
  except AttributeError:
    group = AzureResourceGroup(
        'pkb%s-%s' % (FLAGS.run_uri, spec.uid), zone=zone)
    spec.azure_resource_group = group
    return group


class AzureResourceGroup(resource.BaseResource):
  """A Resource Group, the basic unit of Azure provisioning."""

  def __init__(self, name, zone=None, use_existing=False, timeout_minutes=None):
    super(AzureResourceGroup, self).__init__()
    self.name = name
    self.use_existing = use_existing
    self.timeout_minutes = timeout_minutes
    # A resource group's location doesn't affect the location of
    # actual resources, but we need to choose *some* region for every
    # benchmark, even if the user doesn't specify one.
    self.location = (
        FLAGS.zones[0] if FLAGS.zones else zone or DEFAULT_LOCATION)
    # Whenever an Azure CLI command needs a resource group, it's
    # always specified the same way.
    self.args = ['--resource-group', self.name]

  def _Create(self):
    if not self.use_existing:
      # A resource group can own resources in multiple zones, but the
      # group itself needs to have a location. Therefore,
      # FLAGS.zones[0].
      _, _, retcode = vm_util.IssueCommand(
          [azure.AZURE_PATH, 'group', 'create',
           '--name', self.name,
           '--location', self.location,
           '--tags'] + util.GetTags(self.timeout_minutes))

      if retcode:
        raise errors.Resource.RetryableCreationError(
            'Error creating Azure resource group')

  def _Exists(self):
    stdout, _, _ = vm_util.IssueCommand(
        [azure.AZURE_PATH, 'group', 'show', '--name', self.name],
        suppress_warning=True)
    try:
      json.loads(stdout)
      return True
    except ValueError:
      return False

  def _Delete(self):
    vm_util.IssueCommand(
        [azure.AZURE_PATH, 'group', 'delete', '--yes', '--name', self.name],
        timeout=3600)

  def AddTag(self, key, value):
    """Add a single tag to an existing Resource Group.

    Args:
      key: tag key
      value: tag value

    Raises:
      errors.resource.CreationError on failure.
    """
    _, _, retcode = vm_util.IssueCommand(
        [azure.AZURE_PATH, 'group', 'update', '--name', self.name,
         '--set', 'tags.' + util.FormatTag(key, value)])
    if retcode:
      raise errors.resource.CreationError('Error tagging Azure resource group.')


class AzureAvailSet(resource.BaseResource):
  """Object representing an Azure Availability Set."""

  def __init__(self, name, location):
    super(AzureAvailSet, self).__init__()
    self.name = name
    self.location = location
    self.resource_group = GetResourceGroup()

  def _Create(self):
    """Create the availability set."""
    create_cmd = [azure.AZURE_PATH,
                  'vm',
                  'availability-set',
                  'create',
                  '--resource-group', self.resource_group.name,
                  '--name', self.name]
    if self.location:
      create_cmd.extend(['--location', self.location])
    vm_util.IssueCommand(create_cmd)

  def _Delete(self):
    pass

  @vm_util.Retry()
  def _Exists(self):
    """Returns True if the availability set exists."""
    show_cmd = [azure.AZURE_PATH,
                'vm',
                'availability-set',
                'show',
                '--output', 'json',
                '--resource-group', self.resource_group.name,
                '--name', self.name]
    stdout, _, _ = vm_util.IssueCommand(show_cmd)
    return bool(json.loads(stdout))


class AzureStorageAccount(resource.BaseResource):
  """Object representing an Azure Storage Account."""

  total_storage_accounts = 0

  def __init__(self, storage_type, location, name,
               kind=None, access_tier=None, resource_group=None,
               use_existing=False):
    super(AzureStorageAccount, self).__init__()
    self.storage_type = storage_type
    self.name = name
    self.resource_group = resource_group or GetResourceGroup()
    self.location = location
    self.kind = kind or 'Storage'
    self.use_existing = use_existing

    AzureStorageAccount.total_storage_accounts += 1

    if kind == 'BlobStorage':
      self.access_tier = access_tier or 'Hot'
    else:
      # Access tiers are only valid for blob storage accounts.
      assert access_tier is None
      self.access_tier = access_tier

  def _Create(self):
    """Creates the storage account."""
    if not self.use_existing:
      create_cmd = ([azure.AZURE_PATH,
                     'storage',
                     'account',
                     'create',
                     '--kind', self.kind,
                     '--sku', self.storage_type,
                     '--name', self.name,
                     '--tags'] + util.GetTags(
                         self.resource_group.timeout_minutes)
                    + self.resource_group.args)
      if self.location:
        create_cmd.extend(
            ['--location', self.location])
      if self.kind == 'BlobStorage':
        create_cmd.extend(
            ['--access-tier', self.access_tier])
      vm_util.IssueCommand(create_cmd)

  def _PostCreate(self):
    """Get our connection string and our keys."""
    self.connection_string = util.GetAzureStorageConnectionString(
        self.name, self.resource_group.args)
    self.connection_args = ['--connection-string', self.connection_string]
    self.key = util.GetAzureStorageAccountKey(
        self.name, self.resource_group.args)

  def _Delete(self):
    """Deletes the storage account."""
    delete_cmd = [azure.AZURE_PATH,
                  'storage',
                  'account',
                  'delete',
                  '--name', self.name,
                  '--yes'] + self.resource_group.args
    vm_util.IssueCommand(delete_cmd)

  def _Exists(self):
    """Returns true if the storage account exists."""
    stdout, _, _ = vm_util.IssueCommand(
        [azure.AZURE_PATH, 'storage', 'account', 'show',
         '--output', 'json',
         '--name', self.name] + self.resource_group.args,
        suppress_warning=True)

    try:
      json.loads(stdout)
      return True
    except ValueError:
      return False


class AzureVirtualNetwork(resource.BaseResource):
  """Object representing an Azure Virtual Network."""

  num_vnets = 0
  vnet_lock = threading.Lock()

  def __init__(self, location, name):
    super(AzureVirtualNetwork, self).__init__()
    self.name = name
    self.resource_group = GetResourceGroup()
    self.location = location
    self.args = ['--vnet-name', self.name]

    with self.vnet_lock:
      self.vnet_num = self.num_vnets
      self.__class__.num_vnets += 1

    # Allocate a different /16 in each region. This allows for 255
    # regions (should be enough for anyone), and 65536 VMs in each
    # region. Using different address spaces prevents us from
    # accidentally contacting the wrong VM.
    self.address_space_prefix = '10.%s.' % self.vnet_num
    self.address_space = '10.%s.0.0/16' % self.vnet_num

  def _Create(self):
    """Creates the virtual network."""
    vm_util.IssueCommand(
        [azure.AZURE_PATH, 'network', 'vnet', 'create',
         '--location', self.location,
         '--address-prefixes', self.address_space,
         '--name', self.name] + self.resource_group.args)

  def _Delete(self):
    """Deletes the virtual network."""
    pass

  @vm_util.Retry()
  def _Exists(self):
    """Returns true if the virtual network exists."""
    stdout, _, _ = vm_util.IssueCommand(
        [azure.AZURE_PATH, 'network', 'vnet', 'show',
         '--output', 'json',
         '--name', self.name] + self.resource_group.args,
        suppress_warning=True)

    return bool(json.loads(stdout))


class AzureSubnet(resource.BaseResource):
  """Object representing an Azure Subnet."""

  def __init__(self, vnet, name):
    super(AzureSubnet, self).__init__()
    self.resource_group = GetResourceGroup()
    self.vnet = vnet
    self.address_space = vnet.address_space_prefix + '0.0/24'
    self.name = name
    self.args = ['--subnet', self.name]

  def _Create(self):
    logging.info("subnet CREATE")
    logging.info("")
    vm_util.IssueCommand(
        [azure.AZURE_PATH, 'network', 'vnet', 'subnet', 'create',
         '--vnet-name', self.vnet.name,
         '--address-prefix', self.address_space,
         '--name', self.name] + self.resource_group.args)

  @vm_util.Retry()
  def _Exists(self):
    stdout, _, _ = vm_util.IssueCommand(
        [azure.AZURE_PATH, 'network', 'vnet', 'subnet', 'show',
         '--vnet-name', self.vnet.name,
         '--output', 'json',
         '--name', self.name] + self.resource_group.args)

    return bool(json.loads(stdout))

  def _Delete(self):
    pass


class AzureGatewaySubnet(resource.BaseResource):
  """Object representing an Azure Subnet."""

  def __init__(self, vnet):
    super(AzureGatewaySubnet, self).__init__()
    self.resource_group = GetResourceGroup()
    self.vnet = vnet
    self.name = "GatewaySubnet"
    self.address_space = vnet.address_space_prefix + '1.0/27'
    self.args = ['--subnet', self.name]

  def _Create(self):
    vm_util.IssueCommand(
        [azure.AZURE_PATH, 'network', 'vnet', 'subnet', 'create',
         '--vnet-name', self.vnet.name,
         '--address-prefix', self.address_space,
         '--name', self.name] + self.resource_group.args)

  @vm_util.Retry()
  def _Exists(self):
    stdout, _, _ = vm_util.IssueCommand(
        [azure.AZURE_PATH, 'network', 'vnet', 'subnet', 'show',
         '--vnet-name', self.vnet.name,
         '--output', 'json',
         '--name', self.name] + self.resource_group.args)

    return bool(json.loads(stdout))

  def _Delete(self):
    pass


class AzureVirtualNetworkGatewayResource(resource.BaseResource):
    # @TODO implement methods isTunnelConfiured, ConfigureTunnel

  def __init__(self, name, location, ipaddress, vnet):
    super(AzureVirtualNetworkGatewayResource, self).__init__()
    self.name = name
    self.resource_group = GetResourceGroup()
    self.location = location
    self.ipaddress = ipaddress
    self.vnet = vnet
    self.gateway_type = 'Vpn'
    self.sku = FLAGS.azure_vpngw_sku
    self.vpn_type = 'RouteBased'

  def _Create(self):
    """Creates the virtual network."""
    vm_util.IssueCommand(
        [azure.AZURE_PATH, 'network', 'vnet-gateway', 'create',
         '--location', self.location,
         '--name', self.name,
         '--vnet', self.vnet,
         '--public-ip-addresses', self.ipaddress,
         '--gateway-type', self.gateway_type,
         '--sku', self.sku,
         '--vpn-type', self.vpn_type]
         + self.resource_group.args, timeout=3600)

  def _Delete(self):
    """Deletes the virtual network gateway."""
    delete_cmd = [azure.AZURE_PATH,
                  'network',
                  'vnet-gateway',
                  'delete',
                  '--name', self.name] + self.resource_group.args
    vm_util.IssueCommand(delete_cmd, timeout=3600)

  @vm_util.Retry()
  def _Exists(self):
    """Returns true if the virtual network exists."""
    stdout, _, _ = vm_util.IssueCommand(
        [azure.AZURE_PATH, 'network', 'vnet-gateway', 'show',
         '--output', 'json',
         '--name', self.name] + self.resource_group.args,
        suppress_warning=True)

    return bool(json.loads(stdout))

  def GetIPAddress(self):

    stdout, _ = vm_util.IssueRetryableCommand(
        [azure.AZURE_PATH, 'network', 'public-ip', 'show',
         '--output', 'json',
         '--name', self.ipaddress] + self.resource_group.args)

    response = json.loads(stdout)
    return response['ipAddress']


class AzureLocalNetworkGatewayResource(resource.BaseResource):
  """Object that represents a non-azure VPN gateway.
     The actual gateway can be on another cloud or on premises.
     This object contains information about that foreign gateway
     such as IP address

  [description]
  """

  def __init__(self, name, location, ipaddress, local_address_prefixes = None):
    super(AzureLocalNetworkGatewayResource, self).__init__()
    self.name = name
    self.resource_group = GetResourceGroup()
    self.location = location
    self.ipaddress = ipaddress
    self.local_address_prefixes = local_address_prefixes

  def _Create(self):
    """Creates the virtual network."""

    cmd = [azure.AZURE_PATH, 'network', 'local-gateway', 'create',
           '--location', self.location,
           '--name', self.name,
           '--gateway-ip-address', self.ipaddress]

    if self.local_address_prefixes:
      cmd.append('--local-address-prefixes')
      cmd.append(self.local_address_prefixes)
    vm_util.IssueCommand(cmd + self.resource_group.args)

  def _Delete(self):
    """Deletes the virtual network gateway."""
    delete_cmd = [azure.AZURE_PATH,
                  'network',
                  'local-gateway',
                  'delete',
                  '--name', self.name] + self.resource_group.args
    vm_util.IssueCommand(delete_cmd)

  @vm_util.Retry()
  def _Exists(self):
    """Returns true if the virtual network exists."""
    stdout, _, _ = vm_util.IssueCommand(
        [azure.AZURE_PATH, 'network', 'local-gateway', 'show',
         '--output', 'json',
         '--name', self.name] + self.resource_group.args,
        suppress_warning=True)

    return bool(json.loads(stdout))



#az network vnet-gateway create --resource-group=perfkit --name=gateway1
#  --public-ip-addresses=ipaddress1 --vnet=vnet1 --location=eastus
#  --gateway-type=Vpn --sku=VpnGw1 --vpn-type=RouteBased

#TODO need address space for gcp vpn tunnel setup
class AzureVirtualNetworkGateway(network.BaseVPNGW):
  """An object representing the VPN gateway for Azure"""
  CLOUD = providers.AZURE


  def __init__(self, name, vnet, location, gateway_subnet, public_ip, cidr=None):
    super(AzureVirtualNetworkGateway, self).__init__()
    self._lock = threading.Lock()
    self.forwarding_rules = {}
    self.tunnels = {}
    self.routes = {}
    self.resource_group = GetResourceGroup()
    self.name = name
    self.vnet = vnet
    self.location = location
    self.cidr = self.vnet.address_space

    # this is an AzurePublicIPAddress object
    self.public_ip = public_ip

    # this is the IP address string that is used by VPN.GetVPN
    self.IP_ADDR = None
    self.gateway_subnet = gateway_subnet
    self.vpngw_resource = AzureVirtualNetworkGatewayResource(name,
                            location, self.public_ip.name, self.vnet.name)
    self.created = False
    self.suffix = collections.defaultdict(dict)  # holds uuid tokens for naming/finding things (double dict)
    self.cloud = AzureVirtualNetworkGateway.CLOUD
    self.ZONE = location
    self.require_target_to_init = False
    self.localGateway = None

  def SetupForwarding(self, suffix=''):
    pass

  def SetupRouting(self, target_gw, suffix=''):
    pass

  def AllocateIP(self):
    self.IP_ADDR = self.vpngw_resource.GetIPAddress()
    logging.info("IP ADDRESS")
    logging.info(self.IP_ADDR)

  # az network vpn-connection create --resource-group=perfkit
  # --name connection1 --vnet-gateway1=gateway1
  # --vnet-gateway2=gateway2 --shared-key=123123
  def SetupTunnel(self, target_gw, psk, suffix=''):
    """Create IPSec tunnels  between the source gw and the target gw.

    Args:
      target_gw: The BaseVPN object to point forwarding rules at.
      psk: shared key
    """

    tunnel_name = self.name + "_tunnel"
    logging.info("SETUP TUNNEL --")
    cmd = []

    # TODO setup local gateway for not azure vpn gateways
    if target_gw.CLOUD != 'Azure':
      # TODO change name parameter
      logging.info("INTER CLOUD GATEWAY DETECTED")
      self.localGateway = AzureLocalNetworkGatewayResource(target_gw.name,
                                                           self.location,
                                                           target_gw.IP_ADDR,
                                                           target_gw.cidr)
      self.localGateway.Create()

      cmd = [azure.AZURE_PATH, 'network', 'vpn-connection', 'create',
             '--location', self.location,
             '--name', tunnel_name,
             '--vnet-gateway1', self.name,
             '--local-gateway2', target_gw.name,
             '--shared-key', psk]

    else:
      cmd = [azure.AZURE_PATH, 'network', 'vpn-connection', 'create',
             '--location', self.location,
             '--name', tunnel_name,
             '--vnet-gateway1', self.name,
             '--vnet-gateway2', target_gw.name,
             '--shared-key', psk]

    vm_util.IssueCommand(cmd + self.resource_group.args)

  def DeleteTunnel(self, tunnel):
    """Delete IPSec tunnel"""
    vm_util.IssueCommand(
        [azure.AZURE_PATH, 'network', 'vpn-connection', 'delete',
         '--name', self.name] + self.resource_group.args)

  def Create(self):
    """Creates the actual VPNGW."""
    benchmark_spec = context.GetThreadBenchmarkSpec()
    if benchmark_spec is None:
      raise errors.Error('GetNetwork called in a thread without a '
                         'BenchmarkSpec.')
    # with self._lock:
    if self.created:
      return
    if self.vpngw_resource:
      self.vpngw_resource.Create()

    # self.vpngw_resource._Exists()
    self.IP_ADDR = self.vpngw_resource.GetIPAddress()
    logging.info("IP ADDRESS")
    logging.info(self.IP_ADDR)

    key = self.name
    # with benchmark_spec.vpngws_lock:
    if key not in benchmark_spec.vpngws:
      benchmark_spec.vpngws[key] = self

    logging.info("BENCHMARK SPEC VPNGWS")
    logging.info(benchmark_spec.vpngws)
    self.created = True
    return benchmark_spec.vpngws[key]

  def Delete(self):
    """Deletes the actual VPNGW."""
    # if self.IP_ADDR and self.IPExists():
    #   self.DeleteIP()

    if self.tunnels:
      for tun in self.tunnels:
        if self.TunnelExists(tun):
          self.DeleteTunnel(tun)

    # self.created = False

    # vpngws need deleted last
    if self.vpngw_resource:
      self.vpngw_resource.Delete()

    if self.localGateway:
      self.localGateway.Delete()

  def __repr__(self):
    return '%s(%r)' % (self.__class__, self.__dict__)

# az network public-ip create --resource-group={group_name} --name={} --location={}
class AzurePublicIPAddress(resource.BaseResource):
  def __init__(self, location, name):
    super(AzurePublicIPAddress, self).__init__()
    self.name = name
    self.resource_group = GetResourceGroup()
    self.location = location
    self.args = ['--public-ip-addresses', self.name]

  def _Create(self):
    """Creates the virtual network."""
    vm_util.IssueCommand(
        [azure.AZURE_PATH, 'network', 'public-ip', 'create',
         '--location', self.location,
         '--name', self.name] + self.resource_group.args)

  def _Delete(self):
    """Deletes the Public IP Address."""
    delete_cmd = [azure.AZURE_PATH,
                  'network',
                  'public-ip',
                  'delete',
                  '--name', self.name] + self.resource_group.args
    vm_util.IssueCommand(delete_cmd)

  @vm_util.Retry()
  def _Exists(self):
    """Returns true if the virtual network exists."""
    stdout, _, _ = vm_util.IssueCommand(
        [azure.AZURE_PATH, 'network', 'public-ip', 'show',
         '--output', 'json',
         '--name', self.name] + self.resource_group.args,
        suppress_warning=True)

    return bool(json.loads(stdout))

class AzureNetworkSecurityGroup(resource.BaseResource):
  """Object representing an Azure Network Security Group."""

  def __init__(self, location, subnet, name):
    super(AzureNetworkSecurityGroup, self).__init__()

    self.location = location
    self.subnet = subnet
    self.name = name
    self.resource_group = GetResourceGroup()
    self.args = ['--nsg', self.name]

    self.rules_lock = threading.Lock()
    # Mapping of (start_port, end_port) -> rule name, used to
    # deduplicate rules. We expect duplicate rules because PKB will
    # call AllowPort() for each VM on a subnet, but the rules are
    # actually applied to the entire subnet.
    self.rules = {}
    # True if the special 'DenyAll' rule is present.
    self.have_deny_all_rule = False

  def _Create(self):
    vm_util.IssueCommand(
        [azure.AZURE_PATH, 'network', 'nsg', 'create',
         '--location', self.location,
         '--name', self.name] + self.resource_group.args)

  @vm_util.Retry()
  def _Exists(self):
    stdout, _, _ = vm_util.IssueCommand(
        [azure.AZURE_PATH, 'network', 'nsg', 'show',
         '--output', 'json',
         '--name', self.name] + self.resource_group.args)

    return bool(json.loads(stdout))

  def _Delete(self):
    pass

  def AttachToSubnet(self):
    vm_util.IssueRetryableCommand(
        [azure.AZURE_PATH, 'network', 'vnet', 'subnet', 'update',
         '--name', self.subnet.name,
         '--network-security-group', self.name] +
        self.resource_group.args +
        self.subnet.vnet.args)

  def AllowPort(self, vm, start_port, end_port=None, source_range=None):
    """Open a port or port range.

    Args:
      vm: the virtual machine to open the port for.
      start_port: either a single port or the start of a range.
      end_port: if given, the end of the port range.
      source_range: unsupported at present.

    Raises:
      ValueError: when there are too many firewall rules.
    """

    with self.rules_lock:
      end_port = end_port or start_port

      if (start_port, end_port) in self.rules:
        return
      port_range = '%s-%s' % (start_port, end_port)
      rule_name = 'allow-%s' % port_range
      # Azure priorities are between 100 and 4096, but we reserve 4095
      # for the special DenyAll rule created by DisallowAllPorts.
      rule_priority = 100 + len(self.rules)
      if rule_priority >= 4095:
        raise ValueError('Too many firewall rules!')
      self.rules[(start_port, end_port)] = rule_name

    vm_util.IssueRetryableCommand(
        [azure.AZURE_PATH, 'network', 'nsg', 'rule', 'create',
         '--name', rule_name,
         '--destination-port-range', port_range,
         '--access', 'Allow',
         '--priority', str(rule_priority)]
        + self.resource_group.args
        + self.args)


class AzureFirewall(network.BaseFirewall):
  """A fireall on Azure is a Network Security Group.

  NSGs are per-subnet, but this class is per-provider, so we just
  proxy methods through to the right NSG instance.
  """

  CLOUD = providers.AZURE

  def AllowPort(self, vm, start_port, end_port=None, source_range=None):
    """Opens a port on the firewall.

    Args:
      vm: The BaseVirtualMachine object to open the port for.
      start_port: The local port to open.
      end_port: if given, open the range [start_port, end_port].
      source_range: unsupported at present.
    """

    vm.network.nsg.AllowPort(vm, start_port, end_port=end_port,
                             source_range=source_range)

  def DisallowAllPorts(self):
    """Closes all ports on the firewall."""
    pass


class AzureNetwork(network.BaseNetwork):
  """Regional network components.

  A container object holding all of the network-related objects that
  we need for an Azure zone (aka region).
  """

  CLOUD = providers.AZURE

  def __init__(self, spec):
    super(AzureNetwork, self).__init__(spec)

    self.resource_group = GetResourceGroup()
    avail_set_name = '%s-%s' % (self.resource_group.name, self.zone)
    self.avail_set = AzureAvailSet(avail_set_name, self.zone)

    # Storage account names can't include separator characters :(.
    storage_account_prefix = 'pkb%s' % FLAGS.run_uri

    # Storage account names must be 3-24 characters long and use
    # numbers and lower-case letters only, which leads us to this
    # awful naming scheme.
    suffix = 'storage%d' % AzureStorageAccount.total_storage_accounts
    self.storage_account = AzureStorageAccount(
        FLAGS.azure_storage_type, self.zone,
        storage_account_prefix[:24 - len(suffix)] + suffix)
    prefix = '%s-%s' % (self.resource_group.name, self.zone)
    self.vnet = AzureVirtualNetwork(self.zone, prefix + '-vnet')
    self.subnet = AzureSubnet(self.vnet, self.vnet.name + '-subnet')
    self.nsg = AzureNetworkSecurityGroup(self.zone, self.subnet,
                                         self.subnet.name + '-nsg')

    self.gateway_ip = None
    self.gateway_subnet = None
    self.vpngw = {}

    if FLAGS.use_vpn:
      logging.info("USE VPN")
      logging.info("num tunnels: " + str(FLAGS.vpn_service_tunnel_count))

      gateway_count = FLAGS.vpn_service_gateway_count

      if FLAGS.vpn_service_gateway_count > 1:
        logging.warning("--vpn_service_gateway_count=" +
                        str(FLAGS.vpn_service_gateway_count) +
                        " Only 1 Virtual Network Gateway allowed per" +
                        " vnet in Azure. Flag value will be ignored for" +
                        " Azure vnets and only 1 gateway will be" +
                        " created in this vnet.")
        gateway_count = 1

      for gatewaynum in range(0, gateway_count):
        vpngw_name = 'vpngw-%s-%s-%s' % (
            self.zone, gatewaynum, FLAGS.run_uri)
        ip_name = 'public-ip-gateway-%s-%s' % (self.zone, FLAGS.run_uri)
        self.gateway_ip = AzurePublicIPAddress(self.zone, ip_name)
        self.gateway_subnet = AzureGatewaySubnet(self.vnet)
        #name, vnet, location, publicip, cidr=None
        self.vpngw[vpngw_name] = AzureVirtualNetworkGateway(
            vpngw_name, self.vnet, self.zone,
            self.gateway_subnet, self.gateway_ip)

  @vm_util.Retry()
  def Create(self):
    """Creates the network."""
    # If the benchmark includes multiple zones,
    # self.resource_group.Create() will be called more than once. But
    # BaseResource will prevent us from running the underlying Azure
    # commands more than once, so that is fine.
    logging.info("CREATE HERE")
    self.resource_group.Create()

    self.avail_set.Create()

    self.storage_account.Create()

    self.vnet.Create()

    self.subnet.Create()

    self.nsg.Create()
    self.nsg.AttachToSubnet()

    if getattr(self, 'vpngw', False):
      logging.info("CREATE VPN RESOURCES")
      for gw in self.vpngw:
        self.gateway_ip.Create()
        self.gateway_subnet.Create()
        self.vpngw[gw].Create()

  def Delete(self):
    """Deletes the network."""
    # If the benchmark includes multiple zones, this will be called
    # multiple times, but there will be no bad effects from multiple
    # deletes.
    self.resource_group.Delete()



# az network vnet create --resource-group perfkit --name vnet3 --address-prefixes 10.0.0.0/16 --subnet-name=subnet3 --subnet-prefixes=10.0.0.0/16 --location=northcentralus

 
#   vnet1
#     EastUS
#     192.168.0.0/16

#     subnet1
#     192.168.1.0/24

#   vnet2
#     NorthCentralUS
#     172.16.0.0/16

#     subnet2
#     172.16.1.0/24


# az network public-ip create --resource-group=perfkit --name=ipaddress1 --location=eastus
  
#   ipaddress1

# az network vnet subnet create --resource-group=perfkit --vnet-name=vnet1 --name=GatewaySubnet --address-prefixes=192.168.0.0/24


# az network vnet subnet create --resource-group=perfkit --vnet-name=vnet2 --name=GatewaySubnet --address-prefixes=172.16.0.0/24

# **NOTE IT TAKES A LONG WHILE FOR THESE TO RUN
# real  25m29.608s


# az network vnet-gateway create --resource-group=perfkit --name=gateway1  --public-ip-addresses=ipaddress1 --vnet=vnet1 --location=eastus  --gateway-type=Vpn --sku=VpnGw1 --vpn-type=RouteBased

# az network vnet-gateway create --resource-group=perfkit --name=gateway2  --public-ip-addresses=ipaddress2 --vnet=vnet2 --location=northcentralus  --gateway-type=Vpn --sku=VpnGw1 --vpn-type=RouteBased


# az network vpn-connection create --resource-group=perfkit --name connection1 --vnet-gateway1=gateway1 --vnet-gateway2=gateway2 --shared-key=123123
