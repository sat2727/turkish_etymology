from random import randint
from bs4 import BeautifulSoup
import constants
import requests
import re
from TurkishStemmer import TurkishStemmer
from time import sleep
import sample_words


def main():
    stats = {"haha": 5, "hehe": 2}
    print(len(stats))
    



def et_etymology(word):
    word = word.lower()
    etym = scrape_et_etym(word)

    if etym:
        return [{"sub_stem": word, "etym": etym, "rank": ["from"], "search_lang": "Turkish", "prev_call": "", "prev_call2": ""}]
    
    stemmer = TurkishStemmer()
    while True:
        stemmed_word = stemmer.stem(word)
        if word == stemmed_word:
            break
        sleep(2)
        etym = scrape_et_etym(stemmed_word)
        if etym:
            return [{"sub_stem": stemmed_word, "etym": etym, "rank": "from", "search_lang": "Turkish", "prev_call": "", "prev_call2": ""}]
        else:
            inf_stemmed_word = form_inf(stemmed_word)
            sleep(2)
            etym = scrape_et_etym(inf_stemmed_word)
            if etym:
                return [{"sub_stem": inf_stemmed_word, "etym": etym, "rank": "from", "search_lang": "Turkish", "prev_call": "", "prev_call2": ""}]

        word = stemmed_word



def get_et_soup(word):
    url = "https://www.etimolojiturkce.com/kelime/" + word
    
    try:
        req_session = requests.Session()
        req = req_session.get(url, headers=constants.REQ_HEADERS)

        return BeautifulSoup(req.content.decode("utf-8", "ignore"), "html.parser")
    except:
        pass


def scrape_et_etym(word):
    soup = get_et_soup(word.lower())
    tags = soup.find_all("span", class_="ety2")
    if tags:
        etyms = []
        for tag in tags:
            s_tags = tag.find_all("span")
            if s_tags:
                for s_tag in s_tags:
                    if s_tag.has_attr("title"):
                        etyms.append(s_tag.attrs["title"])
        if etyms:
            if etyms[0].find("Türkçe") != -1:
                return "Turkic"
            elif etyms[0].find("Arapça") != -1:
                return "Arabic"
            elif etyms[0].find("Farsça") != -1:
                return "Persian"
            elif etyms[0].find("İngilizce") != -1:
                return "English"
            elif etyms[0].find("Germence") != -1:
                return "German"
            elif etyms[0].find("Fransızca") != -1:
                return "French"
            elif etyms[0].find("Latince") != -1:
                return "Latin"
            elif etyms[0].find("Moğolca") != -1:
                return "Mongolian"
            else:
                return "Other"
            

def form_inf(word):
    word = word.strip()

    if has_vowel(word):
        for i in range(len(word)):
            if word[len(word) - 1 - i] in constants.HARD_VOWELS:
                return word + "mak"
            elif word[len(word) - 1 - i] in constants.SOFT_VOWELS:
                return word + "mek"
    else:
        return word


def has_vowel(word):
    for i in range(len(word)):
        if word[i] in constants.VOWELS:
            return True

def scrape_list():
    soup = get_soup()
    words = "words = ["
    td_tags = soup.find_all("td")
    if td_tags:
        for td_tag in td_tags:
            a_tags = td_tag.find_all("a")   
            if a_tags:
                for a_tag in a_tags:
                    if a_tag.string:
                        words = words + "\"" + a_tag.string + "\", "

    words = words[0:len(words) - 2] + "]"
    print(words)



def get_soup():
    url = "https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/Turkish"

    req_session = requests.Session()
    req = req_session.get(url, headers=constants.REQ_HEADERS)
    
    return BeautifulSoup(req.text, "html.parser")

if __name__ == "__main__": 
    main()