#!/bin/bash


cd /home/pi/

pip install pyyaml
sudo apt-get install -y python-yaml

sudo rm -rf /home/pi/otone_backend_rsa
sudo cp -al /home/pi/otone_backend /home/pi/otone_backend_rsa

sudo rm -rf /home/pi/otone_frontend_rsa
sudo cp -al /home/pi/otone_frontend /home/pi/otone_frontend_rsa

sudo rm -rf /home/pi/otone_backend
sudo rm -rf /home/pi/otone_frontend

eval `ssh-agent -s`
ssh-add -D
ssh-add ~/.ssh/ot_frontend_rsa
ssh-add ~/.ssh/ot_backend_rsa

git clone --progress git@github.com:Opentrons/otone_backend.git > /home/pi/otone_scripts/gt_backend 2>&1

B_FF=$(grep -o 'Cloning into' /home/pi/otone_scripts/gt_backend)
B_AR=$(grep -o 'Receiving objects: 100%' /home/pi/otone_scripts/gt_backend)
B_CC=$(grep -o 'Checking connectivity... done.' /home/pi/otone_scripts/gt_backend)
echo ''
echo 'B_FF = '$B_FF
echo 'B_AR = '$B_AR
echo 'B_CC = '$B_CC
echo ''
echo '/home/pi/otone_scripts/gt_backend:'
echo $(cat /home/pi/otone_scripts/gt_backend)
echo ''

git clone --progress git@github.com:Opentrons/otone_frontend.git > /home/pi/otone_scripts/gt_frontend 2>&1

F_FF=$(grep -o 'Cloning into' /home/pi/otone_scripts/gt_frontend)
F_AR=$(grep -o 'Receiving objects: 100%' /home/pi/otone_scripts/gt_frontend)
F_CC=$(grep -o 'Checking connectivity... done.' /home/pi/otone_scripts/gt_frontend)
echo ''
echo 'F_FF = '$F_FF
echo 'F_AR = '$F_AR
echo 'F_CC = '$F_CC
echo ''
echo '/home/pi/otone_scripts/gt_frontend:'
echo $(cat /home/pi/otone_scripts/gt_frontend)
echo ''
sudo systemctl disable otone.service
sudo systemctl stop otone.service