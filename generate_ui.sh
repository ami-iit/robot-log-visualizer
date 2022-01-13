#! /bin/bash
echo "Generate UI"
pyuic5 -o ui/visualizer.py ui/visualizer.ui

echo "Generate About"
pyuic5 -o ui/about.py ui/about.ui
