import sys
import os
import socket
import hashlib
import copy
import time

size=999999
TimeoutValue=1
Packet_Size=1024

def Get_Arguments():    #Takes Configuration filename as a argument#
    if len(sys.argv) != 2:
        print("You must enter configuration file as a argumrnt")
        sys.exit()
    else:
        Config_File=sys.argv[1]
        return Config_File
    
def Parse_Config_File(Config_File, UserNames, ServerNames): # Find Username, Password, Server information in configuration file
    try:
        f=open(Config_File,'r')        
        Waiting_Password=0
        Username="none"
        for line in f:
            if Waiting_Password==1:
                if line[0:9]=="Password:":
                    Waiting_Password==0
                    Password_Info=line.split(' ')
                    Password=Password_Info[1]
                    Password=Password.rstrip()
                    if (Username=="none"):
                        print("Syntax Error: Unable to find Username")
                        sys.exit()
                    else:
                        UserNames[Username]=Password
                else:
                    print("Syntax Error: Unable to find password in configuration file")
                    sys.exit()
            if (line[0:6]=="Server"):
                Server_Info=line.split(' ')
                ServerName=Server_Info[1]
                ServerName=ServerName.rstrip()
                ServerAddress=Server_Info[2]
                ServerAddress=ServerAddress.rstrip()
                ServerNames[ServerName]=ServerAddress
            elif(line[0:9]=="Username:"):
                Waiting_Password=1
                Username_Info=line.split(' ')
                Username=Username_Info[1]
                Username=Username.rstrip()
        f.close()
        print("found "+str(len(UserNames))+" User")
        print("found "+str(len(ServerNames))+" Server")
        return UserNames, ServerNames
    except:
        print("Syntax Error: Unable to parse Configuration File")
        sys.exit()
    
def Get_FileName(Command):  # Get Filename from PUT/GET Command
    try:
        Command_Info=Command.split(' ')
        if len(Command_Info) != 2:
            print("Invalid Command!!!")
            return "Invalid"
        Filename=Command_Info[1]
        return Filename
    except:
        print("Invalid Command!!!")
        return "Invalid"

def Get_Extention(Filename):    # Find extension of file
    try:
        Filename_Info=Filename.split('.')
        if len(Filename_Info)!=2:
            print("Unable to find extention")
            return "Invalid"
        Extention=Filename_Info[1]
        return Extention
    except:
        print("Unable to find extention")
        return "Invalid"
    
def Get_Filesize(Filename): # Find file total size
    try:
        Filesize=os.path.getsize(Filename) 
    except:
        print("Unable to get Filesize")
        return "Invalid"
    return Filesize

def Get_Segregated_filesizes(FileSize): # Find files part size
    Even_Part=FileSize/4
    Even_Part=int(Even_Part)
    Part=Even_Part
    return Part

def Check_Command(Command): #Check GET/PUT command syntax
    Filename=Get_FileName(Command)
    if Filename=="Invalid":
        return "Bad", "Invalid", "Invalid", "Invalid", "Invalid"
    Extention=Get_Extention(Filename)
    if Extention == "Invalid":
        return "Bad","Invalid", "Invalid", "Invalid", "Invalid"
    Filesize=Get_Filesize(Filename)
    if Filesize=="Invalid":
        return "NOTFOUND", "Invalid", "Invalid", "Invalid", "Invalid"
    PartSize=Get_Segregated_filesizes(Filesize)
    return "Good", Filename, Extention, Filesize, PartSize 

def Get_Server_Info(SerName,Address):   # Find IP address and Port number of a server
    Address_info=Address.split(':')
    try:
        IP=Address_info[0]
        Port=Address_info[1]
    except:
        print("Unable to separate IP and Port number")
        return False, "Invalid", 0
    try:
        Port=int(Port)
    except:
        print("Port number is not integer (Check Configuration file)")
        return False, "Invalid", 0
    return True, IP, Port

def Send_Data_Packet(CLISoc, Filename, PartSizeFinal, PartSize, PartNumber):    # Send parts of file to server(Actual Data)
    h=open(Filename, 'rb')
    Multiple=PartNumber-1
    p=Multiple*PartSize 
    h.seek(p)
    Send_Data=h.read(PartSizeFinal)
    CLISoc.sendall(Send_Data)
    time.sleep(0.3)
    FinalFlag="####&&&&%%%%FINAL####&&&&%%%%".encode()
    CLISoc.send(FinalFlag)
    CLISoc.settimeout(TimeoutValue)
    try:
        DATA_ACK=CLISoc.recv(size)
    except:
        print("NO DATA_ACK "+Filename+"."+str(PartNumber))
        return "FAILED", CLISoc
    DATA_ACK=DATA_ACK.decode()
    REQUIRED_FIN_ACK="DATA|||"+Filename+"."+str(PartNumber)
    #print(DATA_ACK)
    if REQUIRED_FIN_ACK==DATA_ACK:
        #print("File successfully uploaded")
        return "SUCCESS", CLISoc
    else:
        print("WRONG FIN ACK")
        return "WRONG_FIN", CLISoc

