from TurkishStemmer import TurkishStemmer
import requests
from bs4 import BeautifulSoup
import re
from time import time, sleep
from tr_num2words import tr_num2words
import constants


req_counter = 0
recusion_list = []


def main():
    word = input("Turkish Text: ")

    ultimates = ultimate_etymology(etymology(word))
    if ultimates:
        stats = {}
        print("Substems:")
        for stem in ultimates:
            for sub_stem in stem:
                print(f"\"{sub_stem['sub_stem']}\" is {sub_stem['ratio'] * 100 :.2f}% {sub_stem['etym']}")
                if sub_stem["etym"] in stats:
                    stats.update({sub_stem["etym"]: stats[sub_stem["etym"]] + sub_stem["ratio"]}) 
                else:
                    stats.update({sub_stem["etym"]: sub_stem["ratio"]}) 
        total = 0
        for lang in stats:
            total += stats[lang]
        print("-------------------------------------------")
        print("The phrase etymology is:")
        for lang in stats:
            print(f"{lang}: {stats[lang] / total * 100 :.2f}%")
    else:
        print("Etymology could not be found")

            



def wiktionary_titles(word):
    """
    (str) -> (int | None)
    Looks up any matching titles for 'word' in Wiktionary and fetches the corresponding page_id
    if no matching title is found then it returns none.
    """
    global req_counter

    url = constants.API_URL + "action=query&titles=" + word + "&format=json"

    req_session = requests.Session()
    req = req_session.get(url, headers=constants.REQ_HEADERS)

    req_counter += 1

    page_id = list(req.json()["query"]["pages"].keys())[0]

    if page_id != "-1":
        return page_id


def wiktionary_parse(page_id, lang="Turkish"):
    """
    (int) -> (str | None)
    Returns html source code of the page corresponding to page_id and particular
    language in case more than one is present in page.
    if page_id = None i.e. there is no such page, it returns None.
    if page_id exists but the page doesn't have lang language, then it returns none.
    """
    global req_counter

    if page_id:
        url = constants.API_URL + "action=parse&pageid=" + page_id + "&format=json"

        req_session = requests.Session()
        req = req_session.get(url, headers=constants.REQ_HEADERS)

        req_counter += 1

        soup = req.json()["parse"]["text"]["*"]
        start_i = soup.find(f'<h2><span class="mw-headline" id="{lang}"')
        if start_i != -1:
            end_i = soup[start_i+5:].find('<h2><span class="mw-headline" id=')
            if end_i != -1:
                return soup[start_i:start_i+end_i-3]
            else:
                return soup[start_i:]


def wiktionary_search(word):
    """
    (str) -> (list | None)
    Performs an exact search of Wiktionary for word.
    If there are matches, it returns a list of the match titles.
    Else, it returns None
    """
    global req_counter

    url = constants.API_URL + "action=query&list=search&srsearch=\"" + tr_lower(word) + "\"" + "&format=json"

    req_session = requests.Session()
    req = req_session.get(url, headers=constants.REQ_HEADERS)
    soup = req.json()

    req_counter += 1

    results_list = soup["query"]["search"]
    if results_list:
        results = []
        for result in results_list:
            results.append(result["title"])
        return results


