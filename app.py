from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from PIL import Image
import os
import numpy as np

app = Flask(__name__)

# Folder untuk menyimpan file gambar
UPLOAD_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Fungsi untuk menyisipkan pesan teks ke dalam gambar menggunakan LSB
def encode_image(image_path, message):
    img = Image.open(image_path)
    img = img.convert("RGB")
    encoded_image = img.copy()
    pixels = encoded_image.load()

    binary_message = ''.join(format(ord(i), '08b') for i in message) + '1111111111111110'  # Menambahkan delimiter
    message_index = 0

    for i in range(img.width):
        for j in range(img.height):
            pixel = list(pixels[i, j])

            for k in range(3):  # Loop untuk Red, Green, Blue channels
                if message_index < len(binary_message):
                    pixel[k] = (pixel[k] & 0xFE) | int(binary_message[message_index])  # Modifikasi LSB
                    message_index += 1
                if message_index >= len(binary_message):
                    break
            pixels[i, j] = tuple(pixel)
            if message_index >= len(binary_message):
                break

    # Simpan gambar yang telah dienkode
    encoded_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'encoded_image.png')
    encoded_image.save(encoded_image_path)
    return encoded_image_path

# Fungsi untuk mengekstrak pesan dari gambar
def decode_image(image_path):
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = img.load()

    binary_message = ""

    for i in range(img.width):
        for j in range(img.height):
            pixel = list(pixels[i, j])

            for k in range(3):
                binary_message += str(pixel[k] & 1)

    # Menemukan delimiter untuk memotong pesan yang disisipkan
    message_end = binary_message.find('1111111111111110')
    if message_end != -1:
        binary_message = binary_message[:message_end]

    # Mengubah binary ke karakter
    message = ''.join(chr(int(binary_message[i:i+8], 2)) for i in range(0, len(binary_message), 8))

    return message

# Fungsi untuk menghitung MSE dan PSNR
def calculate_mse_psnr(original_image_path, encoded_image_path):
    original_img = Image.open(original_image_path).convert("RGB")
    encoded_img = Image.open(encoded_image_path).convert("RGB")

    # Mengubah gambar menjadi array numpy
    original_array = np.array(original_img)
    encoded_array = np.array(encoded_img)

    # Menghitung MSE (Mean Squared Error)
    mse = np.mean((original_array - encoded_array) ** 2)
    if mse == 0:  # Tidak ada perbedaan
        psnr = float('inf')
    else:
        # Menghitung PSNR
        max_pixel_value = 255.0
        psnr = 20 * np.log10(max_pixel_value / np.sqrt(mse))
    
    return mse, psnr

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        image = request.files['image']
        message = request.form['message']
        
        # Menyimpan file gambar sementara
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded_image.png')
        image.save(img_path)
        
        # Encode pesan ke gambar
        encoded_image_path = encode_image(img_path, message)
        
        # Menghitung MSE dan PSNR
        mse_value, psnr_value = calculate_mse_psnr(img_path, encoded_image_path)

        # Tampilkan hasil PSNR dan MSE di halaman unduh
        return redirect(url_for('download', mse=mse_value, psnr=psnr_value))
    
    return render_template('index.html')

@app.route('/download')
def download():
    # Mendapatkan nilai MSE dan PSNR dari query parameter
    mse = request.args.get('mse', None)
    psnr = request.args.get('psnr', None)
    return render_template('download.html', mse=mse, psnr=psnr)
@app.route('/decode', methods=['GET', 'POST'])
def decode():
    if request.method == 'POST':
        image = request.files['image']
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], 'decoded_image.png')
        image.save(img_path)

        # Decode pesan dari gambar
        message = decode_image(img_path)

        return render_template('decode.html', message=message)
    
    return render_template('decode.html', message=None)

if __name__ == '__main__':
    app.run(debug=True)
