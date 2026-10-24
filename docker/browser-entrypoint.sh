#!/usr/bin/env bash
set -euo pipefail
# Dedicated browser network namespace only. Failure to install either address
# family's firewall is fatal; there is no permissive fallback.
proxy_ip=172.30.88.2
iptables -P OUTPUT DROP
iptables -F OUTPUT
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -d "$proxy_ip" -p tcp --dport 8888 -j ACCEPT
ip6tables -P OUTPUT DROP
ip6tables -F OUTPUT
ip6tables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -C OUTPUT -d "$proxy_ip" -p tcp --dport 8888 -j ACCEPT
[[ "$(iptables -S OUTPUT | head -1)" == '-P OUTPUT DROP' ]]
[[ "$(ip6tables -S OUTPUT | head -1)" == '-P OUTPUT DROP' ]]
mkdir -p /run/veyra
chown pwuser:pwuser /run/veyra
# Ready evidence must never survive a failed restart.
if [[ -f /run/veyra/ready.json ]]; then mv /run/veyra/ready.json /run/veyra/previous-ready.json; fi
printf '{"ipv4":"OUTPUT DROP; established + gateway:8888 only","ipv6":"OUTPUT DROP; established only","proxyIp":"172.30.88.2"}\n' > /run/veyra/firewall.json
# The Chromium/Node user has no network-administration capabilities.
exec setpriv --reuid=pwuser --regid=pwuser --init-groups --bounding-set=-all --inh-caps=-all --ambient-caps=-all node /opt/veyra-browser/browser-server.cjs
