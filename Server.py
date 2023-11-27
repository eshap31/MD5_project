import hashlib
import os
import socket
import threading
from Protocol import protocol


class md5_server:
    def __init__(self, p_length, p):
        # communication
        self.host = '127.0.0.1'
        self.port = 59000
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # create server object
        self.server.bind((self.host, self.port))
        self.server.listen()  # activate listen
        self.clients = []  # list of clients

        # client
        self.max_clients = os.cpu_count()
        self.current_clients = 0  # keeps track of amount of clients
        self.threads = []
        self.clients = []  # list of clients

        # md5
        self.pass_length = p_length
        self.hashed_password = hashlib.md5(p.encode()).hexdigest()
        self.chunk_count = 9
        self.total_options = 10 ** self.pass_length
        self.client_chunk = self.total_options // self.chunk_count  # min amount of numbers per chunk
        self.client_chunk_list = []  # keeps track of how many numbers are in each chunk
        self.current_number = 0
        self.password_found = False
        self.i = 0

    @staticmethod
    def send_chunk_message(client, total_options, start):
        data_2 = str(total_options) + '$' + str(start)  # create data
        message_2 = protocol.create_message(data_2)  # create message
        client.send(message_2)  # send first message

    def handle_client(self, client, i, start):
        # send client appropriate chunk, hashed password
        total_options = self.client_chunk_list[i]  # chunk size
        start = str(start).zfill(self.pass_length)
        # send hashed password, and password length
        data_1 = self.hashed_password + '$' + str(self.pass_length)
        message_1 = protocol.create_message(data_1)
        client.send(message_1)
        # send total_options, and start
        md5_server.send_chunk_message(client, total_options, start)
        while not self.password_found:
            # wait for client to respond
            response = protocol.get_msg(client)
            # possible responses: didn't crack password, cracked the password
            if response[0] == 'found':  # if password was found by the client
                self.password_found = True
                print('password found')
                print(f'password is {response[1]}')
                break
            else:
                # check if there is a chunk available
                if self.i > len(self.client_chunk_list) - 1:
                    # no chunk available, send rejection message
                    rejection = protocol.create_message('not$available')
                    client.send(rejection)
                    break
                else:
                    # send client the next chunk
                    total_options = self.client_chunk_list[self.i]
                    start = str(self.current_number).zfill(self.pass_length)
                    md5_server.send_chunk_message(client, total_options, start)
                    self.current_number += self.client_chunk_list[self.i]
                    self.i += 1

    def start_loop(self):
        # split password options in to chunks
        if self.total_options % self.chunk_count == 0:
            self.client_chunk_list = [self.client_chunk for x in range(self.chunk_count)]
        else:
            self.client_chunk_list = [self.client_chunk for x in range(self.chunk_count - 1)]
            self.client_chunk_list.append(self.total_options - (self.chunk_count - 1) * self.client_chunk)

        # client connections, and threading
        while not self.password_found:
            print('server is running and listening...')
            client, address = self.server.accept()
            self.current_clients += 1
            print(f'connection is established with {str(address)}')
            if self.current_clients >= self.max_clients or self.i > len(self.client_chunk_list) - 1:
                # send rejection message to client
                rejection = protocol.create_message('not$available')
                client.send(rejection)
            else:
                thread = threading.Thread(target=self.handle_client, args=(client, self.i, self.current_number,))
                self.current_number += self.client_chunk_list[self.i]
                thread.start()
                self.threads.append(thread)
            self.i += 1

        print('finished')

        # close all client sockets
        for c in self.clients:
            c.close()

        for thread in self.threads:
            thread.join()


def main():
    pass_length = 7
    password = '9999999'
    my_server = md5_server(pass_length, password)
    my_server.start_loop()


if __name__ == '__main__':
    main()
