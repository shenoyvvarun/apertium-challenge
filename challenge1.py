#! /usr/bin/python

"""Write (in some scripting language of your choice) a command-line program that takes an Apertium language pair, a source-language sentence S, and a target-language sentence T, and outputs the set of all possible pairs of subsegments (s,t) such that s is a subsegment of S, t a subsegment of T and t is the Apertium translation of s or vice-versa (a subsegment is a sequence of whole words). 

Notes:
    Works with python27
    Assumes you can run apertium as a command
    Case sensitive match between source and target sentence
    Assumes the sentence is equally spaced
    Works only in POSIX Operating systems
"""



import itertools
import sys
import getopt
import re
import subprocess
import os


#global variables
usage = 'Usage: <program>.py -c from-to -s source_sentence -t target_sentence -d apertium_directory [-r]'
is_default_apertium= True
reverse_mode_exists = False

"""Gets the default language directory for an installation of apertium"""
def get_language_dir():
    lang_directory = ''
    try:
        find_installtion_dir = subprocess.Popen(["which","apertium"],stdout=subprocess.PIPE)
        lang_directory,_ = os.path.split(find_installtion_dir.communicate()[0].strip("\n")) #cd ..
        lang_directory,_ = os.path.split(lang_directory) #cd ..
        if find_installtion_dir.returncode != 0 or not os.path.isdir(lang_directory):
            sys.stderr.write("Could not find your apertium installation")
            sys.exit(2)
    except Exception as e:
        sys.stderr.write("which is not available as a command")
        sys.exit(1)
    return lang_directory

"""Get command line arguments as a list"""
def parse_command_line(args):
    global is_default_apertium
    conversion = ''
    source_sentence =''
    target_sentence=''
    reverse= False #whether -r is enabled
    lang_dir=''
    #parse command line inputs
    try:
        opts,args = getopt.getopt(args,"c:s:t:d:r",["conversion","source","target","directory","reverse"])
    except getopt.error,msg:
        print usage
        sys.exit(2)
    for opt,arg in opts:
        if opt in ['-c','--conversion']:
            if len(arg.split("-")) != 2:
                print arg,"expected in pair1-pair2 format"
                sys.exit(7)
            conversion = arg
        elif opt in ['-s','--source']:
            source_sentence = arg
        elif opt in ['-t','--target']:
            target_sentence = arg
        elif opt in ['-d','--directory']:
            is_default_apertium = False
            lang_dir = arg
        elif opt in ['-r','--reverse']:
            reverse = True
    
    return_list = [conversion, source_sentence, target_sentence]
    #All of these are required params and its an error not to specify any one of them
    
    if '' in return_list:
        print usage
        sys.exit(3)
    return_list.extend([lang_dir,reverse])
    return return_list

"""Get the automorf file which is used to split the sentence into its morphological output"""
def get_automorf_try_to_create_if_not_present(language_dir,conversion):
    file_name = os.path.join(language_dir,conversion+".automorf.bin")
    if not os.path.exists(file_name):
        tmp = language_dir.split("/")
        dix_file_name = tmp[len(tmp)-1] if tmp[len(tmp)-1] != '' else tmp[len(tmp)-2] # must be there
        dix_file_name = dix_file_name+"."+conversion.split("-")[0]+".dix"
        dix_file_name = os.path.join(language_dir,dix_file_name)
        morf_file= os.path.join(language_dir,conversion+".automorf.bin")
        if not os.path.exists(dix_file_name):
            print "Could not get the tokens, check your conversion"
            sys.exit(16)
        try:
            new_morf = subprocess.Popen(["lt-comp","lr",dix_file_name,morf_file],stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=sys.stdout)# Try to compile and get the file if it isn't there
            out,err = new_morf.communicate()
            returncode = new_morf.wait()
            if returncode != 0:
                sys.stderr.write("Could not break sentences into tokens, since parts of language pair are incomplete\n"+out)
                sys.exit(8)
        except Exception as e:
            sys.stderr.write("Failed to create "+file_name+"\n")
            sys.exit(11)
    return file_name

"""break the input sentence into lex tokens"""
def get_tokens(sentence,conversion,language):
    #Check whether prerequisites are present
    langs = conversion.split("-")
    if langs[0] == language:
        conversion = language+"-"+langs[1]
    else:
        conversion = language+"-"+langs[0]
    morf_file  = get_automorf_try_to_create_if_not_present(lang_directory, conversion)
    out=''
    try:
        tmp = os.tmpfile()
        tmp.write(sentence)
        tmp.seek(os.SEEK_SET)
        apertium_destxt = subprocess.Popen(["apertium-destxt"],stdout=subprocess.PIPE,stdin=tmp)
        morphological_analyser = subprocess.Popen(["lt-proc",morf_file],stdin=apertium_destxt.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE) ##we will get the morphological output, which will tokenise the sentence
        out,err = morphological_analyser.communicate()
        returncode1 = morphological_analyser.wait()
        returncode2 = apertium_destxt.wait()
        if returncode1 != 0 or returncode2 != 0:
            sys.stderr.write("morphological analyser failed")
            sys.exit(12)
        tmp.close()
    except Exception as e:
        sys.stderr.write("Error executing apertium command\n"+e)
        sys.exit(13)
    words = []
    words_iter =  re.finditer("\\^(.+?)/(.+?)\\$", out)
    for words_match in words_iter:
        if words_match.group(1) != ".": #all except . which is morphological output
            words.append(words_match.group(1))
    return words
    
