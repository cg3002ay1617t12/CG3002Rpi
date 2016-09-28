#!/bin/bash
sudo systemctl stop serial-getty@ttyAMA0
sudo systemctl disable serial-getty@ttyAMA0
sudo chmod g+r /dev/ttyAMA0
nohup python main.py > /dev/null &
nohup python keyboard_sim.py > /dev/null &
