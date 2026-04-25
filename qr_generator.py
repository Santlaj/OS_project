import qrcode
import sys

def create_youtube_qr(video_url, output_filename="youtube_qr.png"):
    """
    Creates an ad-free QR code for a YouTube video or any URL.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction to allow for some damage or logo
        box_size=10,
        border=4,
    )
    
    # Add the URL data to the QR code
    qr.add_data(video_url)
    qr.make(fit=True)

    # Generate the image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save the image
    img.save(output_filename)
    print(f"Success! Your ad-free QR code has been saved as: {output_filename}")

if __name__ == "__main__":
    print("=== Ad-Free YouTube QR Code Generator ===")
    url = input("Enter the YouTube video URL: ").strip()
    
    if not url:
        print("Error: URL cannot be empty.")
        sys.exit(1)
        
    filename = input("Enter the output file name (press Enter for 'youtube_qr.png'): ").strip()
    
    if not filename:
        filename = "youtube_qr.png"
    elif not filename.endswith(".png"):
        filename += ".png"
        
    create_youtube_qr(url, filename)
