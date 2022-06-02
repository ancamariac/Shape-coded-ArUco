import cv2
import numpy as np

def decode_message( image ):
    image_lsb_text = ''
    lsb_char_binary = ''
    end_of_message_string = '@#$%^&'

    for row in image:
        for pixel in row:
            b_steg = get_binary(pixel[0])
            g_steg = get_binary(pixel[1])
            r_steg = get_binary(pixel[2])
            
            if( len(lsb_char_binary) < 8 ): 
                lsb_char_binary += b_steg[-2]
                lsb_char_binary += b_steg[-1]
            else: 
                image_lsb_text += chr(int(lsb_char_binary, 2))
                lsb_char_binary = b_steg[-2]
                lsb_char_binary += b_steg[-1]

            if( len(lsb_char_binary) < 8 ): 
                lsb_char_binary += g_steg[-2]
                lsb_char_binary += g_steg[-1]
            else: 
                image_lsb_text += chr(int(lsb_char_binary, 2))
                lsb_char_binary = g_steg[-2]
                lsb_char_binary += g_steg[-1]

            if( len(lsb_char_binary) < 8 ): 
                lsb_char_binary += r_steg[-2]
                lsb_char_binary += r_steg[-1]
            else: 
                image_lsb_text += chr(int(lsb_char_binary, 2))
                lsb_char_binary = r_steg[-2]
                lsb_char_binary += r_steg[-1]
            
            if( (len(image_lsb_text) > 6) and ( image_lsb_text[-6:] == end_of_message_string )):
                return image_lsb_text[:-6]
    return ''

def get_binary(message):
    if( type(message) == str ):
        binary_message = ( char.split('b')[1] for char in map(bin,bytearray(message,'utf8')) )
        binary_message_8b = []
        for binary_char in binary_message:
            to_fill = ''.join('0' for l in range(len(binary_char), 8))
            binary_message_8b.append((to_fill + binary_char))
        return ''.join(binary_message_8b)
    elif( type(message) == np.uint8 or type(message) == int  ):
        binary_message = bin(message).split('b')[1]
        to_fill = ''.join('0' for l in range(len(binary_message), 8))
        return to_fill + binary_message
    elif( type(message) == np.ndarray ):
        binary_message_8b = []
        for value in message:
            binary_message = bin(value).split('b')[1]
            to_fill = ''.join('0' for l in range(len(binary_message), 8))
            binary_message_8b.append(to_fill + binary_message)
        return ''.join(binary_message_8b)


capture = cv2.VideoCapture('output.avi')
done, image = capture.read()
msg = decode_message( image )
print(msg)

while done: 
  done, image = capture.read()
  if done:
    msg = decode_message(image)
    print(msg)
