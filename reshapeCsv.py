import sys, os, pprint
import numpy as np
import pandas as pd
import unicodedata
import math

def isnan(x):
    if ( isinstance(x, float)):
        if ( math.isnan(x)):
            return True
    return False

def is_japanese(string):
    if ( isinstance(string, str) ):
        for ch in string:
            try:
                name = unicodedata.name(ch)
                #print ("name=", name, "ch=", ch)
                if "CJK UNIFIED" in name \
                   or "HIRAGANA" in name \
                   or "KATAKANA" in name:
                    return True
            except:
                pass
    return False

def unify_lang(d, k1, k2,verbose=False):
    """
    d : pandas dataset
    k1, k2:  keywords for Jap. and Eng.
    """
    
    N = d.shape[0]
    outputArray = np.empty((N,3), dtype="U1024")
    for i, (J, E) in enumerate(zip(d[k1], d[k2])):
        ET = is_japanese(E)
        if ( ET ):
            print ("ThisIsNotEnglish", E)
            E = "<<<JAPANESE>>>"
        if ( d[k1].isnull()[i] ) | ( ET ):
            outputArray[i,0]=E
            outputArray[i,1]=E
            outputArray[i,2]=True
        elif ( d[k2].isnull()[i] ) :
            outputArray[i,0]=J
            outputArray[i,1]=np.nan
            outputArray[i,2]=False
        else:
            outputArray[i,0]=J
            outputArray[i,1]=E
            outputArray[i,2]=True
        if ( verbose ):
            print (outputArray[i])
            
    return outputArray

def truncate_author(author, npresent):
    item = author.split(",")
    output = ""
    for i in item[:npresent-1]:
        output += i+","
    output += item[npresent-1]
    return output


def shorten_author(authors, npresent=0):
    """
    authors : np.array(N,2)
    """
    N = authors.shape[0]
    outputArray = np.empty((N), dtype="U1024")
    for i, elem in enumerate(authors):
        item = elem.split(",")
        Nauthors = len(item)
        if ( npresent == 0 ):
            outputArray[i] = elem
        else:
            if (Nauthors > npresent ):
                outputArray[i] = truncate_author(elem, npresent) + ", et. al"
            else:
                outputArray[i] = elem
        #print (Nauthors, npresent, len(outputArray[i].split(",")), outputArray[i])
    return outputArray

def nan2space(strng, comma=True):
    if strng is np.nan:
        return ""
    else:
        if (comma):
            return strng+", "
        else:
            return strng
        
def remove_tailcomma(string):
    if string[-2:] == ", ":
        string = string[:-2]
    return string
        

def merge_issue(volu, issu, page):
    """
    volu, issu, page : np.array(N)
    """
    N = volu.shape[0]
    outputArray = np.empty(N, dtype="U1024")
    for i in range(N):
        #print (i, volu[i], issu[i], page[i], end="  ")
        try:
            outputArray[i] = remove_tailcomma( nan2space(volu[i])+nan2space(issu[i])+nan2space(page[i], comma=False) )
        except:
            outputArray[i] = ""
        #print (outputArray[i])
    return outputArray

def reshape_date(d):
    outputArray = []
    for date in d.astype("str"):
        if date[4:6]=="00":
            outputArray.append([date[0:4],""])
        else:
            outputArray.append([date[0:4],date[4:6]])
    return np.array(outputArray)

def merge_link(d1, d2):
    outputArray = []
    for l1, l2, in zip(d1, d2):
        if ( isnan(l1) ):
            o1 = ""
        else:
            o1 = l1
        if ( isnan(l2) ):
            o2 = ""
        else:
            o2 = l2
        outputArray.append([o1,o2])
    return np.array(outputArray)
        

    
if __name__ == "__main__":

    fileInput = sys.argv[1]
    npresent = 7 # number of maximum authors to explicitly show
    types = sys.argv[2]

    d = pd.read_csv(fileInput, quotechar='"', skipinitialspace=True, header=0)
    assertmatrix = np.array(d.isnull())
    
    keys = d.keys()
    #for i, k in enumerate(keys):
    #    print (i, k)

    #
    # common for papers and books
    #
    
    title   = unify_lang(d, keys[0], keys[1])
    author_ = unify_lang(d, keys[2], keys[3])
    journal = unify_lang(d, keys[4], keys[5])

    
    auth_J_ = shorten_author(author_[:,0], npresent)
    auth_E_ = shorten_author(author_[:,1], npresent)
    author = np.vstack([auth_J_, auth_E_]).T

    print (title.shape, author_.shape, journal.shape)
    print (title[:,2], author_[:,2], journal[:,2])
    show_Eng = (title[:,2]=="True")&(author_[:,2]=="True")&(journal[:,2]=="True")

    
    num = merge_issue(d[keys[6]], d[keys[7]], d[keys[8]])
    


    #
    # different process for papers or books
    #
    if ( types == "papers" ):
        pub_date = reshape_date(d[keys[10]])
        doi = d[keys[9]]
        link = np.array(doi).copy().reshape(len(doi),1)
        for i in range(len(link)):
            if ( isnan(doi[i]) ):
                link[i,] = ""
            else:
                link[i,] = "https://doi.org/%s"%(doi[i])
            print (link[i,])
    elif ( types == "books" ):
        pub_date = reshape_date(d[keys[9]])
        link = merge_link(d[keys[10]], d[keys[11]])
        for i in link:
            print (i)
    else:
        print ("types unknown", types)
        sys.exit()


    #
    # output
    #

    
    fe = open("outputJ_%s.csv"%types, "w")
    for i in range(pub_date.shape[0]):
        str  = "\"%i\","%(i)
        #str += title[i,2]+author_[i,2]+journal[i,2]+"%r"%show_Eng[i]
        str += "\""+title[i,0]+"\","
        str += "\""+author[i,0]+"\","
        str += "\""+journal[i,0]+"\","
        str += "\""+num[i]+"\","
        str += "\""+pub_date[i,0]+"\","
        str += "\""+pub_date[i,1]+"\","
        str += "\""+link[i,0]+"\""
        if ( link.shape[1] == 2 ):
            str += ",\""+link[i,1]+"\""
        str += "\n"
        fe.write(str)
        #print (link[i])
    fe.close()

    fj = open("outputE_%s.csv"%types, "w")
    for i in range(pub_date.shape[0]):
        if ( show_Eng[i] ):
            str  = "\"%i\","%(i)
            str += "\""+title[i,1]+"\","
            str += "\""+author[i,1]+"\","
            str += "\""+journal[i,1]+"\","
            str += "\""+num[i]+"\","
            str += "\""+pub_date[i,0]+"\","
            str += "\""+pub_date[i,1]+"\","
            str += "\""+link[i,0]+"\""
            if ( link.shape[1] == 2 ):
                str += ",\""+link[i,1]+"\""
            str += "\n"
            fj.write(str)
    fj.close()
