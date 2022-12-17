# Turkish Etymology

## **Description:**
A tool that retrieves the ultimate etymological origins of Turkish words, primarily using Wiktionary.org. The main focus of the project is modern Turkish of Turkey (*Türkiye Türkçesi*), although the script can be adapted for other Turkic and non-Turkic languages.

## **Background**:
Given the history of modern Turkish and the reform it has undergone since 1928, the etymology of Turkish words can be a complicated, and even controversial, topic. That's why I felt the need to create a tool that automates the process of determining the ultimate etymology of Turkish words, and helps in analyzing the occurrence frequency of Turkic and non-Turkic words in text samples.
In order to accomplish this goal, the program performs two main tasks:
- Finding the longest possible etymological stem of the word that retains the semantics.
- Determining the ultimate etymology of the stem.

## **Stemming Algorithm:**
The stemming is handled using the `wiktionary_stemmer` and `etym_stemmer` functions.
### **wiktionary_stemmer:**
An etymological stemmer that returns a list of dictionaries each containing a stem that has an "Etymology" entry in the target language in Wiktionary.org, and the html source code for that page in Wiktionary (referred to as `soup`). Typically, there will be only one dictionary in the list, but in special cases like abbreviations, each word in the abbreviation will have a dictionary containing the corresponding stem and soup.<br>
If no such stem can be found, the function returns `None`.
#### **Usage:**
```
>>> wiktionary_stemmer('oluyor')
[{'stem': 'olmak', 'soup': soup}]
```
```
>>> wiktionary_stemmer('ABD')
[{'stem': 'Amerika', 'soup': soup1}, {'stem': 'birleşmek', 'soup': soup2}, {'stem': devlet, 'soup': soup3}]
```
#### **How it works:**
- if the input word has a page in Wiktionary and it has an Etymology entry, then the word itself is returned as the stem along with the page soup.
- if the input word has a page in Wiktionary but it doesn't have an Etymology entry, then the page is scanned for *"link definitions"* that share a minimal stem with the input word, and those in turn are investigated recursively.
- if the input word doesn't have a page in Wiktionary, an exact search of the word is conducted in Wiktionary. Then the results that contain the input word and share a minimal stem are investigated recursively.
- if all of the above fails, the function returns `None`. 
### **etym_stemmer:**
An etymological stemmer that combines `wiktionary_stemmer` with `TurkishStemmer` and a brute stemming method.<br>
The output is in the same format as that of `wiktionary_stemmer`.
#### **Usage:**
```
>>> etym_stemmer('olduğumuzunun')
[{'stem': 'olmak', 'soup': soup}]
```
#### **How it works:**
- The input word itself is checked using `wiktionary_stemmer`
- If the above returns `None`, then [TurkishStemmer](https://github.com/otuncelli/turkish-stemmer-python) is used to stem the word. Then the stemmed word is checked using `wiktionary_stemmer`. If the previous step returns `None`, the process is repeated until `TurkishStemmer` can stem no further.<br>
Unfortunately, due to `TurkishStemmer`'s shortcomings, especially when it comes to removing derivational suffixes, the next brute stemming technique is sometimes necessary.
- If the word ends in one of the `SUFFIXES` defined in the `constants.py` file, the word is stemmed one letter at a time, and checked using `wiktionary_stemmer`. The process is repeated until the word has only two letters, which is the smallest possible stem in Turkish.
- If all of the above fails, the function returns `None`.

## **Etymology Scraping:**
### **etymology Function:**
The `etymology` function can have any chunk of text, be it a single word or a paragraph, as its input. The function then prepares for stemming and scrapping as follows:
- Punctuation is removed, and the input string is split into a list of word(s).
- Single quotes/apostrophes and the suffixes that might follow them are also removed.
- If a word is a  number, it's converted into words using the `tr_num2words` function contained in the `tr_num2words.py` file. The function uses [num2words](https://pypi.org/project/num2words/) to output Turkish numbers as separate words with some additional features.
- Each word is then stemmed using `etym_stemmer` and its etymology is scraped using the `scrape_etym` function.
- The `etymology` function returns a dictionary containing the input `phrase` and an `etymology` list containing the etymology languages of each `stem` found in the input.
- The function returns `None` if no etymology is found.
### **scrape_etym:**
The `scrape_etym` function scrapes etymology languages from the html source code of the Wiktionary page corresponding to the stem of the input word found through `etym_stemmer`. The function uses [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) to retrieve the desired data.<br>
Each scraped etymology language is assigned a `rank` value as follows:
- "from" for ancestral languages
- "reform" in case a word has been replaced or displaced by another word of different origin
- "cog" for cognations
- "calq" for calques
- `None` otherwise

Cognations and calques are dropped and everything else is collected.

If the word has an etymological root word in the target language mentioned in the "Etymology" entry, then that word is investigated, and the etymological languages mentioned in its page are collected recursively up to two levels of redirection. Also, Ottoman Turkish ancestral words are always investigated up to one level of recursion.<br>

`scrape_etym` returns a list of dictionaries, each containing a substem, its etymological language along with its rank, and what substems were investigated in recursive calls that led to its collection, if any.<br>
The function returns `None` if no etymological language or redirectional root is found in the "Etymology" entry.

## **Ultimate Etymology Analysis:**
The `ultimate_etymology` function determines the ultimate origin languages of the word and their ratios in its etymological makeup, based on the scraped data passed on by the `etymology` function.<br>
The function returns a list of lists, each of which represents a stem and contains dictionaries representing the main substems of each stem, which in turn contain the etymology language and its ratio.
#### **Usage:**
```
>>> ultimate_etymology(etymology("olunca"))
[[{'sub_stem': 'olmak', 'etym': 'Turkic', 'ratio': 1.0}]]
```
```
>>> ultimate_etymology(etymology("kaydediyor"))
[[{'sub_stem': 'kayıt', 'etym': 'Arabic', 'ratio': 0.5}], [{'sub_stem': 'etmek', 'etym': 'Turkic', 'ratio': 0.5}]]
```
```
>>> ultimate_etymology(etymology("1052"))
[[{'sub_stem': 'bin', 'etym': 'Turkic', 'ratio': 1.0}], [{'sub_stem': 'elli', 'etym': 'Turkic', 'ratio': 1.0}], [{'sub_stem': 'iki', 'etym': 'Turkic', 'ratio': 1.0}]]
```
#### **How it works:**
- The function iterates over every stem passed on by the `etymology` function.
- The etymology data is filtered to obtain a list of main substems for each stem. A main substem is a direct component of the stem that's not a result of redirectional etymology scraping.
- The etymology languages of each substem are compiled into a list.
- The ultimate etymologies of each main substem is then determined using the `analyze_etyms_list` function.

#### **analyze_etyms_list:**
This function analyzes the etymological languages of a substem and determines its ultimate origin as follows:
- If there is no conflict in the etymological languages, then the ultimate etymology is determined and the ratio is assigned.
- If there is a conflict, however, an attempt at a resolution is made by scraping the etymology from another resource [EtimolojiTürkçe](https://www.etimolojiturkce.com/) using the `scrape_et_etym` function. This resource is also used when an etymology cannot be found using Wiktionary.
- If there are reform-ranked languages, then the displaced languages(namely, Arabic and Persian) are removed, and the function is called recursively using the updated list of etymological languages.
- Finally, the ultimate etymology languages are returned along with their assigned ratios.

## **sample_analyzer:**
A simple tool contained in the `sample_analyzer.py` file that iterates over the words in a text file, determines the ultimate etymology language of each word, adds up etymology ratios of each language, and outputs the results in a CSV file. The tool also allows restoring a previous session and resumes analysis from the session data. 
### **Example:**
A sample containing the 1000 most frequently used Turkish words according to [this](https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/Turkish) Wikipedia page was analyzed and the results can be seen in [this spreadsheet](https://docs.google.com/spreadsheets/d/19C5a7fc2nqcikygglZepw32lT3yjjkkL/edit?usp=sharing&ouid=118351046651538547295&rtpof=true&sd=true).