def Send_Initial_Packet(FilePartName, PartSizeFinal, Username, Password, ServerAddr, ServerName):   # Send Initial Packet to server
    try:
        CLISoc=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        CLISoc.connect(ServerAddr)
    except:
        print("Timeout reached for "+str(ServerName)+" Server not available")
        return "CONN_PROB", CLISoc
    Initial_Packet="PUT|||"+Username+"|||"+Password+"|||"+FilePartName+"|||"+str(PartSizeFinal)
    Initial_Packet=Initial_Packet.encode()
    CLISoc.send(Initial_Packet)
    CLISoc.settimeout(TimeoutValue)
    try:
        ACK_PUT=CLISoc.recv(size)
    except:
        print("Timeout fot PUT Initial ACK")
        return "INI_ACK_TIMEOUT", CLISoc
    ACK_PUT=ACK_PUT.decode()
    #print("ACK_PUT: "+ACK_PUT)
    REQUIRED_ACK="ACK|||MATCH"
    if ACK_PUT==REQUIRED_ACK:
        return "ESTABLISHED", CLISoc
    elif ACK_PUT=="ACK|||NOTMATCH":
        return "PASS_INCORRECT", CLISoc
    elif ACK_PUT=="ACK|||NOTFOUND":
        return "USER_NOT_FOUND", CLISoc
    else:
        return "WRONG_ACK", CLISoc
    
def Send_Part(Filename, FileSize, PartSize, Username, Password, PartNumber, IP, Port, ServerName):  # Send Part to server
    ServerAddr=(IP,Port)
    if PartNumber ==4:
        PartSizeFinal=FileSize-(3*PartSize)
    else:
        PartSizeFinal=PartSize
    FilePartName=Filename+"."+str(PartNumber)
    
    Result, CLISoc=Send_Initial_Packet(FilePartName, PartSizeFinal, Username, Password, ServerAddr, ServerName)
    if Result=="ESTABLISHED":
        Result, CLISoc=Send_Data_Packet(CLISoc, Filename, PartSizeFinal, PartSize, PartNumber)
        CLISoc.close()
        if Result =="SUCCESS":
            return True
        else:
            return False
    elif Result=="PASS_INCORRECT":
        print("Invalid Password. Please try again.")
        CLISoc.close()
        return False
    
    elif Result=="USER_NOT_FOUND":
        print("User not found in server database: Invalid Username. Please try again."+ServerName)
        CLISoc.close()
        return False
        
    elif Result=="WRONG_ACK":
        print("WRONG ACK FORMAT: "+ServerName)
        CLISoc.close()
        return False
    
def Execute_PUT(Filename, Extention, FileSize, PartSize, UserNames, ServerNames, X):    # Handle PUT request
    
    for key in UserNames.keys():
        Username=key
        Password=UserNames[key]
    
    UploadCount=0
    for key in ServerNames.keys():
        ServerName=key
        ServerAddress=ServerNames[key]
        Result, IP, Port=Get_Server_Info(ServerName, ServerAddress)
        if Result==False:
            return False
        
        Leng=len(ServerName)
        PartNumber=int(ServerName[Leng-1])
        
        X_Invert=4-X
        PartNumber=PartNumber+X_Invert
        PartNumber=PartNumber%4
        if PartNumber==0:
            PartNumber=4
            
        Send_Part_Result=Send_Part(Filename, FileSize, PartSize, Username, Password, PartNumber, IP, Port, ServerName)
        if Send_Part_Result==True:
            UploadCount=UploadCount+1
        PartNumber=PartNumber+1
        PartNumber=PartNumber%4
        if PartNumber==0:
            PartNumber=4
        Send_Part_Backup_Result=Send_Part(Filename, FileSize, PartSize, Username, Password, PartNumber, IP, Port, ServerName)
        
        if Send_Part_Backup_Result==True:
            UploadCount=UploadCount+1
    if UploadCount==8:
        return True
    return False
        
