# coding: ISO-8859-1
"""
Ce programme permet de faire tourner un serveur de discussion instantanée.
"""


import multiprocessing
import socket
import queue
import sys
import os
import traceback
 
#------------------------------------------------------------------------------
#               GESTION DES CLIENTS
#------------------------------------------------------------------------------
def login(con,allConnexions):
    """
    Permet l'identification du client lors d'une connexion
    
    :param con: connexion du client
    :type con: socket
    :param allConnexions: ensemble des couples (socket,identifiant) des clients actuellement connectés
    :type allConnexions: queue
    :return: identifiant du client connecté
    :rtype: str
    """
    con.sendall("Veuillez entrer votre nom d'utilisateur : ".encode("utf-8"))
    try:
        ID=con.recv(1024)
        ID=ID.decode("utf-8")
        ID=ID[:-1] #retire le \n en fin du nom d'utilisateur
        print (ID)
        
        if(is_known("run/passwd.txt",ID)) :
            wrongPasswd=True
            while(wrongPasswd): 
                con.sendall("Veuillez entrer votre mot de passe : ".encode("utf-8")) 
                passwd=con.recv(1024)
                passwd=passwd.decode("utf-8") 
                if(check_passwd("run/passwd.txt",ID,passwd)) : 
                    wrongPasswd=False
                else:
                    con.sendall("Mot de passe incorrect\n".encode("utf-8")) 
        else:
            con.sendall("Veuillez saisir un mot de passe pour créer votre compte : ".encode("utf-8")) 
            passwd=con.recv(1024)
            passwd=passwd.decode("utf-8") 
            add_user("run/passwd.txt", ID, passwd) 
        
        allConnexions.append(con) 
        print(ID)
        con.sendall(("Vous êtes connecté en tant que : "+ID+"\n").encode("utf-8"))
        							
    except:
        con.sendall("Erreur d'authentification, la connexion n'a pas pu être correctement établie".encode("utf-8"))
        raise
        

    sendHistory(con,"run/history.txt",findLastMsg("run/history.txt",ID))
    return ID

#------------------------------------------------------------------------------
#               GESTION DES FICHIERS
#------------------------------------------------------------------------------
def is_known(fpassword, ID) :
    """
    Parcours le fichier fpassword pour vérifier si l'identifiant est déjà contenu
  
    :param fpassword: nom du fichier à parcourir
    :type fpassword: str
    :param ID
    :return: true / false
    :rtype: bool
    """
    res=False
    with open(fpassword,'r') as file:

        for i,l in enumerate(file):
            if l[:len(ID)]==ID: 
                res=True
    return res
  
def file_len(fname):
    """Parcours le fichier fname pour compter le nombre de lignes
    
    :param fname: nom du fichier à parcourir
    :type fname: str
    :return: nombre de lignes du fichier
    :rtype: int
    """
    i=-1
    try:
        with open(fname,'r') as file:
            for i, l in enumerate(file):
                pass
    except IOError:
        warn("Impossible de compter les lignes de "+fname+": fichier inaccessible")
        
    return i + 1

def rmFirstLines(fname,toRemove):
    """Supprime les 'toRemove' premières lignes du fichier fname
    
    :param fname: nom du fichier à parcourir
    :type fname: str
    :param toRemove: nombre de lignes à supprimer
    :type toRemove: int
    """
    try:
        tmpFile=open(fname+".tmp","w")
        with open(fname,'r') as file:
            for i, l in enumerate(file):
                if i>=toRemove:
                    tmpFile.write(l)
        tmpFile.close()
    
        os.remove(fname)
        os.rename(fname+".tmp",fname)
        
    except IOError:
        warn("Impossible de supprimer les premières lignes de "+fname+": fichier inaccessible")
    
def findLastMsg(fname,ID):
    """Parcours le fichier fname pour trouver le dernier message envoyé par ID
    
    :param fname: nom du fichier à parcourir
    :type fname: str    
    :param ID: nom de l'utilisateur dont on recherche le dernier message
    :type fname: str
    :return: Numéro de ligne du dernier message envoyé par l'utilisateur
    :rtype: int
    """
    last=0
    try:
        with open(fname,'r') as file:
            for i, l in enumerate(file):
                if l[:len(ID)]==ID:
                    last=i
    except IOError:
        warn("Impossible de trouver le dernier message dans "+fname+": fichier inaccessible")

    return last

def check_passwd(fpasswd, ID, passwd): 
	"""Parcours le fichier fpasswd et regarde si le passwd correspond au mot de passe de l'utilisateur ID
	
	:param fpasswd : nom du fichier à parcourir
	:type fpasswd : str
	:param ID : nom de l'utilisateur dont on check le mot de passe
	:type ID : str
	:return True si le mot de passe est le bon, false sinon
	rtype : bool
""" 
	res=False
	with open(fpasswd,'r') as file: 
		for i, l in enumerate(file):
			if l[:len(ID)]==ID: 
				if l[len(ID)+4:]==passwd : 
					res = True 
	return res

