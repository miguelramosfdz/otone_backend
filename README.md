# Backend Python Component of the OpenTrons OT.One

This is the minimum viable product backend component of the OpenTrons OT.One. It runs the business logic on python3 and Crossbar.io (python2).

# The OT.One Components

The three components of the OpenTrons OT.One software are:
* Frontend (/home/pi/otone_frontend)
* Backend (/home/pi/otone_backend)
* Scripts (/home/pi/otone_scripts)

Additionally, SmoothiewareOT is OpenTrons' version of the Smoothieware firmware running on the Smoothieboard motorcontroller board.

All three components run together and are started with the script *start.sh* in otone_scripts. The *start.sh* script is called on startup.

