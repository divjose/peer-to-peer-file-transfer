from xmlrpclib import ServerProxy , Fault
from Tkinter import *
from ttk import *
import socket
import thread
import threading
from tkFileDialog import askopenfilename
import tkFileDialog
import os
from urlparse import urlparse
from random import choice
from string import lowercase
import ntpath
import time

MAX_HISTORY_LENGTH = 6

UNHANDLED = 100
ACCESS_DENIED = 200

def randomString(length):
    chars=[]
    letters = lowercase[:26]
    while length > 0:
        length -=1
        chars.append(choice(letters))
    return ''.join(chars)

class UnhandledQuery(Fault):
  def __init__(self, message="Couldn't handle the query"):
    Fault.__init__(self, UNHANDLED, message)
  	
class AccessDenied(Fault):
  def __init__(self, message="Access denied"):
    Fault.__init__(self, ACCESS_DENIED, message)


class peerToPeer(Frame):
  
  def __init__(self, root):
    Frame.__init__(self, root)
    self.root = root
    self.GUI()
    self.serverSocket = None
    self.serverStatus = 0
    self.buffsize = 1024
    self.allClients = {}
    self.counter = 0
  
  def GUI(self):
    self.root.title("A-N-D-FileSharingSystem")
    ScreenSizeX = self.root.winfo_screenwidth()
    ScreenSizeY = self.root.winfo_screenheight()
    self.FrameSizeX  = 695
    self.FrameSizeY  = 685
    FramePosX   = (ScreenSizeX - self.FrameSizeX)/2
    FramePosY   = (ScreenSizeY - self.FrameSizeY)/2
    self.root.geometry("%sx%s+%s+%s" % (self.FrameSizeX,self.FrameSizeY,FramePosX,FramePosY))
    self.root.resizable(width=True, height=True)
    
    padX = 10
    padY = 10
    s = Style()
    s.configure('My.TFrame')
    parentFrame = Frame(self.root, style='My.TFrame')
    parentFrame.grid(padx=padX, pady=padY, stick=E+W+N+S)
    
    ipGroup = Frame(parentFrame)
    serverLabel = Label(ipGroup, text="IP Address: ", background = "dark green",font = "Helvetica 16 bold italic")
    serverLabel1=Label(ipGroup, text="Port Number: ", background = "dark green",font = "Helvetica 16 bold italic")
    serverSetButton = Button(ipGroup, text="Set Server", width=10, command=self.setServer)
    addClientLabel = Label(ipGroup, text="Peer IP Address: " ,background = "dark green", font = "Helvetica 16 bold italic")
    clientLabel2=Label(ipGroup, text="Peer Port Number: " , background = "dark green", font = "Helvetica 16 bold italic")
    clientSetButton = Button(ipGroup, text="Add Peer", width=10, command=self.setClient)
    self.nameVar = StringVar()
    self.nameVar.set("Server")
    self.serverIPVar = StringVar()
    self.serverIPVar.set(socket.gethostbyname(socket.gethostname()))
    serverIPField = Entry(ipGroup, width=15, textvariable=self.serverIPVar)
    self.serverPortVar = StringVar()
    self.serverPortVar.set(" ")
    serverPortField = Entry(ipGroup, width=5, textvariable=self.serverPortVar)
    self.clientIPVar = StringVar()
    self.clientIPVar.set(" ")
    clientIPField = Entry(ipGroup, width=15, textvariable=self.clientIPVar)
    self.clientPortVar = StringVar()
    self.clientPortVar.set(" ")
    clientPortField = Entry(ipGroup, width=5, textvariable=self.clientPortVar)
    blankValue = Label(ipGroup, text=" ")
    serverLabel.grid(row=0, column=0, sticky=W+N+S)
    serverIPField.grid(row=0, column=1, sticky=W+N+S)
    serverLabel1.grid(row=0, column=2, padx=10, sticky=W+N+S)
    serverPortField.grid(row=0, column=3, sticky=W+N+S)
    serverSetButton.grid(row=0, column=4, padx=10, sticky=W+N+S)
    blankValue.grid(row=1, column=0)
    addClientLabel.grid(row=2, column=0, sticky=W+N+S)
    clientIPField.grid(row=2, column=1, sticky=W+N+S)
    clientLabel2.grid(row=2, column=2, padx=10, sticky=W+N+S)
    clientPortField.grid(row=2, column=3, sticky=W+N+S)
    clientSetButton.grid(row=2, column=4, padx=10, sticky=W+N+S)
    
    readChatGroup = Frame(parentFrame)
    
    self.friends = Listbox(readChatGroup, bg="white", width=70)
    self.friends.grid(padx=20, row=0, column=0, pady=10)
    self.receivedChats = Listbox(readChatGroup, bg="white", width=70)
    self.receivedChats.grid(padx=20, row=1, column=0,pady =10)

    browseButton = Button(readChatGroup, text="Browse", width=10, command=self.browseFiles)
    browseButton.grid(row=2, column=0, padx=5)
    DownloadButton = Button(readChatGroup, text="Download", width=10, command=self.downloadFiles)
    DownloadButton.grid(row=3, column=0, padx=5)
    self.browseVar = StringVar()
 
    self.statusLabel = Label(parentFrame)
    
    ipGroup.grid(row=0, column=0)
    readChatGroup.grid(row=1, column=0)
    
    self.statusLabel.grid(row=2, column=0)
    
    
  def setServer(self):
    hostAddr = (self.serverIPVar.get(), int(self.serverPortVar.get()))
    fileHostAddr = (self.serverIPVar.get(), 9000)
    try:
        self.hostSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.hostSocket.bind(hostAddr)
        self.hostSocket.listen(5)

        self.fileHostSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.fileHostSocket.bind(fileHostAddr)
        self.fileHostSocket.listen(5)
        self.statusLabel.config(text=("Server connected %s:%s" % hostAddr))
        thread.start_new_thread(self.listenPeers,())
        thread.start_new_thread(self.listenFilePeers,())
                
        self.serverStatus = 1
        self.name = self.nameVar.get().replace(' ', '')
        if self.name == '':
            self.name = "%s:%s" % hostAddr
    except:
        self.statusLabel.config(text="Error setting up server")
    
  def listenPeers(self):
    while True:
      peerSocket, peerAddr = self.hostSocket.accept()
      self.statusLabel.config(text=("Peer connected from %s:%s" % peerAddr))
      self.addClient(peerSocket, peerAddr)
      thread.start_new_thread(self.receivePath, (peerSocket, peerAddr))  
    self.hostSocket.close()

  def fetch(self, query, secret):
    if sert!= self.secret: raise AccessDenied
    result = self.query(query)
    f = open(join(self, query), 'wb')
    f.write(result)
    f.close()

  def handle(self, query):
    dir = self.dirname
    name = join(dir, query)
    if not isfile(name): raise UnhandledQuery
    if not inside(dir, name): raise AccessDenied
    return open(name).read()

  def listenFilePeers(self):
    while True:
      peerSocket, peerAddr = self.fileHostSocket.accept()
      self.statusLabel.config(text=("File peer connected from %s:%s" % peerAddr))
      t = threading.Thread(target = self.retrieveFile, args=("retrThread" , peerSocket))
      t.start()
    self.fileHostSocket.close()

    

  def setClient(self):
    peerAddr = (self.clientIPVar.get().replace(' ', ''), int(self.clientPortVar.get().replace(' ', '')))
    try:
        peerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peerSocket.connect(peerAddr)
    
        self.statusLabel.config(text=("Connected to %s:%s" % peerAddr))
        self.addClient(peerSocket, peerAddr)
        thread.start_new_thread(self.receivePath, (peerSocket, peerAddr))       
    except:
        self.statusLabel.config(text="Error connecting to peer")
        

  def hello(self, other):
    self.known.add(other)
    return 0


  def receivePath(self, peerSocket, peerAddr):
    while 1:
      try:
        path = peerSocket.recv(self.buffsize)
        
        if not path:
            break
        self.displayPath("%s:%s" % peerAddr, path)
      except:
          break
    self.removePeer(peerSocket)
    peerSocket.close()
    self.statusLabel.config(text="Error connecting to peer")


  def displayPath(self, client, msg):
    self.receivedChats.insert("end",client+": "+msg+"\n")
    

  def addClient(self, peerSocket, peerAddr):
    self.allClients[peerSocket]=self.counter
    self.counter += 1
    self.friends.insert(self.counter,"%s:%s" % peerAddr)

  def broadcast(self, query, history):
        for other in self.known.copy():
            if other in history: continue
            try:
                s = ServerProxy(other)
                return s.query(query, history)

            except Fault, f:
                if f.faultCode == UNHANDLED: pass
                else: self.known.remove(other)
            except:
                self.known.remove(other)
        raise UnhandledQuery

  def browseFiles(self):
    filePath = tkFileDialog.askopenfilename()    
    if filePath == '':
        return
    self.displayPath("me", filePath)
    for peer in self.allClients.keys():
      peer.send(filePath)


  def downloadFiles(self):
      selections = self.receivedChats.curselection()
      if len(selections)==1:
         selection = self.receivedChats.get(selections[0])
         name=selection.split(' ',1)
         filename=name[1].strip()
         addr=name[0].strip()
      self.downloadFile(addr,filename)


  def downloadFile(self,host,filename):
    hostport=host.split(':')
    peer=hostport[0]
    s=socket.socket()
    try:      
      s.connect((peer,9000))
      t=time.time()
      s.send(filename)
      data = s.recv(1024)
      filesize = long(data[6:])
      s.send('OK')
      filePathSplit = filename.split('/')
      f= open(os.path.join('/Users/dynajose/Desktop/P2P-FileDownload', filePathSplit[len(filePathSplit)-1]), 'wb')
      data = s.recv(1024)
      rcvdData = len(data)
      f.write(data)
      while rcvdData < filesize:
          data = s.recv(1024)
          rcvdData += len(data)
          f.write(data)
      downloadTime=(time.time()-t)
      self.statusLabel.config(text=("Download completed in %s seconds" % downloadTime))
    except:
      self.statusLabel.config(text="File cannot be downloaded")
    s.close()
    

  def retrieveFile(self, name, socket):
      fName = socket.recv(1024)
      filename = ntpath.basename(fName)     
      sub_dir = ''
      directoryPath = fName.split('/')
      pathLen= len(directoryPath)
      size = 0
      while size < pathLen - 1:
             sub_dir +=  directoryPath[size] + '/'
             size = size+1                              
      filefoundBit = 0

      filepath = os.path.join(sub_dir, filename)
      if os.path.isfile(filepath):
            filefoundBit = 1
            fileSize = os.path.getsize(filepath)
               
      if filefoundBit:
          socket.send("EXISTS " + repr(fileSize))
          userResponse = socket.recv(1024)
          if userResponse[:2] == 'OK': 
              with open(filepath, "rb") as f:
                  bytesToSend = f.read()
                  socket.send(bytesToSend)
                  while bytesToSend != "":
                      bytesToSend = f.read()
                      socket.send(bytesToSend)        
      else:
          socket.send("ERR")
      self.statusLabel.config(text="File sent successfully")
      socket.close()
 
  def removePeer(self, peerSocket):
      self.friends.delete(self.allClients[peerSocket])
      del self.allClients[peerSocket]


def main():  
  root = Tk()
  app = peerToPeer(root)
  root.mainloop()  

if __name__ == '__main__':
  main()
