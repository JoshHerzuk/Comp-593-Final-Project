""" 
COMP 593 - Final Project

Description: 
  Downloads NASA's Astronomy Picture of the Day (APOD) from a specified date
  and sets it as the desktop background image.

Usage:
  python apod_desktop.py image_dir_path [apod_date]

Parameters:
  image_dir_path = Full path of directory in which APOD image is stored
  apod_date = APOD image date (format: YYYY-MM-DD)

History:
  Date        Author    Description
  2022-03-11  J.Dalby   Initial creation
  2022-04-27  J.Herzuk  Finished Script

"""
from sys import argv, exit
from datetime import datetime, date
from hashlib import sha256
from os import path
import os
import sqlite3
import requests
import re
import ctypes

def main():

    # Determine the paths where files are stored
    image_dir_path = get_image_dir_path()
    db_path = path.join(image_dir_path, 'apod_images.db')

    # Get the APOD date, if specified as a parameter
    apod_date = get_apod_date()

    # Create the images database if it does not already exist
    create_image_db(db_path)

    # Get info for the APOD
    apod_info_dict = get_apod_info(apod_date)
    
    # Download today's APOD
    image_url = apod_info_dict['url']
    image_msg = download_apod_image(image_url)
    image_sha256 = sha256(image_msg).hexdigest()
    image_size = len(image_msg)
    image_path = get_image_path(image_url, image_dir_path)
    
    # Print APOD image information
    print_apod_info(image_url, image_path, image_size, image_sha256)
    
    # Add image to cache if not already present
    if not image_already_in_db(db_path, image_sha256):
        save_image_file(image_msg, image_path)
        add_image_to_db(db_path, image_path, image_size, image_sha256)
    
    # Set the desktop background image to the selected APOD
    set_desktop_background_image(image_path)

def get_image_dir_path():
    """
    Validates the command line parameter that specifies the path
    in which all downloaded images are saved locally.

    :returns: Path of directory in which images are saved locally
    """
    if len(argv) >= 2:
        #gets the directory path from the parameter
        dir_path = argv[1]
        if path.isdir(dir_path):
            print("Images directory:", dir_path)
            return dir_path
        else:
            print('Error: Non-existent directory', dir_path)
            exit('Script execution aborted')
    else:
        print('Error: Missing path parameter.')
        exit('Script execution aborted')

def get_apod_date():
    """
    Validates the command line parameter that specifies the APOD date.
    Aborts script execution if date format is invalid.

    :returns: APOD date as a string in 'YYYY-MM-DD' format
    """    
    if len(argv) >= 3:
        # Date parameter has been provided, so get it
        apod_date = argv[2]

        # Validate the date parameter format
        try:
            datetime.strptime(apod_date, '%Y-%m-%d')
        except ValueError:
            print('Error: Incorrect date format; Should be YYYY-MM-DD')
            exit('Script execution aborted')
    else:
        # No date parameter has been provided, so use today's date
        apod_date = date.today().isoformat()
    
    print("APOD date:", apod_date)
    return apod_date

def get_image_path(image_url, dir_path):
    """
    Determines the path at which an image downloaded from
    a specified URL is saved locally.

    :param apod_info_dict: Dictionary containing metadata for the image
    :param dir_path: Path of directory in which image is saved locally
    :returns: Path at which image is saved locally
    """
    #uses regex to extract the image name from the url
    url_search = re.search(r".*/(.*)", image_url)

    image_name = url_search.group(1)
    #joins the directory path with the image name to create the image path
    image_path = os.path.join(dir_path, image_name)

    return image_path

def get_apod_info(date):
    """
    Gets information from the NASA API for the Astronomy 
    Picture of the Day (APOD) from a specified date.

    :param date: APOD date formatted as YYYY-MM-DD
    :returns: Dictionary of APOD info
    """ 
    #my NASA APOD api key
    api_key = '79bUBvryLhNhbVOMkA3gvy4NbR50Dz2hfh5VdFR2'

    print("Retrieving APOD Data...", end='')
       
    URL = 'https://api.nasa.gov/planetary/apod'
    params = {
        'api_key': api_key,
        'date': date
    }
    #queries the API for the image info
    response = requests.get(URL, params=params)

    if response.status_code == 200:
        print("Success.")
        return response.json()

    else:
        print('failed. Response code:', response.status_code)
        return   
    
