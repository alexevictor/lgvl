import re
import sys
import os
from PIL import Image

def main():
    if len(sys.argv) < 2:
        print("Utilizare: python3 extractor.py nume_fișier.c")
        sys.exit(1)

    c_file_path = sys.argv[1]

    if not os.path.exists(c_file_path):
        print(f"Eroare: Fișierul '{c_file_path}' nu există!")
        sys.exit(1)

    print(f"Se decodează formatul hibrid intercalat (RGB565+A8): {c_file_path}")
    with open(c_file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    width, height = 267, 267
    total_pixels = width * height

    # Extragere izolată a blocului hexazecimal
    array_match = re.search(r'ui_img_267x267_e_png_data\s*\[\]\s*=\s*\{(.*?)\}', content, re.DOTALL)
    if not array_match:
        print("Eroare: Nu s-a găsit vectorul de date în fișier!")
        sys.exit(1)

    hex_strings = re.findall(r'0x[0-9a-fA-F]+', array_match.group(1))
    raw_bytes = bytearray(int(h, 16) for h in hex_strings)
    print(f"S-au încărcat {len(raw_bytes)} octeți.")

    pixel_data = []
    idx = 0

    # Citire pixel cu pixel: 2 octeți culoare (RGB565) + 1 octet Alpha
    while idx + 2 < len(raw_bytes) and len(pixel_data) < total_pixels:
        # Extragere culoare pe 16 biți (Little Endian)
        low = raw_bytes[idx]
        high = raw_bytes[idx+1]
        color16 = (high << 8) | low
        
        # Extragere canal Alpha intercalat
        a = raw_bytes[idx+2]
        
        # Avansăm exact cu 3 octeți pentru următorul pixel
        idx += 3

        # Decodare canale standard din structura RGB565
        r = ((color16 >> 11) & 0x1F) * 255 // 31
        g = ((color16 >> 5) & 0x3F) * 255 // 63
        b = (color16 & 0x1F) * 255 // 31

        # FILTRU CURĂȚARE COLOANĂ / ROZ: Dacă masca Alpha este zero sau culoarea tinde 
        # spre fundalul întunecat original, forțăm pixelul în negru profund (0,0,0)
        if a == 0 or (r < 35 and g < 35 and b < 35):
            r, g, b, a = 0, 0, 0, 255
        else:
            # Opțional: Asigurăm opacitate completă pentru cadran ca să nu preia nuanța roz de fundal
            a = 255

        pixel_data.append((r, g, b, a))

    # Completare în caz de siguranță geometrică
    while len(pixel_data) < total_pixels:
        pixel_data.append((0, 0, 0, 255))

    # Salvare imagine originală direct în format PNG
    output_name = "VU_METRU_FINAL_PERFECT.png"
    img = Image.new("RGBA", (width, height))
    img.putdata(pixel_data[:total_pixels])
    img.save(output_name)
    print(f"\n[SUCCES] Imaginea geometrică corectă a fost salvată ca: {output_name}")

if __name__ == "__main__":
    main()