def scrape_etym(word, soup = "", lang="Turkish", lang_suffix="tr", prev_call="", prev_call2="", call_type="all"):
    """
    (str) -> (list | None)
    Returns a list of etymologies in order of occurrence corresponding to the word
    and in the selected language
    if no etymology is found, then it returns None
    """
    if word not in constants.SUFFIXES:
        if soup:
            parsed_etym_list = etym_parse(soup)
        else:
            parsed_etym_list = etym_parse(wiktionary_parse(wiktionary_titles(word), lang))

        if parsed_etym_list:
            etym_list = []
            for parsed_etym in parsed_etym_list:
                # collect ultimate etymologies
                soup = BeautifulSoup(parsed_etym, "html.parser")
                tags = soup.find_all("span", class_="etyl")
                for tag in tags:
                    rank = get_rank(soup, tag.string)
                    if rank != ["cog"] and "calq" not in rank:
                        etym_list.append({"sub_stem": word, "etym": tag.string, "rank": rank, "search_lang": lang, "prev_call": prev_call, "prev_call2": prev_call2})
                        if tag.string == "Ottoman Turkish":
                            if call_type == "all":
                                ota_etym_list = get_ota_etyms(word, soup)
                                if ota_etym_list:
                                    for etym in ota_etym_list:
                                        etym_list.append(etym)

                # collect redirectional etymologies
                if call_type in ["all", "redirect1"]:
                    tags = soup.find_all("i", class_="Latn mention")
                    if tags:
                        for tag in tags:
                            if tag.has_attr('lang'):
                                if tag.attrs["lang"] == lang_suffix:
                                    a_tags = tag.find_all("a")
                                    for a_tag in a_tags:
                                        if a_tag.attrs["title"] != prev_call:
                                            if call_type == "all":
                                                redirect_etym_list = scrape_etym(a_tag.attrs["title"], lang=lang, lang_suffix=lang_suffix, prev_call=word, call_type="redirect1")
                                                if redirect_etym_list:
                                                    for etym in redirect_etym_list:
                                                        etym_list.append(etym)
                                            if call_type == "redirect1":
                                                redirect_etym_list = scrape_etym(a_tag.attrs["title"], lang=lang, lang_suffix=lang_suffix, prev_call=word, prev_call2=prev_call, call_type="redirect2")
                                                if redirect_etym_list:
                                                    for etym in redirect_etym_list:
                                                        etym_list.append(etym)



            return etym_list


def get_rank(soup, etym_lang):
    tags = soup.find_all("p")
    text = ""
    for tag in tags:
        text = text + tag.text

    rank = []
    sents = text.split(".")
    for sent in sents:
        if sent.strip().find("From") != -1:
            from_sent = sent.strip()
            if etym_lang in from_sent:
                rank.append("from")
        if sent.strip().find("Cognate") != -1:
            cog_sent = sent.strip()
            if etym_lang in cog_sent:
                rank.append("cog")

    calq_matches = re.findall(r"calque of [^\s]+ [^\s]+ [^\s]+", text)
    if calq_matches:
        for calq_match in calq_matches:
            if etym_lang in calq_match:
                rank.append("calq")

    if "reform" in text.lower() or "replaced" in text.lower() or "displaced" in text.lower():
        rank.append("reform")


    return rank


def get_ota_etyms(word, soup="", lang="Turkish", lang_suffix="tr", prev_call="", call_type="all"):
    ota_tags = soup.find_all("i", class_="ota-Arab mention")
    if ota_tags:
        for ota_tag in ota_tags:
            if ota_tag.has_attr("lang"):
                if ota_tag.attrs["lang"] == "ota":
                    ota_a_tags = ota_tag.find_all("a")
                    for ota_a_tag in ota_a_tags:
                        if ota_a_tag.attrs["title"] != prev_call:
                            ota_etym_list = scrape_etym(ota_a_tag.attrs["title"], lang="Ottoman_Turkish", lang_suffix="ota", prev_call=word, call_type="ota")
                    return ota_etym_list


def etym_parse(soup):
    """
    (str) -> (list | None)
    soup: html source code (of page_id)
    returns a list of etymologies source code in the soup
    if soup is None, then it returns None
    if soup does not contain etymologies, then it returns None
    """

    # check if soup is not none
    if soup:
        # check if there is etymology in soup
        if soup.find('<h3><span class="mw-headline" id="Etymology') != -1:

            # get the end index of the last etymology
            start_i = soup.rfind('<h3><span class="mw-headline" id="Etymology')
            if soup[start_i+5:].find('<h3><span class="mw-headline" id=') != -1:
                end_i = soup[start_i+5:].find('<h3><span class="mw-headline" id=') + start_i + 4
            else:
                end_i = len(soup) - 1

            # get the start index of the first etymology
            start_i = soup.find('<h3><span class="mw-headline" id="Etymology')

            etym_soup = soup[start_i:end_i]

            etyms = etym_soup.split("<h3>")
            parsed_etym_list = []
            for etym in etyms:
                if etym:
                    parsed_etym_list.append("<h3>" + etym)

            return parsed_etym_list


