#!/bin/bash
set -e

# Variables modifiables
CTID=
HOSTNAME="timelapse-lxc"
TEMPLATE="local:vztmpl/debian-12-standard_12.0-1_amd64.tar.zst"
IP=""
GW=""
DISK_SIZE="4G"
RAM="1024"
CPU="2"
PASSWORD="timelapse123"
STORAGE="local-lvm"

echo "Création du conteneur LXC $CTID avec hostname $HOSTNAME"

pct create $CTID $TEMPLATE \
  -hostname $HOSTNAME \
  -password $PASSWORD \
  -net0 name=eth0,ip=$IP,gw=$GW,bridge=vmbr0 \
  -storage $STORAGE \
  -memory $RAM \
  -cores $CPU \
  -features nesting=1 \
  -unprivileged 1

echo "Démarrage du conteneur..."
pct start $CTID
sleep 5

echo "Installation des dépendances dans le conteneur..."
pct exec $CTID -- bash -c "apt update && apt install -y python3 python3-pip git"

echo "Récupération du projet depuis GitHub..."
pct exec $CTID -- bash -c "cd /root && git clone https://github.com/oOBenjaminOo/timelapse-lxc.git"
pct exec $CTID -- bash -c "cd /root/timelapse-lxc && pip3 install -r requirements.txt"

echo "Création du service systemd pour lancer Flask..."
pct exec $CTID -- bash -c 'cat <<EOF > /etc/systemd/system/timelapse.service
[Unit]
Description=Timelapse Flask App
After=network.target

[Service]
User=root
WorkingDirectory=/root/timelapse-lxc
ExecStart=/usr/bin/python3 /root/timelapse-lxc/app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF'

pct exec $CTID -- systemctl daemon-reexec
pct exec $CTID -- systemctl enable timelapse
pct exec $CTID -- systemctl start timelapse

echo "Déploiement terminé. Le conteneur $CTID tourne et l'app Flask est accessible sur $IP:5000"
