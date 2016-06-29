import sys
import os
import socket
import threading
import time

PacketSize=1024
TimeoutValue=1
size=999

def Get_Parameters():   # Get passed arguments 
    if len(sys.argv)!=3:
        print("ERROR: Two Arguments Required: 1.base directory(/DEF#) 2.port number ")
        sys.exit()
    else:
        Def_Location=sys.argv[1]
        Port_Number=sys.argv[2]
        try:
            Port_Number=int(Port_Number)
        except:
            print("Port number must be a integer number")
            sys.exit()
        if Port_Number > 65525 or Port_Number < 1024:
            print("Port number must be a number from 1024 to 65535")
            sys.exit()
    return Def_Location, Port_Number

def Create_Listening_Socket(Port_Number):   #Create Server Socket
    MainSoc=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    address=('127.0.0.1',Port_Number)
    MainSoc.bind(address)
    MainSoc.listen(5)
    return MainSoc

def Parse_Config(Config_Filename):  # Parse Configuration file
    f=open(Config_Filename,'rb')
    for line in f:
        User_Info=line.split(" ")
        if len(User_Info)!= 2:
            print("Wrong syntax in dfs.conf filr")
            sys.exit()
        else:
            UserName=User_Info[0]
            UserName=UserName.rstrip()
            Password=User_Info[1]
            Password=Password.rstrip()
        UserNames[UserName]=Password
    return UserNames    

def Handle_Request(CLISoc, CLIAddr, UserNames, Req, Def_Location, Port_Number): 	# handle requests 
    Req_Info=Req.split("|||")
    Type=Req_Info[0]
    if Type=="PUT":
        Username=Req_Info[1]
        Password=Req_Info[2]
        if Username in UserNames: 
            if (UserNames[Username]==Password):
                print("Password match")
                FilePartName=Req_Info[3]
                PartSize=Req_Info[4]
                Ack_Data="ACK|||MATCH".encode()
                CLISoc.send(Ack_Data)
                #print("zal na bho")
                try:
                    if not os.path.isdir(Def_Location+"/"+Username):
                        os.mkdir(Def_Location+"/"+Username)
                except:
                    print("Error Occured: Making dir for user")
                h=open(Def_Location+"/"+Username+"/."+FilePartName, 'wb')
                Flag=False
                ReqFinFlag=("####&&&&%%%%FINAL####&&&&%%%%".encode())
                while Flag==False:
                    CLISoc.settimeout(TimeoutValue)
                    try:
                        Write_Data=CLISoc.recv(size)
                        if Write_Data!=ReqFinFlag:
                            h.write(Write_Data)
                        else:
                            h.close()
                            Flag=True
                    except:
                        print("Not received any data from Client closing connection")
                FinAck="DATA|||"+FilePartName
                FinAck=FinAck.encode()
                CLISoc.send(FinAck)
                CLISoc.close()
            else:
                print("Wrong Password for "+Username)
                Ack_Data="ACK|||NOTMATCH".encode()
                CLISoc.send(Ack_Data)
                CLISoc.close()
        else:
            print("User Not Found:"+Username)
            Ack_Data="ACK|||NOTFOUND".encode()
            CLISoc.send(Ack_Data)
            CLISoc.close()
    elif Type=="LIST":
        Username=Req_Info[1]
        Password=Req_Info[2]
        if Username in UserNames:
            if (UserNames[Username]==Password):
                print("Password match for "+Username)
                if not os.path.isdir(Def_Location+"/"+Username):
                    print("no data available for this Username")
                    ListResponse="LIST|||MATCH"
                    ListResponse=ListResponse.encode()
                    CLISoc.send(ListResponse)
                    CLISoc.close()
                else:
                    List_Files=os.listdir(Def_Location+"/"+Username)
                    if len(List_Files)==0:
                        print("The folder is empty")
                        ListResponse="LIST|||MATCH"
                        ListResponse=ListResponse.encode()
                        CLISoc.send(ListResponse)
                        CLISoc.close()
                    else:
                        FileListStr=""
                        for filename in List_Files:    
                            filename=filename[1:]
                            FileListStr=FileListStr+"|||"+filename
                        ListResponse="LIST|||MATCH"+FileListStr
                        ListResponse=ListResponse.encode()
                        CLISoc.send(ListResponse)
                        CLISoc.close()
            else:
                print("Wrong password for : "+Username)
                ListResponse="LIST|||NOMATCH"
                ListResponse=ListResponse.encode()
                CLISoc.send(ListResponse)
                CLISoc.close()
                
        else:
            print("Username not found")
            ListResponse="LIST|||NOTFOUND"
            ListResponse=ListResponse.encode()
            CLISoc.send(ListResponse)
            CLISoc.close()
            
    elif Type=="GET":
        Username=Req_Info[1]
        Password=Req_Info[2]
        if UserNames[Username]==Password:
            File_Part_Name=Req_Info[3]
            if os.path.isfile(Def_Location+"/"+Username+"/."+File_Part_Name):
                print("Password Match For GET and file found on server :"+File_Part_Name)
                Pack="ACK|||Match|||Found".encode()
                CLISoc.send(Pack)
                Final_Req=CLISoc.recv(size)
                Final_Req=Final_Req.decode()
                #print(Final_Req)
                if (Final_Req=="SENDFILE|||"+File_Part_Name):
                    #print("Final Request matched")
                    h=open(Def_Location+"/"+Username+"/."+File_Part_Name, 'rb')
                    FileData=h.read()
                    CLISoc.sendall(FileData)
                    FinalFlag=("####&&&&%%%%FINAL####&&&&%%%%").encode()
                    #print("Sending Final Flag")
                    time.sleep(0.1)
                    CLISoc.send(FinalFlag)
                    CLISoc.close()
                    l=len(FileData)
                    print("Data length: "+str(l)+" "+File_Part_Name)
                    h.close()
                    print("File send to client : Filename: "+File_Part_Name)
                else:
                    print("Wrong Final Request from server")
            else:
                print("Password Match For GET but File requested not found on server :"+File_Part_Name )
                PAck="ACK|||Match|||Notfound".encode()
                CLISoc.send(PAck)
        else:
            print("Password not Match For GET")
            PAck="ACK|||Unmatch".encode()
            CLISoc.send(PAck)
    
    
# Main Program Starts
Def_Location, Port_Number = Get_Parameters()
print(Def_Location)
print(Port_Number)
if Def_Location[:1]!=".":
    Def_Location="."+Def_Location
if os.path.isdir(Def_Location):	#Find directory for server if not present then create new one
    print("Default Directory found")
else:
    print("Default Directory not found" )
    os.mkdir(Def_Location)
MainSoc=Create_Listening_Socket(Port_Number)	#Create a listening main socket

if not (os.path.isfile("dfs.conf")):	# Check if dfs.cfg file is present or not
    print("dfs.conf not found")
    sys.exit()
UserNames={}
UserNames=Parse_Config("dfs.conf")
print(UserNames)
while True:
    CLISoc, CLIAddr=MainSoc.accept()
    Req=CLISoc.recv(size)
    threading.Thread(target=Handle_Request(CLISoc, CLIAddr, UserNames, Req, Def_Location, Port_Number))	# Create a thread for each request
    #print(Data)
    #CLISoc.close()
print("END")