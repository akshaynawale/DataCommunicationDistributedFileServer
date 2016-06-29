###################### AUTHOR ##########################################################
Name: Akshay Satyendra Navale
Occupation: ITP Student at University of Colorado, Boulder.USA.
Contact Details: akna8887@colorado.edu
Phone Number: 720-345-4053
#########################################################################################

Welcome!!! 
This is a README file for dfc.py  and dfs.py program.
The python code is written in python version 2.7.

############### Required configurations files ###########################################

$$$ for Distributed File Server	$$$
We are using a dfs.conf file that must be present to run this program. This file contain
the Username and associated passwords lists. DFS takes the username and password from 
this file.

$$$ for Distributed File Client	$$$
We are using a dfc.conf file that contains the server names , IP and ports addresses. 
The client will connect to these Servers. Also a User`s username and password are saved 
in this file. This file must contain only one username and password pair. And they must 
be present in the serverside config file. 

################## Required Arguments ######################################################
dfs.py takes two arguments 
1. folder name in which the all files for this server will be saved.
2. portnumber on which the server will run.

dfc.py takes one argument
1. config file name from which it will load the configuration.
[This file must be present in the same directory in which the python file is running]

################## File storing pattern on client and server ##################################
On server:
Server will create a root folder passed to it as a argument and create one folder for each user 
and stores their respective files to that folder.

On client:
Client will create a folder with name "Client" and for each user it will create  a folder with 
its names and will store all downloaded files in that folder.

############### Operation Method ##############################################################
The client and server supports three main operations:
1. LIST:
this command will list all files present for the perticular user and their status (complete/
incomplete)

2. GET <filename>
This command will download the file from server to the client

3. PUT <filename>
This file will upload the file from client and store it on the server.

################### Traffic optimization ##########################################################
The client intelligently requests only those servers which and donloads only 4 parts of the 
file which are essential for downloading the file.
 
########## Time-out functionality###################################################################
If the server is down then Cline will timeout in one secound.

########## Username/ Password missmatch ############################################################
When client makes a request it will send its username and password. if those does not match with the 
username and password stored on the server then server will send the ACK message with "NOTFOUND" for 
invalid username and "NOTMATCH" for invalid password.

################################## MultiThreading ################################################
DFServer has a functionality to handle multiple requests at a same time. It can also handle multile 
clinets at sametime.

###############################################################################################################
Thank you for reading!!!  

 