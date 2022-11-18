# 🤖 robot-log-visualizer

`robot-log-visualizer` implements a python visualizer to display the data logged with
[`YarpRobotLoggerDevice`](https://github.com/ami-iit/bipedal-locomotion-framework/tree/master/devices/YarpRobotLoggerDevice) application.

## 📝 Install

Please follow one of the following method to use the software

### 🐍 Install from `pip` with apt python

Install `python3`, if not installed (in **Ubuntu 20.04**):

```console
sudo apt install python3.8 python3-virtualenv swig
```

Create a [virtual environment](https://docs.python.org/3/library/venv.html#venv-def) and activate it. For example:
```console
python3 -m venv visualizer-env
. visualizer-env/bin/activate
```

Inside the virtual environment, install the library from `pip`:

```console
pip install robot-log-visualizer
```


### 📦 Use the `AppImage`
If you are in a Linux distribution you can use the [`AppImage`](https://appimage.org/).
Please run the following command on your terminal. Remeber to change the `version` number in the following command
```console
version=0.3.0
wget https://github.com/ami-iit/robot-log-visualizer/releases/download/v${version}/robot-log-visualizer-${version}-x86_64.AppImage
chmod a+x robot-log-visualizer-${version}-x86_64.AppImage
```

Run the application
```console
./robot-log-visualizer-${version}-x86_64.AppImage
```

### 👷 Install latest version (not recommended)
If you want to use the latest feature of the `robot-log-visualizer` you can install it with the
following command
```console
python -m pip install git+https://github.com/ami-iit/robot-log-visualizer.git
```

## 🏃 Example

Once you have install the `robot-log-visualizer` you can run it from the terminal

https://user-images.githubusercontent.com/16744101/175927697-19d3b4fa-f315-483f-8ee5-ce571bf717a3.mp4


You can navigate the dataset thanks to the slider or by pressing `Ctrl-f` and `Ctrl-b` to move
forward and backward.

##  🐛 Bug reports and support
All types of [issues](https://github.com/ami-iit/robot-log-visualizer/issues/new) are welcome.

## 📝 License
Materials in this repository are distributed under the following license:

> All software is licensed under the BSD 3-Clause License. See [LICENSE](https://github.com/ami-iit/robot-log-visualizer/blob/main/LICENSE) file for details.