def wiktionary_stemmer(word, lang="Turkish", lang_suffix="tr", prev_call=""):
    """
    (str) -> (list | None)
    An etymological stemmer that returns a list of dictionaries containing the 'longest' stem
    whose page has an etymology in wiktionary, and the html source code for the page of stem.
    if it fails to find a matching stem, it returns None.
    """
    # initialize values
    global recusion_list
    stems = []
    if word.lower() in constants.mi_particles:
        word = "mı"
    if word.lower() == "ord":
        word = "o"

    # check if word has a title in wiktionary
    word_page_id = wiktionary_titles(word)
    if word_page_id:
        # get the soup of page
        word_soup = wiktionary_parse(word_page_id, lang)
        # check if page has an etymology
        if word_soup:
            if etym_exists(word_soup):
                stems.append({"stem": word, "soup": word_soup})
                if stems:
                    return stems
            else:   # if word has title but doesn't have etymology
                # check for link definitions
                soup = BeautifulSoup(word_soup, "html.parser")
                def_tags = soup.find_all("span", class_="form-of-definition-link")
                if def_tags:
                    # retrive title for defintion
                    for def_tag in def_tags:
                        i_tags = def_tag.find_all("i", class_="Latn mention")
                        if i_tags:
                            for i_tag in i_tags:
                                if i_tag.has_attr("lang"):
                                    if i_tag.attrs["lang"] == lang_suffix:
                                        a_tags = i_tag.find_all("a")
                                        if a_tags:
                                            for a_tag in a_tags:
                                                # call wiktionary_stemmer(def_title) and return results (if any) recursively
                                                if a_tag.has_attr("title"):
                                                    titles = a_tag.attrs["title"].replace(f"w:{lang_suffix}:", "").split()
                                                    if titles:
                                                        if len(titles) == 1:
                                                            if titles[0] != prev_call:
                                                                return wiktionary_stemmer(titles[0], lang=lang, lang_suffix=lang_suffix, prev_call=word)
                                                        else:
                                                            for title in titles:
                                                                if title not in recusion_list:
                                                                    recusion_list.append(title)
                                                                    stem = etym_stemmer(title, lang=lang, lang_suffix=lang_suffix, prev_call=word)
                                                                    if stem:
                                                                        for s in stem:
                                                                            stems.append(s)
                                                            recusion_list = []

                                                            if stems:
                                                                return stems

    # if word doesn't have a title
    # perform an exact search of wiktionary
    search_titles = wiktionary_search(word)
    # if there are results, sift through them for a match in word count and minimal stem
    if search_titles:
        for search_title in search_titles:
            if len(search_title.split()) == len(word.split()):
                if tr_lower(search_title[0:2]) == tr_lower(word[0:2]):
                    if has_lang(search_title, lang):              # not too necessary but...
                            # if a match is found call wiktionary_stemmer(title) recursively and return
                            if search_title != prev_call and search_title != word:
                                return wiktionary_stemmer(search_title, lang=lang, lang_suffix=lang_suffix, prev_call=word)


def etym_exists(soup):
    """
    (str) -> (True | None)
    Checks if the soup contains at least one etymology
    """
    if soup.find('<h3><span class="mw-headline" id="Etymology') != -1:
        return True


def has_lang(title, lang="Turkish"):
    """
    (str) -> (True | None)
    checks if the page of 'title' has the 'lang' language
    """
    page_id = wiktionary_titles(title)
    if page_id:
        if wiktionary_parse(page_id, lang):
            return True


