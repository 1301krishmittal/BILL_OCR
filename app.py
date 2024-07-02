import streamlit as st
import sys

from paddleocr import PaddleOCR, draw_ocr
import re
from PIL import Image
import numpy as np
from pdf2image import convert_from_bytes
st.markdown(
    """
    <style>
    body {
        background-color: #f0f2f6; /* A light grey-blue background color similar to ChatGPT */
        color: #333333; /* Dark grey text color */
    }
    .stApp {
        background-color: #f0f2f6; /* Same light grey-blue background color */
    }
    .reportview-container .main .block-container {
        padding: 2rem;
        background-color: #ffffff; /* White background for main content area */
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1); /* Subtle shadow effect */
    }
    .custom-label {
        font-size: 20px; /* Adjust the font size */
        color: #ff6600; /* Adjust the color */
        font-weight: bold; /* Make it bold */
    }
    .custom-label2 {
        font-size: 14px; /* Adjust the font size */
        color: #eb3446; /* Adjust the color */
        margin-bottom:20px;
        text-align:center;
    }
    .custom-selectbox {
    border: 2px solid #ff6600 ; /* Add border to selectbox */
    border-radius: 4px; /* Rounded corners */
    color: black;
    height:40px;
    font-size: 16px; /* Font size */
    }

    .custom-selectbox:hover {
    border-color: white ; 
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Functions for extracting GST numbers and dates
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    
def extract_gst_number(word):
    gst_pattern =  r'\b(?:\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z\d]{2})\b'
    a = re.findall(gst_pattern, word)
    return a

def extract_dates(text):
    date_pattern1 = r'\b(?:\d{2}/\d{2}/\d{4})\b'
    date_pattern2 = r'\b(?:\d{2}/(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/\d{4})\b'
    date_pattern3 = r'\b(?:\d{2}\.\d{2}\.\d{4})\b'
    date_pattern4 = r'\b(?:\d{2}\-\d{2}\-\d{4})\b'
    date_pattern5 = r'\b(?:\d{1,2}-(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)-\d{2,4})\b'
    
    
    lst = []
    dates1 = re.findall(date_pattern1, text,flags=re.IGNORECASE)
    dates2 = re.findall(date_pattern2, text,flags=re.IGNORECASE)
    dates3 = re.findall(date_pattern3, text,flags=re.IGNORECASE)
    dates4 = re.findall(date_pattern4, text,flags=re.IGNORECASE)
    dates5 = re.findall(date_pattern5, text,flags=re.IGNORECASE)
    if dates1:
        lst.extend(dates1)
    if dates2:
        lst.extend(dates2)
    if dates3:
        lst.extend(dates3)
    if dates4:
        lst.extend(dates4)
    if dates5:
        lst.append(dates5)
    return lst

def has_number(s):
    for i in s:
        try:
            float(i)
            return False
        except ValueError:
            pass
    return True

def has_common_word(s):
    common_words = ['gst', 'invoice', 'tax', 'date', 'code', 'bill', 'rate', 'total', 'amount', 'copy','balance',':']
    for word in common_words:
        if word.lower() in s.lower():
            return False
    return True

def avg_height(boxes):
    avg_height = 0
    n = 0
    for i in boxes:
        n += 1 
        avg_height += abs(i[2][1] - i[1][1])
    return avg_height / n

def overlapping_parmeter(x1,x2,xn1,xn2):
    #assuming threshhold to be 20
    if(x1 == xn1  and x2 == xn2):
        return True
    if(x1<=xn1 and x2>=xn2):
        return True
    if(xn1<=x1  and xn2>=x2):
        return True
    if(x1 > xn1 and x1>=xn2):
        return False
    if(xn1>x1 and xn1>=x2):
        return False
    if(xn1>=x1 and xn1<=x2):
        if(x2-xn1>20):
            return True
        return False
    if(xn2>=x1 and xn2<=x2):
        if(xn2-x1>20):
            return True
        return False
    


# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')

# Streamlit app
st.title('Invoice Data Extractor')

uploaded_file = st.file_uploader("Upload an invoice image", type=["png", "jpg", "jpeg","pdf"])

if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        images = convert_from_bytes(uploaded_file.read())
        imagel = images[0]  # Take the first page
        st.image(imagel, caption='First page of uploaded PDF', use_column_width=True)

        # Convert PIL Image to numpy array
        image = np.array(imagel)

        # Perform OCR on preprocessed image
        result = ocr.ocr(image, cls=True)
    else:
        imagel = Image.open(uploaded_file)
        st.image(imagel, caption='Uploaded Image', use_column_width=True)

        # Perform OCR on original image
        image = np.array(imagel)
        result = ocr.ocr(image, cls=True)
    result = result[0]
    boxes = [line[0] for line in result]
    txts = [line[1][0] for line in result]
    scores = [line[1][1] for line in result]
    # print(txts)

    lst_gst = []
    lst_date = []
    lst_company_name = []
    lst_Amount = []
    lst_total = []
    lst_tax = []

    average_height = avg_height(boxes)
    target_length = len(txts) / 8
    
    # For Company name
    for i in range(int(target_length)):
        temp_box  = boxes[i]
        temp_text = txts[i]
        high = abs(temp_box[2][1] - temp_box[1][1])
        if high > average_height:
            lst_company_name.append(temp_text)

    # For amount,Tax and Total
    for i in range(len(txts)):
        if('AMOUNT' in txts[i].upper()  or 'AMT' in txts[i].upper()):
            tmp_lst = []
            x1,y1,x2,y2 = boxes[i][0][0], boxes[i][0][1],boxes[i][2][0],boxes[i][2][1]
            for j in range(len(txts)):
                xn1,yn1,xn2,yn2 = boxes[j][0][0], boxes[j][0][1],boxes[j][2][0],boxes[j][2][1]
                if(overlapping_parmeter(x1,x2,xn1,xn2) == True  and is_number(txts[j]) == False and yn1>=y2):
                    break
                if(overlapping_parmeter(x1,x2,xn1,xn2) == True and is_number(txts[j]) == True and yn1>=y2):
                    # print(x1,x2,xn1,xn2,txts[i],txts[j])
                    tmp_lst.append(txts[j])
            if(len(tmp_lst)>0):    
                lst_Amount.append({txts[i]:tmp_lst})
        if('TOTAL' in txts[i].upper()):
            tmp_lst = []
            x1,y1,x2,y2 = boxes[i][0][0], boxes[i][0][1],boxes[i][2][0],boxes[i][2][1]
            for j in range(len(txts)):
                xn1,yn1,xn2,yn2 = boxes[j][0][0], boxes[j][0][1],boxes[j][2][0],boxes[j][2][1]
                if(overlapping_parmeter(x1,x2,xn1,xn2) == True  and is_number(txts[j]) == False and yn1>=y2):
                    break
                if(overlapping_parmeter(x1,x2,xn1,xn2) == True and is_number(txts[j]) == True and yn1>=y2):
                    # print(x1,x2,xn1,xn2,txts[i],txts[j])
                    tmp_lst.append(txts[j])
            if(len(lst_total)>0):
                lst_total.append({txts[i]:tmp_lst})
        
        if('TAX' in txts[i].upper()):
            tmp_lst = []
            x1,y1,x2,y2 = boxes[i][0][0], boxes[i][0][1],boxes[i][2][0],boxes[i][2][1]
            for j in range(len(txts)):
                xn1,yn1,xn2,yn2 = boxes[j][0][0], boxes[j][0][1],boxes[j][2][0],boxes[j][2][1]
                if(overlapping_parmeter(x1,x2,xn1,xn2) == True  and is_number(txts[j]) == False and yn1>=y2):
                    break
                if(overlapping_parmeter(x1,x2,xn1,xn2) == True and is_number(txts[j]) == True and yn1>=y2):
                    # print(x1,x2,xn1,xn2,txts[i],txts[j])
                    tmp_lst.append(txts[j])
            if(len(lst_tax)>0):
                lst_tax.append({txts[i]:tmp_lst})


    lst_company_name = sorted(lst_company_name)[-6:]
    latest_company_name = [i for i in lst_company_name if has_common_word(i) and has_number(i)]

    for i in txts:
        a = extract_dates(i)
        if a:
            lst_date.extend(a)
        a = extract_gst_number(i)
        if a:
            lst_gst.extend(a)

    # Display results with dropdowns
    st.subheader('Extracted Information')

    if lst_date:
        st.markdown('<div class="custom-label">Dates:</div>', unsafe_allow_html=True)
        date = st.selectbox('', lst_date)
        st.markdown(f'<div class="custom-label2">{date}</div>', unsafe_allow_html=True)
    else:
        st.write('No dates found.')

    if lst_gst:
        st.markdown('<div class="custom-label">GST Numbers:</div>', unsafe_allow_html=True)
        gst = st.selectbox('', lst_gst)
        st.markdown(f'<div class="custom-label2">{gst}</div>', unsafe_allow_html=True)
    else:
        st.write('No GST numbers found.')

    if latest_company_name:
        st.markdown('<div class="custom-label">Company Names:</div>', unsafe_allow_html=True)
        company_name = st.selectbox('',latest_company_name)        
        st.markdown(f'<div class="custom-label2">{company_name}</div>', unsafe_allow_html=True)
    else:
        st.write("No company Name found.")
    
    if(lst_total):
        st.markdown('<div class="custom-label">Totals:</div>', unsafe_allow_html=True)
        totals = st.selectbox("",lst_total)
        st.markdown(f'<div class="custom-label2">{totals}</div>', unsafe_allow_html=True)
    else:
        st.write("No totals found in bills.")
    
    if(lst_Amount):
        st.markdown('<div class="custom-label">Amount:</div>', unsafe_allow_html=True)
        amount = st.selectbox("",lst_Amount)
        st.markdown(f'<div class="custom-label2">{amount}</div>', unsafe_allow_html=True)
    else:
        st.write("No amount found in bill")
    
    if(lst_tax):
        st.markdown('<div class="custom-label">Tax:</div>', unsafe_allow_html=True)
        tax = st.selectbox("",lst_tax)
        st.markdown(f'<div class="custom-label2">{tax}</div>', unsafe_allow_html=True)
    else:
        st.write("No tax word found.")


    st.write('All Extracted Texts:')
    st.write(txts)
