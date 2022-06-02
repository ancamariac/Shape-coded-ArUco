import cv2
import numpy as np

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
    
def encode_message(image, message):
    end_of_message_string = '@#$%^&'

    message = message + end_of_message_string
    binary_message = get_binary(message)

    max_bytes_to_encode = (image.shape[0] * image.shape[1] * 3 ) // 8
    if( max_bytes_to_encode > len(message) ):
        # Index pentru pozitia curenta din reprezentarea binara a mesajului
        index = 1
        for row in image:
            for pixel in row:
                b = get_binary(pixel[0])
                g = get_binary(pixel[1])
                r = get_binary(pixel[2])
                
                if( index < len(binary_message) ): 
                    b_steg = binary_message[index-1] + binary_message[index]
                    pixel[0] = int(b[0:-2] + b_steg, 2)
                    index += 2
                else: 
                    return image
                if( index < len(binary_message) ): 
                    g_steg = binary_message[index-1] + binary_message[index]
                    pixel[1] = int(g[0:-2] + g_steg, 2)
                    index += 2
                else: 
                    return image
                if( index < len(binary_message) ): 
                    r_steg = binary_message[index-1] + binary_message[index]
                    pixel[2] = int(r[0:-2] + r_steg, 2)
                    index += 2
                else: 
                    return image
        return image
    else:
        # TODO: returnati o imagine goala (neagra) daca encodarea nu a putut fi realizata
        print("Mesajul este prea mare pentru a fi ascuns in imagine!")


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

with open("speech.txt",'r') as script:
    speech = script.read().splitlines()
    
res = []
for x in range(10):
    res.append(speech[x * 9 :  (x + 1) * 9])
    
import numpy as np
import cv2
import time

COMPRESSED_FORMAT = False

cap = cv2.VideoCapture(0)
print("Opened Camera")

if( COMPRESSED_FORMAT == True ):
    # Folosim codec MPEG4 
    fourcc = cv2.VideoWriter_fourcc(*'3IVD')#FFmpeg DivX (MS MPEG-4 v3)
else: 
    # Nu folosim comprimare, video-ul va fi salvat frame cu frame.
    fourcc = cv2.VideoWriter_fourcc(*'RGBA')

fps = 25.0
duration = 3 # seconds
dimensions = (640,  480)

frame_number = -1
counter = 0
out = cv2.VideoWriter('output.avi', fourcc, fps, dimensions)
if(cap.isOpened()):
    t = time.time()
    while( (time.time() - t) < duration ):
        frame_number += 1
        ret, frame = cap.read()
        
        if (frame_number % 5) == 0 and counter < 10:
            image_stegano = encode_message(frame, ''.join(res[counter]) )
            counter += 1
            frame = image_stegano
            #cv2.imwrite('tree_stegano.png', frame)

            
        
        if not ret:
            break
        
        out.write(frame)


cap.release()
out.release()
cv2.destroyAllWindows()
print("Video Saved")

import cv2
vidcap = cv2.VideoCapture('output.avi')
success,image = vidcap.read()
message_decoded = decode_message( image )
print(message_decoded)
count = 0

while success: 
  success,image = vidcap.read()
  if success:
      message_decoded = decode_message( image )
      print(message_decoded)