def etym_stemmer(word, lang="Turkish", lang_suffix="tr", prev_call=""):
    """
    (str) -> (list | None)
    An etymological stemmer that returns a list of dictionaries containing the 'longest' stem
    whose page has an etymology in wiktionary, and the html source code for the page of stem.
    if it fails to find a matching stem, it returns None.
    """
    # check if stem can be retrieved from word itself using wiktionary_stemmer
    stem = wiktionary_stemmer(word, lang, lang_suffix, prev_call=prev_call)
    if stem:
        return stem

    # if word is in all caps try the lower
    if word.isupper():
        stem = wiktionary_stemmer(tr_lower(word), lang, lang_suffix, prev_call=prev_call)
        if stem:
            return stem

    # apply tr_stemmer and check the result using wiktionary_stemmer
    # if fails, repeat until tr_stemmer can stem no further
    tr_stemmer = TurkishStemmer()
    temp_word = word
    while True:
        stemmed_word = tr_stemmer.stem(temp_word)
        if stemmed_word == temp_word:
            break

        stem = wiktionary_stemmer(stemmed_word, lang, lang_suffix, prev_call=prev_call)
        if stem:
            return stem

        temp_word = stemmed_word

    # apply brute stemming algorithm in tandem with wiktionary_stemmer
    if has_suffix(word):
        while True:
            if len(word) > 2:
                word = word[0:len(word)-1]
                stem = wiktionary_stemmer(word, lang, lang_suffix, prev_call=prev_call)
                if stem:
                    return stem
            else:
                break


def has_suffix(word):
    for i in range(len(constants.SUFFIXES)):
        if word.endswith(constants.SUFFIXES[i][1:]):
            return True


def etymology(phrase, lang="Turkish", lang_suffix="tr"):
    """
    (str) -> (dict | None)
    Returns a dictionary containing the 'phrase' and a list of dictionaries containing
    the stems of phrase words and their respective etymologies.
    If no etymology is found, then it returns None
    """
    if phrase:
        # convert query phrase into a list of words free of non-alphanumeric characters
        phrase_words = re.sub(r"[^0-9A-Za-zİIıÖöÜüÇçŞşĞğÂâÊêÎîÔôÛû']", " ", phrase).split()
        word_list = []
        for phrase_word in phrase_words:
            if phrase_word:
                if "'" in phrase_word: # remove single quotes and suffix
                    phrase_word = re.sub(r"^'", "", phrase_word)
                    phrase_word = re.sub(r"'$", "", phrase_word)
                    phrase_word = re.sub(r"'.+", "", phrase_word)

                if phrase_word.isdigit(): # if a phrase word is a number, convert it to a list of words
                    phrase_word_list = tr_num2words(phrase_word)
                    for word in phrase_word_list:
                        word_list.append(word)
                else:
                    word_list.append(phrase_word)

        # collect etymologies list
        etym_list = []
        # stem every phrase word
        for word in word_list:
            if len(word) > 1 or word.lower() == "o": # stem only if the word has more than one char
                stems = etym_stemmer(word)
                # find the etymology of each stem
                if stems:
                    for stem in stems:
                        etym = scrape_etym(stem["stem"], soup=stem["soup"], lang=lang, lang_suffix=lang_suffix)
                        # if an etymology exists, add it to the list of etymologies
                        if etym:
                            etym_list.append({"stem": stem["stem"], "etym": etym})
                        else:
                            etym = et_etymology(stem["stem"])
                            if etym:
                                etym_list.append({"stem": stem["stem"], "etym": etym})
                            else:
                                etym = et_etymology(word)
                                if etym:
                                    etym_list.append({"stem": word, "etym": etym})
                else:
                    etym = et_etymology(word)
                    if etym:
                        etym_list.append({"stem": word, "etym": etym})

        # return the list of etymologies
        if etym_list:
            return {"phrase": phrase, "etymology": etym_list}


