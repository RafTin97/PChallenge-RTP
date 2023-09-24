import os
import bottle
import base64
import traceback

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from binascii import hexlify
from cgi import escape


page = '''
<html>
<head><title>Welcome</title></head>
<body>
  <p><h2>Welcome, %s!</h2></p>
  <p><h3>You have %s tickets left</h3></p>
  <p>%s</p>
</body>
</html>
'''

key = os.urandom(32)
iv = os.urandom(16)
cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())


def get_ticket(username, email, amount):
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder() 
    message = padder.update("%s&%s&%d" % (username, email, amount)) + padder.finalize()
    ct = encryptor.update(message) + encryptor.finalize()
    return base64.b64encode(ct)

@bottle.route('/')
def default():
    decryptor = cipher.decryptor()
    unpadder = padding.PKCS7(128).unpadder()
    try:
        ticket = bottle.request.get_cookie('ticket')
        if ticket:
            message = decryptor.update(base64.b64decode(ticket)) + decryptor.finalize()
            username, email, amount = (unpadder.update(message) + unpadder.finalize()).split('&')
            return page % (escape(username), escape(amount),
                'I cannot lead you towards glorious times' if amount == '1' else 
                'Baaam! You are the Woodpecker No.1!')
        else:
            return '<html><body><p><a href=/ticket>Get a free ticket, but only one!</a></p></body><html>\n'
    except Exception, e:
        print traceback.format_exc()
        raise bottle.HTTPError(status=400, body=e.message)

@bottle.post('/ticket')
def ticket():
    username = bottle.request.forms.get('username')
    email = bottle.request.forms.get('email')
    if username and email:
        ticket = get_ticket(username, email, 1)
        bottle.response.set_cookie('ticket', ticket)
        return '<html><body><p>So you said you are ready to ascend a mountain of heavy light?</p></body></html>\n'
    raise bottle.HTTPError(status=400, body='Post me your username and email')

bottle.run(host='localhost', port=8080)