def Get_X(Filename):    #Find mod value from file content
    hand=open(Filename,'rb')
    String=hand.read()
    m=hashlib.md5()
    m.update(String)
    hexData=m.hexdigest()
    integer=int(hexData,16)
    Value=integer%4
    hand.close()
    print("X is "+str(Value))
    return Value

def Process_List_Response(Response, Username, Password, IP, Port, File_Part_List, File_Part_Detail_Report, SerName):    # Process List Response come from Server
    #print(Response)
    try:
        Response_info=Response.split("|||")
        Response_info_new=[]
        for item in Response_info:
            Response_info_new.append(item.encode('UTF8'))
        Response_info=copy.copy(Response_info_new) 
        Response_info.pop(0)
        Auth=Response_info.pop(0)
        #PasswordRes=Response_info.pop(0)
        #Response_info.pop(0)
        #PortRes=Response_info.pop(0)
        #PortRes=int(PortRes)
        #print(Auth)
        if (Auth=="MATCH"):
            for item in Response_info:
                if SerName+"--"+item not in File_Part_Detail_Report: 
                    File_Part_Detail_Report.append(SerName+"--"+item)
            
            for item in Response_info:
                if item not in File_Part_List:
                    File_Part_List.append(item)
            return True,  File_Part_List, File_Part_Detail_Report
        elif (Auth=="NOMATCH"):
            print("Invalid Password. Please try again.")
            return False,  File_Part_List, File_Part_Detail_Report
        elif (Auth=="NOTFOUND"):
            print("Invalid Username. Please try again.")
            return False,  File_Part_List, File_Part_Detail_Report
        else:
            print("The response for list is in wrong format: "+SerName)
            print(Response)
            return False,  File_Part_List, File_Part_Detail_Report
    except:
        return False,  File_Part_List, File_Part_Detail_Report

def Send_List_Request(ServerNames, UserNames, File_Comp_Report, File_Part_Detail_Report):   # Send List Command Request to Server
    File_Part_List=[]
    
    for key in UserNames.keys():
        Username=key
        Password=UserNames[key]
        
    for key in ServerNames.keys():
        Connection=False
        SerName=key
        Address=ServerNames[key]
        Result, IP, Port=Get_Server_Info(SerName, Address)
        if Result==False:
            return False, File_Comp_Report, File_Part_Detail_Report
        CLISoc=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ServerAddr=(IP,Port)
        try:
            CLISoc.connect(ServerAddr)
            Connection=True
        except:
            print("Connection Timeout reached for :"+SerName+" Server unavailable")
            CLISoc.close()
            Connection=False
            #print("Unable to connect to the server :"+SerName)
            
        if Connection==True:
            Request_Data="LIST|||"+Username+"|||"+Password
            Request_Data=Request_Data.encode()
            CLISoc.send(Request_Data)
            CLISoc.settimeout(TimeoutValue)
            Data_Recevied=False
            try:
                Response=CLISoc.recv(size)
                Data_Recevied=True
                CLISoc.close()
            except:
                print("Connection Timeout reached for :"+SerName+" Server unavailable")
                CLISoc.close()
            if Data_Recevied==True:
                Response=Response.decode()
                Result,  File_Part_List, File_Part_Detail_Report=Process_List_Response(Response, Username, Password, IP, Port, File_Part_List, File_Part_Detail_Report, SerName)
                #if Result==False:
                    #print("Unable to process List Response")
                    #return False, File_Comp_Report, File_Part_Detail_Report
    Files_Names=[]
    for item in File_Part_List:
        l=len(item)
        l=l-2
        item=item[:l]
        if item not in Files_Names:
            Files_Names.append(item)
    
    for item in Files_Names:
        numb=0
        for item1 in File_Part_List:
            l=len(item1)
            l=l-2
            File=item1[:l]
            if File==item:
                numb=numb+1
        File_Comp_Report[item]=numb
    return True, File_Comp_Report, File_Part_Detail_Report

def Check_Get_Command(Command): # Check Syntax of Get Command
    Command_info=Command.split(" ")
    if len(Command_info)==2:
        Filename=Command_info[1]
        Extention=Get_Extention(Filename)
        if Extention == "Invalid":
            print("Bad Request")
            return False, "Invalid", "Invalid"
        return True, Filename, Extention
    else:
        return False, "Invalid", "Invalid"
    
