#Environment Setup Instructions:
This codebase runs on Python 3.6. It's recommended you use conda and set up conda environment:
>conda create -n myenv python=3.6
>conda activate myenv

After you cd into this repository you set up a conda environment go into main code repo by running
>cd Control_And_Interface_Software

#To install all the required packages run:
python3 -m pip install -r requirements.txt

This should allow you to run the control software.

#X-Plane UDP telemetry setup:
It's assumed you have already install X-Plane 12 or X-Plane 11. XPPython is an X-Plane plugin which allows to integrate python functionality. In this case a script called "PI_simple_telemetry.py" within "Control_And_Interface_Software\X_Plane_Plugins"
will send out the current simulated airplane's motion as a UDP message on port 10022 on the system's localhost ip (127.0.0.1). This is neccesary to ensure the control software can obtain the airplane's motion and move the platform accordingly.

Go to XPPython's "https://xppython3.readthedocs.io/en/3.1.5/usage/installation_plugin.html" website and follow the required instructions to install XPPython.

After going through the neccesary setup outlined in the site, drag and drop "PI_simple_telemetry.py" from "Control_And_Interface_Software\X_Plane_Plugins" to "C:\X-Plane 11\Resources\plugins\PythonPlugins". Everytime a plane simulation 
is run, the script will output the airplane's motion in the required format through UDP port 1022 on the system's localhost ip (127.0.0.1).

#How to run main control software:
Activate your environment with "conda activate myenv"
  
##For the core software state machine cd into repo folder and run the following commands:
    >cd Control_And_Interface_Software\X_Plane_To_Chair_Control_App\src
    >python state_machine.py

  This script forms the core logic that'll control the platform

  To activate the GUI that allows you to control the flight motion platform, on a separate terminal:
    >cd Control_And_Interface_Software\X_Plane_To_Chair_Control_App\src
    >python "platform_control_app.py"
  The START, STOP and RESET simulation buttons do as they imply. START starts moving the platform as X-Plane runs. STOP stops moving the platform. RESET resets back to idle state where motion can be started again by pressing START.

  To activate the safe state dummy that is required to fool the state machine into thinking the platform is in it's safe state:
    >cd Control_And_Interface_Software\X_Plane_To_Chair_Control_App\src
    >python "safe_state_dummy.py"

  Assumming the motion platform is connected on ip "192.168.0.10", the software should work for the physical MDX flight motion platform
  
#How to replace telemetry input to dummy_airplane input:
  Alternatively, if you have want to manually control the flight motion platform:
    >cd Control_And_Interface_Software\X_Plane_To_Chair_Control_App\src
    Open state_machine.py and replace line 18 "TELEMETRY_UDP_PORT = 10022" with "TELEMETRY_UDP_PORT = 5005"
    In the same directory run:
    >python dummy_airplane_app.py

  This will open up an application which allows you to set the pose of the motion platform with some sliders