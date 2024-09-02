import cv2
import rembg
import easygui
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont
import os

def apply_light_sepia(image, intensity=0.5):
    width, height = image.size
    pixels = image.load()

    for py in range(height):
        for px in range(width):
            r, g, b, a = pixels[px, py]

            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
            tb = int(0.272 * r + 0.534 * g + 0.131 * b)

            tr = min(255, tr)
            tg = min(255, tg)
            tb = min(255, tb)

            r = int(r * (1 - intensity) + tr * intensity)
            g = int(g * (1 - intensity) + tg * intensity)
            b = int(b * (1 - intensity) + tb * intensity)

            pixels[px, py] = (r, g, b, a)

    return image

def adjust_image(image, brightness=1.0, contrast=1.0, saturation=1.0, warmth=1.0, fade=0):
    image = ImageEnhance.Brightness(image).enhance(brightness)
    image = ImageEnhance.Contrast(image).enhance(contrast)
    image = ImageEnhance.Color(image).enhance(saturation)
    
    if warmth != 1.0:
        r, g, b = image.split()
        r = r.point(lambda i: i * warmth)
        b = b.point(lambda i: i * (2 - warmth))
        image = Image.merge('RGB', (r, g, b))
    
    if fade > 0:
        grey_image = Image.new("RGB", image.size, (128, 128, 128))
        image = Image.blend(image, grey_image, fade / 100.0)
    
    return image

def manual_crop_image(image):
    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    r = cv2.selectROI("Crop Image", cv_image, fromCenter=False, showCrosshair=True)
    cropped_cv_image = cv_image[int(r[1]):int(r[1]+r[3]), int(r[0]):int(r[0]+r[2])]
    cropped_image = Image.fromarray(cv2.cvtColor(cropped_cv_image, cv2.COLOR_BGR2RGB))
    cv2.destroyAllWindows()
    return cropped_image

def real_time_adjustment(image):
    def nothing(x):
        pass
    
    cv_image = np.array(image)
    cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
    
    cv2.namedWindow('Adjust Image')

    cv2.createTrackbar('Brightness', 'Adjust Image', 100, 200, nothing)
    cv2.createTrackbar('Contrast', 'Adjust Image', 100, 200, nothing)
    cv2.createTrackbar('Saturation', 'Adjust Image', 100, 200, nothing)
    cv2.createTrackbar('Warmth', 'Adjust Image', 100, 200, nothing)
    cv2.createTrackbar('Fade', 'Adjust Image', 0, 100, nothing)
    
    while True:
        brightness = cv2.getTrackbarPos('Brightness', 'Adjust Image') / 100.0
        contrast = cv2.getTrackbarPos('Contrast', 'Adjust Image') / 100.0
        saturation = cv2.getTrackbarPos('Saturation', 'Adjust Image') / 100.0
        warmth = cv2.getTrackbarPos('Warmth', 'Adjust Image') / 100.0
        fade = cv2.getTrackbarPos('Fade', 'Adjust Image')
        
        adjusted_image = adjust_image(image, brightness, contrast, saturation, warmth, fade)
        
        adjusted_cv_image = cv2.cvtColor(np.array(adjusted_image), cv2.COLOR_RGB2BGR)
        cv2.imshow('Adjust Image', adjusted_cv_image)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()
    return adjusted_image

def add_text_to_image(image, text, position, font_size, font_color):
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    draw.text(position, text, font=font, fill=font_color)
    return image