"""The package may be named as l1-l2 / l2-l1"""
def get_comb(conversion):
    lang = conversion.split("-")
    if len(lang) != 2:
        print conversion,"is not in the expected format"
        sys.exit(11)
    return [lang[0]+"-"+lang[1],lang[1]+"-"+lang[0]]
    
"""Get immediate directories given a PATH"""
def get_immediate_subdirectories(dir):
    try:
        return [name for name in os.listdir(dir) if os.path.isdir(os.path.join(dir, name))]
    except OSError as e:
        sys.stderr.write("required files not found under"+apertium)
        sys.exit(11)

"""Checks whether directory was changed by -d"""
def get_language_dir_if_changed(orginal,changed,conversion):
    if changed == '': #not set using -d
        ret_dir = os.path.join(orginal,"share","apertium")
        dirs = get_immediate_subdirectories(ret_dir)
        possible_combinations = get_comb(conversion)
        if os.path.isdir(os.path.join(ret_dir,"apertium-"+possible_combinations[0])):
            ret_dir = os.path.join(ret_dir,"apertium-"+possible_combinations[0])
        elif os.path.isdir(os.path.join(ret_dir,"apertium-"+possible_combinations[1])):
            ret_dir = os.path.join(ret_dir,"apertium-"+possible_combinations[1])
        else:
            print "Could not find the required language-pair"
            sys.exit(4)
        return ret_dir
    else:
        if not os.path.isdir(changed):
            print "Specified folder in -d doesn't exist"
            sys.exit(5)
        return changed
"""Get all possible subsegments which satisfy the property (s,t) where s is the translation of t or vice versa"""
def get_possible(conversion,source_sentence,target_sentence,lang_dir,language):
    global reverse_mode_exists
    source_words = source_sentence.split(' ')
    #get all possible segements for the sentence, its like traversing an upper dia-gonal matrix
    test_set = []
    for i in range(len(source_words)):
        for j in range(i,len(source_words)):
            test_set.append(" ".join(source_words[i:j+1]))
    process_output = ''
    #Execute the apertium process and get the output, Instead for forking(forking is expensive) the apertium process for every possible pair, we form a paragraph(; sep) and do it once
    try:
        apertium_process = ''
        if is_default_apertium:
            apertium_process=subprocess.Popen(["apertium",conversion,"-u"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        else:
            apertium_process=subprocess.Popen(["apertium",conversion,"-u","-d",lang_dir],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        process_output,_ = apertium_process.communicate(input="; ".join(test_set)) #more strict error checking can be done as per reqmt
        returncode = apertium_process.wait()
        if returncode != 0:
            print "Apertium conversion failed\n",
            if reverse_mode_exists:
                print "Sorry! No reverse mode exists"
            sys.exit(14)
    except Exception as e:
        print "Error executing apertium command\n",e
        sys.exit(3)
    #currently only prints the error
    if apertium_process.returncode != 0:
        print "subprocess output->",process_output
        sys.exit(1)
    #check for pairs (s,t)
    test_output = ' '.join(get_tokens(process_output, conversion, language))
    output_set = test_output.split(" ; ")
    possible_pairs = [] #pairs that satisfy the (s,t) property
    for index,candidate in enumerate(output_set):
        pattern = "(\\b%s\\b)" %(re.escape(candidate.decode("utf-8")))
        if re.search(pattern,unicode(target_sentence.decode("utf-8")),re.IGNORECASE) != None: #ORDERING of segments in translated sentence is not same as ordering in original sentence
            possible_pairs.append((test_set[index],candidate))
    return possible_pairs

"""Display the result which is obtained as a pair """
def display_result_pair(pair):
    sys.stdout.write("(")
    match = re.search(re.escape(pair[0].replace("' ","'",).replace(" '","'")),args[1],re.IGNORECASE)
    if match == None:
        sys.stdout.write(pair[0].decode("utf8").replace("' ","'",).replace(" '","'"))
    else:
        sys.stdout.write(args[1][match.start():match.end()])
    sys.stdout.write(",")
    match = re.search(re.escape(pair[1].replace("' ","'",).replace(" '","'")),args[2],re.IGNORECASE)
    if match == None:
        sys.stdout.write(pair[1].decode("utf8").replace("' ","'",).replace(" '","'"))
    else:
        sys.stdout.write(args[2][match.start():match.end()])
    sys.stdout.write(")\n")    

if __name__=="__main__":
    lang_directory = get_language_dir()
    args = parse_command_line(sys.argv[1:])
    lang_directory = get_language_dir_if_changed(lang_directory,args[3],args[0])
    source_words = ''   
    target_words = ''
    langs = args[0].split("-")
    source_sentence = ' '.join(get_tokens(args[1], args[0], langs[0]))
    target_sentence = ' '.join(get_tokens(args[2], args[0], langs[1]))
    total_pairs= set(get_possible(args[0], source_sentence, target_sentence, lang_directory,langs[1]))
    if args[4]:
        reverse_mode_exists = True
        conversion = langs[1]+"-"+langs[0]
        pairs = get_possible(conversion, target_sentence,source_sentence,lang_directory,langs[0])
        for pair in [(pair[1],pair[0]) for pair in pairs]:
            total_pairs.add(pair)
    for pair in total_pairs:
        display_result_pair(pair)
