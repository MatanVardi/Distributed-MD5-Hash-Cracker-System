class Protocol:
    def __init__(self):
        self.IP = "0.0.0.0"
        self.PORT = 5555
        
    def create_msg(self,data):
        length = str(len(data))
        zfill_length = length.zfill(2)
        message = zfill_length + data
        return message     
    
    def get_msg(self,my_socket):

        try:
            length  = my_socket.recv(2).decode() 
            length = int(length)
            message = my_socket.recv(int(length)).decode() 
        except:
            message = "Error message from other side"
            return False, message
    
        return True, message