def Request_Part_to_Server(IP, Port, ReqFilePartName, Username, Password, Rec_File_hand, SerName):  # Request part to server
    CLISoc=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    DestAddr=(IP,Port)
    CLISoc.connect(DestAddr)
    Part_Request="GET|||"+Username+"|||"+Password+"|||"+ReqFilePartName
    Part_Request=Part_Request.encode()
    CLISoc.send(Part_Request)
    CLISoc.settimeout(TimeoutValue)
    try:
        ACK_From_Server=CLISoc.recv(size)
    except:
        print("Unable to connect to "+SerName+" Server unavailable")
    ACK_From_Server=ACK_From_Server.decode()
    ACK_From_Server_Info=ACK_From_Server.split("|||")
    Type=ACK_From_Server_Info[0]
    User_Auth=ACK_From_Server_Info[1]
    File_Found=ACK_From_Server_Info[2]
    if Type=="ACK" :
        if User_Auth=="Match":
            if File_Found=="Found":
                #print("Final request sending")
                Final_Req="SENDFILE|||"+ReqFilePartName
                Final_Req=Final_Req.encode()
                CLISoc.send(Final_Req)
                FinalFlag="####&&&&%%%%FINAL####&&&&%%%%".encode()
                Flag=False
                while Flag==False:
                    CLISoc.settimeout(TimeoutValue)
                    try:
                        File_Data=CLISoc.recv(size)
                        if File_Data!=FinalFlag:
                            Rec_File_hand.write(File_Data)
                        else:
                            Flag=True
                    except:
                        print("Timeout reached")
                CLISoc.close()
                return True, Rec_File_hand
            else:
                print("File not found on "+SerName)
                CLISoc.close()
                return False, Rec_File_hand
        else:
            print("Invalid Username/Password. Please try again.")
            CLISoc.close()
            return False, Rec_File_hand
    else:
        print("Bad Ack From Server"+SerName)
        CLISoc.close()
        return False, Rec_File_hand
    
def Find_Server_For_Download(File_Part_Detail_Report, ReqFilePartName): #Find Server Name for download
    for item in File_Part_Detail_Report:
        Storage_info=item.split("--")
        FilePartName=Storage_info[1]
        if ReqFilePartName == FilePartName:
            SerName=Storage_info[0]
            return True, SerName
    return False, "Unknown"
    
def Choose_Optimal_Servers(File_Part_Detail_Report, Filename):	# chooses optimal server combinations to download a file
    File_Part_Detail=[]
    for item in File_Part_Detail_Report:
        Storage_info=item.split("--")
        FilePartName=Storage_info[1]
        length=len(FilePartName)
        FilenameInReport=FilePartName[:(length-2)]
        if FilenameInReport==Filename:
            File_Part_Detail.append(item)
    #print(File_Part_Detail)
    File_Part_Detail_SG1=[]
    File_Part_Detail_SG2=[]
    for item in File_Part_Detail:
        Storage_info=item.split("--")
        ServerName=Storage_info[0]
        if ServerName=="DFS1" or ServerName=="DFS3":
            File_Part_Detail_SG1.append(item)
        else:
            File_Part_Detail_SG2.append(item)
    #print(File_Part_Detail_SG1)
    #print(File_Part_Detail_SG2)
    if len(File_Part_Detail_SG1)==4:
        return File_Part_Detail_SG1
    elif len(File_Part_Detail_SG2)==4:
        return File_Part_Detail_SG2
    else:
        return File_Part_Detail_Report
    
def Get_Part_From_Servers(Part_Number, Filename, ServerNames, Username, Password, Rec_File_hand, File_Part_Detail_Report): # Download Part from Server
    ReqFilePartName=Filename+"."+str(Part_Number)
    File_Part_Detail_Report.sort()
    File_Part_Detail_Report_Optimal=Choose_Optimal_Servers(File_Part_Detail_Report, Filename)
    Result, SerName=Find_Server_For_Download(File_Part_Detail_Report_Optimal, ReqFilePartName)
    
    Server_Address=ServerNames[SerName]
    Result, IP, Port=Get_Server_Info(SerName, Server_Address)
    
    Result, Rec_File_hand=Request_Part_to_Server(IP, Port, ReqFilePartName, Username, Password, Rec_File_hand, SerName)
    
    if Result==False:
        print("Failed to download part: "+ReqFilePartName+" from "+SerName)
        Entry=SerName+"--"+ReqFilePartName
        File_Part_Detail_Report.remove(Entry)
        Result_ser, SerName=Find_Server_For_Download(File_Part_Detail_Report, ReqFilePartName)
        if Result_ser == True:
            Server_Address=ServerNames[SerName]
            Result, IP, Port=Get_Server_Info(SerName, Server_Address)
            Result2, Rec_File_hand=Request_Part_to_Server(IP, Port, ReqFilePartName, Username, Password, Rec_File_hand, SerName)
            if Result2==False:
                print("Failed to download part: "+ReqFilePartName+" from "+SerName)
                return False, Rec_File_hand
            else:
                print("Downloaded "+ReqFilePartName+" from "+SerName)
                return True, Rec_File_hand
        else:
            print("Failed to download part: "+ReqFilePartName+" from "+SerName)
            return False, Rec_File_hand
    else:
        print("Downloaded "+ReqFilePartName+" from "+SerName)
        return True, Rec_File_hand
        
