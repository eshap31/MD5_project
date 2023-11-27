import hashlib
import multiprocessing
import os
import socket
from Protocol import protocol


class client:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.total_processes = os.cpu_count()
        self.process_chunk = None
        self.pass_length = None
        self.hashed_password = None
        self.processes = []
        self.password_found = multiprocessing.Value('i', 0)  # Create a shared int variable between processes

    @staticmethod
    def create_hash(guess):
        hashed_guess = hashlib.md5(guess.encode()).hexdigest()
        return hashed_guess

    @staticmethod
    def guesser(total_options, start, password_found, pass_length, hashed_password):
        for i in range(total_options):
            if password_found.value != 0:  # if password was found, exit function
                print('exiting function')
                break

            current_guess = str(start + i).zfill(pass_length)
            if client.create_hash(current_guess) == hashed_password:
                print(current_guess)
                password_found.value = int(current_guess)  # Set the value to the correct password
                break

    def start_loop(self):
        self.client.connect(("127.0.0.1", 59000))
        # get hashed password and length from server
        self.hashed_password, self.pass_length = protocol.get_msg(self.client)
        if self.hashed_password == 'not' and self.pass_length == 'available':
            print('rejected')
            return
        self.hashed_password = self.hashed_password
        self.pass_length = int(self.pass_length)
        while True:
            print('in while')
            total_options, start = protocol.get_msg(self.client)
            if total_options == 'not' and start == 'available':
                print('no more chunks')
                return
            total_options = int(total_options)
            start = int(start)
            print(f'START {start}')
            self.process_chunk = total_options // self.total_processes
            print('starting decryption...')
            # split into chunks according to amount of processors
            if total_options % self.total_processes == 0:
                process_chunk_list = [self.process_chunk for x in range(self.total_processes)]
                print(f'Process load split: {process_chunk_list}')

            else:
                process_chunk_list = [self.process_chunk for x in range(self.total_processes - 1)]
                process_chunk_list.append(total_options - (self.total_processes - 1) * self.process_chunk)
                print(f'Process load split: {process_chunk_list}')

            # start multi-processing
            current_number = start
            for i, process_load in enumerate(
                    process_chunk_list):  # put the index and value of each value in list into i and self.process_chunk accordingly
                process = multiprocessing.Process(target=self.guesser,
                                                  args=(process_load, current_number, self.password_found, self.pass_length,
                                                        self.hashed_password))
                self.processes.append(process)
                process.start()
                current_number += process_load

            # Wait for processes to finish
            for process in self.processes:
                process.join()

            if self.password_found.value != 0:  # password was found
                print(f'\r\nPASSWORD IS {self.password_found.value}\r\n')
                # send password to server
                data = 'found$' + str(self.password_found.value)
                self.client.send(protocol.create_message(data))
                break
            else:
                print('not found')
                data = 'not$found'
                self.client.send(protocol.create_message(data))


def main():
    print('main')
    my_client = client()
    my_client.start_loop()


if __name__ == '__main__':
    main()
