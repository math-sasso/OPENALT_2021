# Author: Darpan (Lines 1-236)
"""
MIT License

Copyright (c) 2020 tdbowman-CompSci-F2020

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import json
import csv
import pandas
import logging
import flask
import platform
import mysql
import shutil
import datetime as dt
import time
import dbQuery
from flask import redirect
import emailResults as er

# Importing app config file
path = os.getcwd()
parent = os.path.dirname(path)
config_path = os.path.join(path, "config", "openAltConfig.json")
#config_path = "C:\\Users\\darpa\\Desktop\\openAlt_W2021\\config\\openAltConfig.json"
f = open(config_path)

APP_CONFIG = json.load(f)

### SAMPLE AUTHOR API INFO ###
### https://api.crossref.org/works?query=renear+ontologies ###


# Setter for zip directory
def setZipUni(path):
    global zipUni
    zipUni = path
    print("RESULTS DIRECTORY:", zipUni)


# Getter for zip directory, used to retrieve directory in front end
def getZipUni():
    return zipUni

# Setter for stats
def setStats(x, y):
    global stats
    stats = 'RESULTS: ' + str(x) + '/' + str(y) + ' FOUND'
    print(stats)

# Getter for stats
def getStats():
    return stats


def downloadUni(mysql, dir_csv, type, email):

    # time execution of script
    start_time = time.time()

    # Directories
    dir_file = str(os.path.dirname(os.path.realpath(__file__)))

    # Path of uploaded file
    dir_template = dir_csv

    # Path of results folde with current time
    if not os.path.exists(dir_file + '\\Results'):
        os.mkdir(dir_file + '\\Results')

    dir_results = dir_file + '\\Results\\universityEvents_' + \
        str(dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))

    # Create folder to hold results
    if not os.path.exists(dir_results):
        os.mkdir(dir_results)


    # Set the logging parameters
    if not os.path.exists(dir_file + '\\Logs'):
        os.mkdir(dir_file + '\\Logs')
    logging.basicConfig(filename=dir_file + '\\Logs\\uploadUniversity.log', filemode='a', level=logging.INFO,
                        format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

    # Array containing universities listed in uploaded file
    uni_arr = []


    # Pandas library reads doi list
    uni_list = pandas.read_csv(dir_template, header=None)


    # Adds doi values into array and prints the array
    for x in range(len(uni_list)):
        uni_arr.append(uni_list.values[x][0].lower())

    # Remove duplicates from author array
    uni_arr = list(dict.fromkeys(uni_arr))

    # Set up cursor to run SQL query
    db = mysql.connection
    cursor = db.cursor()

    # Creating text file with API instructions
    f = open(dir_results + '\\API_Instructions.txt', 'w+')
    f.write("Thank you for using OpenAlt v2.0!\n"
            "We do not provide the complete information listed from the APIs. For more complete and raw information, consider using the CrossRef API with the instructions listed below\n\n"
            "1) Download Postman from https://www.postman.com/downloads/\n"
            "2) Run a GET Request on Postman, enter a link listed below and hit send\n"
                "3) You will see the output in the body section on the lower third half of the window. Make sure that the *Body* setting is set to *Pretty* and the dropdown to *JSON*\n\n"
                "You may also use any other API retrieval method, Postman happens to be the method the developers here at OpenAlt use to test APIs\n\n"
                "For more information about the CrossRef API, checkout the links listed below:\n"
                "https://www.crossref.org/education/retrieve-metadata/rest-api/\n"
                "https://github.com/CrossRef/rest-api-doc\n\n\n"
                "YOUR API QUERIES: \n")

    # Execution of query and output of result + log
    resultSet = []
    count = 0

    for uni in uni_arr:
        # Get university Authors
        resultSet = dbQuery.getUniAuthors(uni, cursor)
        logging.info(resultSet)

        # Writing API query to API_Instructions.txt
        uni_api = uni.replace(' ','+')
        f.write(APP_CONFIG['Crossref-Metadata-API']['uni_url'] + uni_api + "\n")

        # Write result to file.
        df = pandas.DataFrame(resultSet)
        df = df.drop_duplicates()

        # If query outputs no results, then author not in database
        if df.empty:
            # CSV containing list of results not found
            emptyResultPath = dir_results + '\\NotFound.csv'

            with open(emptyResultPath,'a',newline='') as emptyCSV:
                writer = csv.writer(emptyCSV)
                writer.writerow([uni])

            logging.info("UNIVERSITY NOT FOUND: " + uni)

        else:
            count = count + 1
            # Replace invalid chars for file name
            invalid_chars = ['/','.','(',')',':','<','>','?','|','\"','*']
            file_id = uni.replace(' ', '-')
            for char in invalid_chars:
                file_id = file_id.replace(char,'-')
            #print('FILE ID:', file_id)

            df.columns = [i[0] for i in cursor.description]  ###### CAUSED ISSUE ON SALSBILS MACHINE #######

            if type == 'csv':
                resultPath = dir_results + '\\' + str(file_id) + '_authorInfo.csv'
                df.to_csv(resultPath,index=False)
            elif type == 'json':
                resultPath = dir_results + '\\' + str(file_id) + '_authorInfo.json'
                df.to_json(resultPath, orient='index', indent=2)



            # Author Associated DOIs Query
            resultSet = dbQuery.getUniArticles(uni, cursor)
            logging.info(resultSet)

            # Write associated DOI info to file.
            df = pandas.DataFrame(resultSet)
            df = df.drop_duplicates()

            if not df.empty:
                df.columns = [i[0] for i in cursor.description]

                if type == 'csv':
                    resultPath = dir_results + '\\' + str(file_id) + '_DOIs.csv'
                    df.to_csv(resultPath,index=False)
                elif type == 'json':
                    resultPath = dir_results + '\\' + str(file_id) + '_DOIs.json'
                    df.to_json(resultPath, orient='index', indent=2)


    # Close API_Instructions.txt
    f.close()

    # Stats of query
    print('\n')
    setStats(count, len(uni_arr))

    # Zip the folder
    shutil.make_archive(str(dir_results), 'zip', dir_results)

    # Delete unzipped folder
    if os.path.exists(dir_results):
        shutil.rmtree(dir_results)

    # Path of zip folder
    zipUni = dir_results + '.zip'
    setZipUni(zipUni)

    # Send Results via email
    er.emailResults(zipUni, email, 'uni')

    # Insert User to Table
    dbQuery.bulkSearchUserInsert(email, 'uni', cursor, db)

    dbQuery.checkUser(email, 'uni', cursor)

    # Time taken to execute script
    print("--- %s seconds ---" % (time.time() - start_time))

    return zipUni


###### Darpan End ######

# ====================== Beginning of Salsabil's Code ======================

def searchByUni(mysql, fileName, type, email):

    # Directory of doi list
    dir = '../web/uploadFiles/' + fileName

    downloadUni(mysql, dir, type, email)

    # Delete uploaded file
    if os.path.exists(dir):
        os.remove(dir)

    return flask.render_template('downloadUni.html', results=getStats())

# ========================= End of Salsabil's Code =========================
