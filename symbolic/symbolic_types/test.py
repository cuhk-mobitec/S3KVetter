import binascii
import base64
sig_pad='-rRNSU9o80WdyH3nvUYiFNOYdA1tPEJo4Jp_eE1tqeY='

base64.urlsafe_b64decode(sig_pad)

val = b'-rRNSU9o80WdyH3nvUYiFNOYdA1tPEJo4Jp_eE1tqeY='
binascii.a2b_base64(val)

