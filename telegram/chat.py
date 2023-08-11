# importing all required libraries
from telethon import TelegramClient, sync, events


# get your api_id, api_hash, token
# from telegram as described above
api_id = '14933452'
api_hash = '75532d51426b8e8588a440dbb64ee4a1'
token = '6031866012:AAHqAix7aWBLLzk6NFQyHJhsttpeMf55Sbc'
message = "Working..."

# your phone number
phone = '59898421844'

def createClient():
    # connecting and building the session
    print("Conectando el cliente de Chat")
    client = TelegramClient('session_2', api_id, api_hash)
    client.connect()
    return client


# contacts = client.invoke(GetContactsRequest(""))

# file = client.upload_file('song.ogg')
# client.send_file(chat, file)                   # sends as song
# client.send_file(chat, file, voice_note=True)

def mandarMensaje(client, telegram_mensaje, file):
    # in case of script ran first time it will
    # ask either to input token or otp sent to
    # number or sent or your telegram id
    if not client.is_user_authorized():
        client.send_code_request(phone)

        # signing in the client
        codigo = input('Enter the code: ')
        client.sign_in(phone, codigo)

    try:
        # receiver user_id and access_hash, use
        # my user_id and access_hash for reference
        # receiver = InputPeerUser('user_id', 'user_hash')

        destination_user_username = 'calesi_2023_bot'
        receiver = client.get_entity(destination_user_username)
        client.send_message(entity=receiver, message=telegram_mensaje, parse_mode='Markdown')
        if file:
            client.send_file(entity=receiver, file=file, caption=telegram_mensaje)

        # sending message using telegram client
        # client.send_message(receiver, message, parse_mode='Markdown')
    except Exception as e:

        # there may be many error coming in while like peer
        # error, wrong access_hash, flood_error, etc
        print(e);


def disconnect(client):
    # disconnecting the telegram session
    client.disconnect()


#file_path = '13-43-12.jpg'
#mandarMensaje("hola la la ", file_path)
#disconnect()