def print_apod_info(image_url, image_path, image_size, image_sha256):
    """
    Prints information about the APOD

    :param image_url: URL of image
    :param image_path: Path of the image file saved locally
    :param image_size: Size of image in bytes
    :param image_sha256: SHA-256 of image
    :returns: None
    """  
    #prints out the relevant information about the APOD  
    print('Image URL: ', image_url)
    print('Image Path: ', image_path)
    print('Image Size: ', str(image_size), 'bytes')
    print('Image Hash: ', image_sha256)

def download_apod_image(image_url):
    """
    Downloads an image from a specified URL.

    :param image_url: URL of image
    :returns: Response message that contains image data
    """
    print("Retrieving Image Data...", end='')
    #Queries the image url to retrive the response content
    image_data = requests.get(image_url)
    if image_data.status_code == 200:
        print("Success.")
        image_msg = image_data.content
        return image_msg

    else:
        print('failed. Response code:', image_data.status_code)
        return   

def save_image_file(image_msg, image_path):
    """
    Extracts an image file from an HTTP response message
    and saves the image file to disk.

    :param image_msg: HTTP response message
    :param image_path: Path to save image file
    :returns: None
    """
    print("Saving image to disk...", end="")
    #saves the content of image_msg to the hardrive at image_path
    with open(image_path, 'wb') as file:
        file.write(image_msg)
        print("Success.")

def create_image_db(db_path):
    """
    Creates an image database if it doesn't already exist.

    :param db_path: Path of .db file
    :returns: None
    """
    print("Creating image database...", end="")
    #creates the images database if it doesn't already exit
    myConnection = sqlite3.connect(db_path)
    myCursor = myConnection.cursor()
    create_APOD_table = """ CREATE TABLE IF NOT EXISTS images (
                          id integer PRIMARY KEY,
                          image_path text NOT NULL,
                          image_size text NOT NULL,
                          hash text NOT NULL,
                          downloaded_at datetime NOT NULL
                        );"""
    myCursor.execute(create_APOD_table)

    myConnection.commit()
    myConnection.close()

    print("Success.")
   
def add_image_to_db(db_path, image_path, image_size, image_sha256):
    """
    Adds a specified APOD image to the DB.

    :param db_path: Path of .db file
    :param image_path: Path of the image file saved locally
    :param image_size: Size of image in bytes
    :param image_sha256: SHA-256 of image
    :returns: None
    """
    print("Adding image to database...", end="")
    #adds the saved image to the database
    myConnection = sqlite3.connect(db_path)
    myCursor = myConnection.cursor()
    add_image_query = """INSERT INTO images (image_path, 
                      image_size, 
                      hash, 
                      downloaded_at) 
                    VALUES (?, ?, ?, ?);"""

    my_image = (image_path, image_size, image_sha256, datetime.now())

    myCursor.execute(add_image_query, my_image)

    myConnection.commit()
    myConnection.close()

    print("Success.")

def image_already_in_db(db_path, image_sha256):
    """
    Determines whether the image in a response message is already present
    in the DB by comparing its SHA-256 to those in the DB.

    :param db_path: Path of .db file
    :param image_sha256: SHA-256 of image
    :returns: True if image is already in DB; False otherwise
    """ 
    print("Searching for image in database...", end = "")
    my_connection = sqlite3.connect(db_path)
    my_cursor = my_connection.cursor()

    args = (image_sha256)
    hash_search ="""SELECT id FROM images WHERE hash = ?"""

    my_cursor.execute(hash_search, [args])
    results = my_cursor.fetchall()
    my_connection.close()

    if len(results) < 1:
        print("Image not found.")
        return False

    else:
        print("Image found.")
        return True

def set_desktop_background_image(image_path):
    """
    Changes the desktop wallpaper to a specific image.

    :param image_path: Path of image file
    :returns: None
    """
    print("Setting image as desktop background...", end="")
    ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 0)
    print("Success.")

main()