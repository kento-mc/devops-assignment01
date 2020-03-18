# devops-assignment01
Dev Ops assignment 01 for the WIT 2019 HDIP

## run_webserver.py

The run_webserver.py file can be run from the command line with no arguments or with one argument (the user's private key pem file).

### With no arguments

The user will be prompted to provide a private key pem file, otherwise one will be created.

### With one argument

The user's private key pem file is passed as a command line argument


The script then attempts to create a new security group. If one of that name already exists the user is prompted to run their EC2 instance in the existing group, otherwise they are given the option to delete that security group or create a new one and specify a name.

After the instance is launched, the user is given the choice to use an existing S3 bucket or create a new one.

Once the instance is launched and the server configured the link to the home page is provided before the script completes.

## monitoring.py

The monitoring.py file can be run from the command line after the run_webserver.py script completes. It will print the average CPU usage for the instance.