def Handle_Get_Request(Filename, UserNames, ServerNames, File_Part_Detail_Report):  #Handles GET request
    for key in UserNames.keys():
        Username=key
        Password=UserNames[key]
    #X=Get_X(Filename)
    if not os.path.isdir("./Client"):
        os.mkdir('Client')
    if not os.path.isdir("./Client/"+Username):
        os.mkdir("./Client/"+Username)
    Rec_File_hand=open("./Client/"+Username+"/"+Filename,'wb')
    Part_Number=1
    while Part_Number < 5:
        Result, Rec_File_hand=Get_Part_From_Servers(Part_Number, Filename, ServerNames, Username, Password, Rec_File_hand, File_Part_Detail_Report)
        if Result==False:
            print("Unable to download part from all servers :"+Filename+"."+str(Part_Number))
            return False 
        Part_Number=Part_Number+1
    Rec_File_hand.close()
    return True

# main program starts
	
Config_File=Get_Arguments()
if (not (os.path.isfile(Config_File))):
    print("File not found")
    sys.exit()
UserNames={}
ServerNames={}
UserNames, ServerNames=Parse_Config_File(Config_File, UserNames, ServerNames)
if (len(UserNames)!=1):
    print("This Client only takes one user Please enter only one username and password in config file")
    sys.exit()


while True:
    Command= raw_input("Enter the command: (List/ GET <filename>/ PUT <filename>/ EXIT)")
    if Command[0:3]=="PUT":	# if the request is a PUT request
        Result, Filename, Extention, FileSize, PartSize=Check_Command(Command)
        if Result == "Good":
            X=Get_X(Filename)
            Success=Execute_PUT(Filename, Extention, FileSize, PartSize, UserNames, ServerNames, X)
            if Success==True:
                print("File uploaded to servers successfully")
                print("Total Data length: "+str(FileSize))
            else:
                print("Unable to upload file to servers")
        elif Result =="NOTFOUND":
            print("Error: File not found")
        else:
            print("Error: Bad Command")
    elif Command[0:3]=="GET":	# if the request is a GET request
        File_Comp_Report={}
        File_Part_Detail_Report=[]
        Result, File_Comp_Report, File_Part_Detail_Report=Send_List_Request(ServerNames, UserNames, File_Comp_Report, File_Part_Detail_Report)
        #print(File_Part_Detail_Report)
        if Result==False:
            print("Unable to find file in database")
        else:
            Result, Filename, Extention=Check_Get_Command(Command)
            if Result==True:
                if Filename in File_Comp_Report.keys():
                    if  File_Comp_Report[Filename]==4:  
                        #print(File_Part_Detail_Report)
                        Success=Handle_Get_Request(Filename, UserNames, ServerNames, File_Part_Detail_Report)
                        if Success==True:
                            print("File Download successful")
                        else:
                            print("File Download unsuccessful")
                    else:
                        print("File is incomplete")
                else:
                    print("File you have requested is not present in database")
            else:
                print("Bad Command syntax for GET command")    
                
    elif Command[0:4]=="LIST":	# if the request is a LIST request
        File_Comp_Report={}
        File_Part_Detail_Report=[]
        Result, File_Comp_Report, File_Part_Detail_Report=Send_List_Request(ServerNames, UserNames, File_Comp_Report, File_Part_Detail_Report)
        count=0
        for key in File_Comp_Report.keys():
            if File_Comp_Report[key]==4:
                print(key)
            else:
                print(key+" [incomplete]")
            if Result == False:
                print("Unable to get list from Servers")
            count=count+1
        if count==0:
            print("No data for this user on any server")
            
    elif Command[0:4]=="EXIT":
        print("Exiting Client ...")
        sys.exit()
    else:
        print("Error: BAD COMMAND")