def ultimate_etymology(etymology, lang="Turkish"):
    if etymology:
        ultimate_etyms = []
        # analyze every stem in etymology
        for stem in etymology["etymology"]:

            # create a list of main sub_stems for each stem
            sub_stems = []
            sub_stems_list = []
            for sub_stem in stem["etym"]:
                sub_stems.append(sub_stem["sub_stem"])
            sub_stems = list(dict.fromkeys(sub_stems))
            for sub_stem in sub_stems:
                temp_list = [sub for sub in stem["etym"] if (sub["sub_stem"] == sub_stem) or sub_stem in [sub["prev_call"], sub["prev_call2"]]]
                ex_sub_stems = [sub for sub in sub_stems if sub != sub_stem]
                temp_list = [sub for sub in temp_list if sub["prev_call"] not in ex_sub_stems and sub["prev_call2"] not in ex_sub_stems]
                if temp_list:
                    sub_stems_list.append({"sub_stem": sub_stem, "sub_sub_stems": temp_list})

            # get the ultimate etym of each main sub_stem
            for sub_stem in sub_stems_list:
                # get the reform ranks of the main_sub_stem
                reform_ranks = [sub["rank"] for sub in sub_stem["sub_sub_stems"] if "reform" in sub["rank"]]

                # get the etyms in main sub_stem
                sub_stem_etyms = list(dict.fromkeys([sub["etym"] for sub in sub_stem["sub_sub_stems"] if sub["etym"] != "Ottoman Turkish" and sub["search_lang"] == lang]))
                if sub_stem_etyms == []:
                    sub_stem_etyms = list(dict.fromkeys([sub["etym"] for sub in sub_stem["sub_sub_stems"]]))
                # analyze the etyms list of the main sub_stem
                ultimate_sub_stem_etym = analyze_etyms_list(sub_stem["sub_stem"], sub_stem_etyms, reform_ranks, len(sub_stems_list))
                ultimate_etyms.append(ultimate_sub_stem_etym)

        return ultimate_etyms


def analyze_etyms_list(sub_stem, sub_stem_etyms, reform_ranks, num_sub_stems, call_type="all"):
    # check if all etyms are turkic
    if is_turkic(sub_stem_etyms):
        return [{"sub_stem": sub_stem, "etym": "Turkic", "ratio": 1/num_sub_stems}]

    # non-tutkic etyms exist
    else:
        # check if there is only one etym
        if len(sub_stem_etyms) == 1:
            return [{"sub_stem": sub_stem, "etym": sub_stem_etyms[0], "ratio": 1/num_sub_stems}]

        # more than one etym exists and they conflict
        if call_type == "all":
            etym = scrape_et_etym(sub_stem)
            if etym:
                return [{"sub_stem": sub_stem, "etym": etym, "ratio": 1/num_sub_stems}]

            if reform_ranks:
                sub_stem_etyms = [etym for etym in sub_stem_etyms if etym not in ["Arabic", "Persian", "Classical Persian"]]
                ultimate = analyze_etyms_list(sub_stem, sub_stem_etyms, None, num_sub_stems, call_type="reform")
                if ultimate:
                    return ultimate

        ultimeate_etyms = []

        turkic_etyms = [etym for etym in sub_stem_etyms if is_turkic([etym])]
        if turkic_etyms:
            ultimeate_etyms.append({"sub_stem": sub_stem, "etym": "Turkic", "ratio": len(turkic_etyms)/len(sub_stem_etyms)/num_sub_stems})

        non_turkic_etyms = [etym for etym in sub_stem_etyms if not is_turkic([etym])]
        for etym in non_turkic_etyms:
            ultimeate_etyms.append({"sub_stem": sub_stem, "etym": etym, "ratio": 1/len(sub_stem_etyms)/num_sub_stems})

        return ultimeate_etyms


def is_turkic(etyms_list):
    for etym in etyms_list:
        if (etym not in constants.TURKIC_LANGS) and ((etym + " language") not in constants.TURKIC_LANGS) and ((etym + " languages") not in constants.TURKIC_LANGS):
            return False
    return True


def tr_lower(word):
    if "İ" in word:
        word = word.replace("İ", "I")
        return word.lower()
    else:
        return word.lower()


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


# diagnostics
def completion_time(start_time):
    duration = time() - start_time
    if duration < 60:
        print(f"Done in {duration :.2f} seconds")
        print("Number of requests:", req_counter)
    elif 60 <= duration < 3600:
        print(f"Done in {duration/60 :.2f} minutes")
        print("Number of requests:", req_counter)
    else:
        print(f"Done in {duration/3600 :.2f} hours")
        print("Number of requests:", req_counter)


def save_soup(soup, filename="soup.html"):
    with open(filename, "a") as file:
        file.truncate(0)
        file.seek(0)
        for line in soup:
            file.write(str(line))


# call main()
if __name__ == "__main__":
    main()
