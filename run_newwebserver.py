#!/usr/bin/env python3
import boto3
import os
import sys
import subprocess
import time
ec2 = boto3.resource('ec2')
ec2Client = boto3.client('ec2')
keyName = ''

if len(sys.argv) > 1:
    keyName = os.path.splitext(sys.argv[1])[0]
else:
    print('')
    print('Welcome! You\'re about to spin up your custom web server.')
    print('')
    ans = input('''Do you already have a key pair to use for the new EC2 instance?
    (If not, one will be generated for you)
    (y/n): ''')
    if ans[0] == 'y' or ans[0] == 'Y':
        print('')
        print('Great! First, make sure the your_key.pem file is in the current directory.')
        print('')
        ans = input('Please enter the file name without the .pem extension: ')
        keyName = ans
    else:
        keyNameString = 'assignment01-keypair'
        keyString = 'assignment01-keypair.pem'
        print('')
        print('Generating new key pair: \'' + keyNameString + '\'...')
        # The block below is taken from the assignment tips document
        # create a file to store the key locally
        outfile = open(keyString,'w')
        # call the boto ec2 function to create a key pair
        while True:
            try:
                key_pair = ec2.create_key_pair(KeyName=keyString)
                break
            except Exception as error:
                ec2Client.delete_key_pair(KeyName=keyString)
        # capture the key and store it in a file
        KeyPairOut = str(key_pair.key_material)
        print('')
        print('New key pair:')
        print(KeyPairOut)
        outfile.write(KeyPairOut)
        keyName = 'assignment01-keypair'

print(keyName)
ans = input('Another question')

# spin up new ec2 instance and configure web server
instance = ec2.create_instances(
    ImageId='ami-099a8245f5daa82bf', #TODO update to retrieve dynamically
    InstanceType='t2.nano',
    KeyName=keyName,
    MinCount=1,
    MaxCount=1,
    SecurityGroupIds=['sg-04b2eda6495892f38'], #TODO update to create new security group
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'Assignment 01'
                },
            ]
        },
    ],
    UserData='''#!/bin/bash
                yum update -y
                yum install httpd -y
                systemctl enable httpd
                systemctl start httpd''')

print('')
print('New EC2 instance spinning up...')
instance[0].wait_until_running(
    Filters=[
        {
            'Name': 'instance-state-name',
            'Values': [
                'running',
            ]
        },
    ],
)

instance[0].reload()
print('New EC2 instance running: ' + instance[0].instance_id)
print('')

# download the image to the local directory
subprocess.run(['curl', '-O', 'http://devops.witdemo.net/image.jpg'])


#status = ec2.instances.filter(
#        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])


status = ec2Client.describe_instance_status()
#print(status)
s3 = boto3.resource("s3")
bucket_name = 'wit2020-devops-kchadwick-w05-2020-02-27-1582823115'
object_name = 'image.jpg'
region_name = boto3.session.Session().region_name # save region name to variable
public_ip = instance[0].public_ip_address
key_path = '~/dev/wit/devops/01/kchadwick_key.pem'

try:
    # add ACL='public-read' to put arguments to allow public access to image
    response = s3.Object(bucket_name, object_name).put(Body=open(object_name, 'rb'),ACL='public-read')
    #print (response)
    # build url string from relevant variables
    url_string = "https://%s.s3-%s.amazonaws.com/%s" % (bucket_name, region_name, object_name)

    subprocess.run("echo '<html>' > index.html", shell=True)
    command = "echo '<img src=\"%s\">' >> index.html" % (url_string)
    subprocess.run(command, shell=True)
    subprocess.run("echo '<br>' >> index.html", shell=True)

    print('')
    print('Establishing ssh connection to server (This may take a few seconds)')
    print('')
    time.sleep(15)
    instance[0].reload()
    command = "scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -rp -i " + key_path + " index.html ec2-user@" + public_ip + ":."
    subprocess.run(command, shell=True)

    sshCmd = "ssh -o StrictHostKeyChecking=no -i " + key_path + " ec2-user@" + public_ip

    command = sshCmd + " \'echo \"Private IP address: \" >> index.html\'"
    subprocess.run(command, shell=True)

    command = sshCmd + " \'curl http://169.254.169.254/latest/meta-data/local-ipv4 >> index.html\'"
    subprocess.run(command, shell=True)

    print('')
    print('Setting up custom home page on server (This may take a minute or two)')
    print('')

    waiter = ec2Client.get_waiter('instance_status_ok')
    waiter.wait()
    #time.sleep(120)
    #print(status)
    command = sshCmd + " sudo cp index.html /var/www/html/"
    subprocess.run(command, shell=True)

    print('Server home page available at:')
    print('http://' + public_ip)
    print('')
except Exception as error:
    print (error)
