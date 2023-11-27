class protocol:
    LENGTH_FIELD_SIZE = 4

    @staticmethod
    def create_message(data):
        length = str(len(str(data)))
        zfill_length = length.zfill(protocol.LENGTH_FIELD_SIZE)
        message = zfill_length + str(data)
        return message.encode()

    @staticmethod
    def get_msg(my_client):
        len_word = my_client.recv(protocol.LENGTH_FIELD_SIZE).decode()
        message = my_client.recv(int(len_word)).decode()
        return message.split('$')