def add_user(fpasswd, ID, passwd): 
	"""Ajoute un utilisateur et son mot de passe dans le fichier fpasswd
	
	:param fpasswd : nom du fichier à parcourir
	:type fpasswd : str 
	:param ID : nom de l'utilisateur à ajouter 
	:type ID : str 
	:param passwd : mot de passe de l'utilisateur à ajouter 
	:type passwd : str 	
"""
	with open(fpasswd,'a') as file: 
		conc=ID+'    '+passwd
		file.write(conc)
		
#------------------------------------------------------------------------------
#               ENVOI DE MESSAGES
#------------------------------------------------------------------------------

def sendHistory(con, fname, startLine=0):
    """Envoie les lignes du fichier fname sur la socket con
    
    :param con: client à qui envoyer les lignes du fichier
    :type con: Socket
    :param fname: nom du fichier dont on envoie les lignes
    :type fname: str
    :param startLine: numéro de ligne à partir duquel on commence à lire le fichier
    :type startLine: int"""
    
    try:
        with open(fname,'r') as file:
            for i, l in enumerate(file):
                if i>=startLine:
                    con.sendall(l.encode("utf-8"))
    except:
        warn("Impossible d'écrire d'envoyer l'historique au client, celui-ci ne pourra pas voir les anciencs messages.")
    
    
def send_message(sender,senderID,message,allConnexions):
    """
    Retransmet le message reçu en provenance de sender à tous les autres clients connectés.
    
    :param sender: émetteur du message
    :type sender: socket
    :param senderID: identifiant de l'émetteur du message
    :type senderID: str
    :param message: message (encodé) envoyé par sender
    :type message: str
    :param allConnexions: ensemble des couples (socket,identifiant) des clients actuellement connectés
    :type allConnexions: queue
    """
    
    #Récupération de l'ensemble des clients connectés
    print("Récupération de la liste des clients")
                    
    #Retransmission du message à tous les autres clients
    toSend=senderID+": "+message.decode("utf-8")
    print("Retransmission du message")
    for k, connexion in enumerate(allConnexions):
        if connexion.getpeername() != sender.getpeername():
            print("émetteur:",sender.getpeername())
            print("destinataire:",connexion.getpeername())
            try:
                connexion.sendall(toSend.encode("utf-8"))
                print("données envoyées: ",toSend)
            except:
                print("erreur de connexion avec ",connexion.getpeername())
                print("fermeture de la connexion...")
                connexion.close()
                allConnexions.drop(k)
                print("connexion fermée")

    #Sauvegarde du message dans l'historique
    try:
        history=open("run/history.txt", 'a')
        history.write(toSend)
        history.close()
        toRemove=file_len("run/history.txt")-100
        if toRemove>0:
            rmFirstLines("run/history.txt",toRemove)
    except IOError:
        warn("Impossible d'écrire dans le fichier history.txt, l'historique ne sera pas mis à jour")
    
def handle_com(con, addr,allConnexions):
    """
    Permet au serveur de communiquer avec un client
    
    :param con: connexion du client
    :type con: socket
    :param addr: adresse du client sous forme d'un couple (adresse IP, numéro de port)
    :type addr: tuple (str,int)
    :param allConnexions: ensemble des couples (socket,identifiant) des clients actuellement connectés
    :type allConnexions: queue
    """
    try:
        print("Connexion ",con," à  l'adresse ", addr)
        conID=login(con,allConnexions)
        connected=True
        while connected:            
            #Attente de l'envoi d'un message par le client
            data = con.recv(1024)
            if data == "".encode("utf-8"):
                print("Client déconnecté")
                connected=False
                
                #Retire le client de la liste des clients connectés
                for k, connexion in enumerate(allConnexions):
                    if con.getpeername()==connexion.getpeername():
                        allConnexions.pop(k)
                print(con.getpeername()," retirée de la liste")                      
            else:
                print("Données reçues ", data)         
                send_message(con,conID,data,allConnexions)
                print("Données envoyées")
    except:
        print("Erreur inattendue:")
        k =  sys.exc_info()
        print(k[0],k[1])
        traceback.print_tb(k[2])
    finally:
        print("Fermeture de la connexion ",con.getpeername())
        con.close()
        print("Connexion fermée")
      
#------------------------------------------------------------------------------
#               MAIN
#------------------------------------------------------------------------------
if __name__ == "__main__":
    #Création si besoin des fichiers nécessaires au fonctionnement
    if not os.path.exists("run"):
        os.makedirs("run")
    open("run/passwd.txt", 'a').close()
    open("run/history.txt", 'a').close()
    try:
        mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        mySocket.bind(("",8888))
        mySocket.listen(1)
        print("En attente de connexion")
        allConnexions=multiprocessing.Manager().list()
        while True:
            con, addr = mySocket.accept()
            print("Client connecté")
            process = multiprocessing.Process(target=handle_com, args=(con, addr, allConnexions))
            process.daemon = True
            process.start()
            print("Processus ", process)

    except KeyboardInterrupt:
        print("Interruption clavier")
    finally:
        print("Fermeture des processus:")
        for process in multiprocessing.active_children():
            print("Fermeture du processus ", process)
            process.terminate()
            process.join()            
        mySocket.close()
    print("FIN") 
