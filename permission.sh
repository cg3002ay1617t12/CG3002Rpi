#!/bin/bash
sudo systemctl stop serial-getty@ttyAMA0
sudo systemctl disable serial-getty@ttyAMA0
sudo chmod g+r /dev/ttyAMA0
