#!/bin/bash
set -e

# Variables modifiables
CTID=${1:-110}                # ID du conteneur Proxmox par défaut 110
HOSTNAME=${2:-timelapse-lxc}  # Nom du conteneur
PASSWORD=${3:-rootpass}       # Mot de passe root du conteneur
IP=${4:-192.168.73.210/24}   # IP statique du conteneur (ajuste selon ton réseau)
GATEWAY=${5:-192.168.73.1}   # Passerelle
REPO="https://github.com/oOBenjaminOo/timelapse-lxc.git"
BRIDGE="vmbr0"                # Interface bridge de Proxmox

echo "Création du conteneur LXC $CTID avec hostname $HOSTNAME"

# Créer le conteneur Debian minimal (buster ou bullseye selon proxmox)
pct create $CTID local:vztmpl/debian-11-standard_11.7-1_amd64.tar.gz \
    -hostname $HOSTNAME \
    -password $PASSWORD \
    -net0 name=eth0,bridge=$BRIDGE,ip=$IP,gw=$GATEWAY \
    -memory 512 \
    -cores 1 \
    -features nesting=1 \
    -unprivileged 0

echo "Démarrage du conteneur..."
pct start $CTID

echo "Installation des dépendances dans le conteneur..."

pct exec $CTID -- bash -c "
  apt-get update && apt-get install -y python3 python3-pip git
  cd /root
  if [ ! -d timelapse-lxc ]; then
    git clone $REPO
  else
    cd timelapse-lxc && git pull
  fi
  pip3 install flask
"

echo "Création du service systemd pour lancer Flask..."

SERVICE="[Unit]
Description=Timelapse Flask App
After=network.target

[Service]
User=root
WorkingDirectory=/root/timelapse-lxc
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
"

echo "$SERVICE" | pct exec $CTID tee /etc/systemd/system/timelapse.service > /dev/null

pct exec $CTID -- bash -c "
  systemctl daemon-reload
  systemctl enable timelapse.service
  systemctl start timelapse.service
"

echo "Déploiement terminé. Le conteneur $CTID tourne et l'app Flask est accessible sur $IP:5000"
