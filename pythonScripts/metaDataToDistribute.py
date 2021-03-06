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
import platform
import csv
import pandas as pd
import json
import argparse
import crossref
import mysql.connector
import getpass
import authorMetaDataIngest
import contentDomainMetaDataIngest

#Author: Mohammad Tahmid
#Date: 01/30/2021
#Lines: 1-128
#Description: This python script takes in DOI's from the csv generated by "gatherDOI.py" to later pass on for processing 
#UPDATE: This is during the beginning of version 2.0 of the project and was replaced later on in the development of this project. This placed data into MySQL directly instead of using MongoDB.

#tempDir = "AuthorMetaData"
#csvLineCount = 0

#Establlish a connection to the MySQL server to the correct database
print("MySQL Credentials")

#Gets username information from user
mysql_username = input("Username: ")

#Gets password information from user (WHEN TYPING THE PASSWORD IN, IT WILL BE HIDDEN BUT LETTERS ARE BEING ENTERED IN)
mysql_password = getpass.getpass("Password: ")

#Establish a connection to the databse
connection = mysql.connector.connect(user=str(mysql_username), password=str(
        mysql_password), host='127.0.0.1', database='crossrefeventdatamain')

cursor = connection.cursor()


#Changes the working directory to the one this script is running from. 
try: 

    filePath = os.path.abspath(__file__)
    directoryName = os.path.dirname(filePath)
    os.chdir(directoryName)

    #Reads in the DOI list from "gatherDOI.py" to find metadata on from Crossref
    csvData = pd.read_csv("gatherDOI_csv.csv", header = None)
    csvLineCount = len(list(csvData.index))
except OSError:
    print("Cannot change directory to the location of this file")
except:
    print("Unspecified Error, Exiting")



def main():

    #Tracks the row that is entered in from the DOI list.
    currentRows = 0

    with open('DOIValues.csv', newline='') as csvFile:

            #A line is read in from file instead of the whole file in order to be memory efficient 
            lineIn = csv.reader(csvFile)

            #Look continues while there are left to process in the .csv file
            while currentRows < csvLineCount:
            
                #Reads in the next line
                csvRow = next(lineIn) 
                StringConvert = ""
                csvLineString = StringConvert.join(csvRow)

                try:
                    #Creates a "works" object from the Crossref metadata API 
                    from crossref.restful import Works
                    works = Works()

                    #Passes DOI from the .csv file to Crossref to get all metadata info that is available
                    doiMetaData = works.doi(csvLineString)

                    #If author information is found in the "works" obejct then it passed to the "authorMetaDataIngest.py" for processing
                    # if (doiMetaData['author']):

                    #     authorInfo = doiMetaData['author']
                    #     print("Author information for DOI: " + csvLineString + " found") 
                    #     authorMetaDataIngest.authorIngest(connection, cursor, csvLineString, authorInfo)

                    if (doiMetaData['content-domain']):

                        contentDomainInfo = doiMetaData['content-domain']
                        print("Content Domain information for DOI: " + csvLineString + " found") 
                        contentDomainMetaDataIngest.contentDomainIngest(connection, cursor, csvLineString, contentDomainInfo)

                except ImportError:
                    print("Installation of the Crossref API is needed")
                except:
                    print("Unknown Error")

                #Increases counter to keep track of whether at the end of .csv file
                currentRows += 1
                if currentRows > csvLineCount:
                    currentRows = csvLineCount

if __name__ == '__main__':
    main()