def text_adjustment_loop(result_image):
    while True:
        text = easygui.enterbox("Enter the text you want to add:", "Add Text")
        if not text:
            break

        font_size = easygui.integerbox("Enter the font size:", "Font Size", 20, 10, 100)
        font_color = easygui.enterbox("Enter the font color (e.g., 'white', 'black', '#ff0000'):", "Font Color", "white")

        cv_image = np.array(result_image)
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)

        r = cv2.selectROI("Select Text Position", cv_image, fromCenter=False, showCrosshair=True)
        cv2.destroyAllWindows()

        result_image_with_text = add_text_to_image(result_image.copy(), text, (r[0], r[1]), font_size, font_color)

        preview_image = np.array(result_image_with_text)
        cv2.imshow('Text Preview', cv2.cvtColor(preview_image, cv2.COLOR_RGB2BGR))
        key = cv2.waitKey(0) & 0xFF
        cv2.destroyAllWindows()

        confirm = easygui.ynbox("Are you satisfied with the text position and settings?", "Confirm Text", ("Yes", "No"))
        if confirm:
            result_image = result_image_with_text
            break

    return result_image

welcome_message = "Welcome to the Photo Master Project!"
easygui.msgbox(welcome_message, title="Photo Master")

choice = easygui.buttonbox("Choose an option:", "Photo Master", ("Click a Photo", "Upload a Picture"))

image = None

if choice == "Click a Photo":
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        cv2.imshow('Preview', frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 32:
            break
        elif key == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            exit()

    cap.release()
    cv2.destroyAllWindows()
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    preview_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    cv2.imshow('Captured Image', preview_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

elif choice == "Upload a Picture":
    image_path = easygui.fileopenbox(title="Select a Picture to Upload")
    if image_path:
        image = Image.open(image_path)

if image is not None:
    crop_option = easygui.ynbox("Would you like to crop the image manually?", "Crop Image", ("Yes", "No"))
    if crop_option:
        image = manual_crop_image(image)
    
    adjust_option = easygui.ynbox("Would you like to adjust brightness, contrast, etc.?", "Adjust Image", ("Yes", "No"))
    if adjust_option:
        image = real_time_adjustment(image)

    proceed = easygui.ynbox('Do you want to proceed with this image?', 'Confirm', ('Yes', 'No'))

    if proceed:
        output = rembg.remove(image)
        output = output.convert("RGBA")
        mask = output.split()[3]
        background_path = easygui.fileopenbox(title='Select a background image')
        background_image = Image.open(background_path)
        background_image = background_image.resize(output.size)

        object_filters = easygui.buttonbox('Do you want to apply filters to the object photo?', 'Object Filters', ('Yes', 'No'))
        if object_filters == 'Yes':
            while True:
                action = easygui.buttonbox('What kind of filter do you want to apply to the object photo?', 'Object Filters', ('Blur', 'Sharpen', 'Sepia', 'Done'))
                if action == 'Blur':
                    output = output.filter(ImageFilter.BLUR)
                elif action == 'Sharpen':
                    output = output.filter(ImageFilter.SHARPEN)
                elif action == 'Sepia':
                    output = apply_light_sepia(output)
                elif action == 'Done':
                    break

        result_image = background_image.copy()
        result_image.paste(output, mask=mask)

        overall_filters = easygui.buttonbox('Do you want to apply filters to the overall photo?', 'Overall Filters', ('Yes', 'No'))
        if overall_filters == 'Yes':
            while True:
                action = easygui.buttonbox('What kind of filter do you want to apply to the overall photo?', 'Overall Filters', ('Blur', 'Sharpen', 'Sepia', 'Done'))
                if action == 'Blur':
                    result_image = result_image.filter(ImageFilter.BLUR)
                
                elif action == 'Sharpen':
                    result_image = result_image.filter(ImageFilter.SHARPEN)
                elif action == 'Sepia':
                    result_image = apply_light_sepia(result_image)
                elif action == 'Done':
                    break

        # Allow the user to add text to the image with preview and adjustment
        add_text_option = easygui.ynbox('Do you want to add text to the image?', 'Add Text', ('Yes', 'No'))
        if add_text_option:
            result_image = text_adjustment_loop(result_image)

        # Save the final image
        output_path = easygui.filesavebox(title='Save as')
        if output_path:
            if not os.path.splitext(output_path)[1]:
                output_path += ".png"
            result_image.save(output_path)
else:
    print('No image selected. Exiting...')
