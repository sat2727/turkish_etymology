from etymology import etymology, ultimate_etymology
import os
from time import time
import sys
import re

def main():
    try:
        sample_analyzer("example1.txt")
    except KeyboardInterrupt:
        print("\nSession saved")


def sample_analyzer(sample_filename, restore = True):

    # initialize values
    sample_words = convert_file_to_words(sample_filename)
    num_words = len(sample_words)
    # restore previous session
    if restore:
        print("Restoring previous session...")
        session_values = restore_session(sample_filename)
        if session_values:
            stats = session_values[0]
            i = session_values[1]
            prev_session_time = session_values[2]

            if i == num_words:
                sys.exit(f"All words in file have already been analyzed. Check the stats file.")
            else:
                input("Session restored successfully. Press 'Return' to continue.")

        else:
            print("Could not find a matching previous session. Starting a fresh one.")
            input("Press 'Return' to contuinue")
            i = 0
            stats = {}
            prev_session_time = 0
            filename = re.search(r"[^\.]+", sample_filename).group(0)
            clear_file(f"{filename}_no_etym_log.txt")
            
    else: 
        i = 0
        stats = {}
        prev_session_time = 0
        filename = re.search(r"[^\.]+", sample_filename).group(0)
        clear_file(f"{filename}_no_etym_log.txt")
         

    start_time = time()
    duration = prev_session_time + time() - start_time

    # Sample analysis
    while i < num_words:
        # display messages
        os.system("clear")
        print(f"Analyzing the etymology of \"{sample_words[i]}\"...")
        print(f"Total progress: {i / num_words * 100 :.2f}%")
        elapsed_time(duration)
        if duration != 0:
            print(f"Speed: {i/duration*3600 :.2f} words/h")

        # etymology analysis of word
        etym = etymology(sample_words[i])
        if etym:
            ultimates = ultimate_etymology(etym)
            if ultimates:
                for stem in ultimates:
                    for sub_stem in stem:
                        # update stats for etym
                        if sub_stem["etym"] in stats:
                            stats.update({sub_stem["etym"]: stats[sub_stem["etym"]] + sub_stem["ratio"]}) 
                        else:
                            stats.update({sub_stem["etym"]: sub_stem["ratio"]}) 
            else: # update stats for no-ultimate failure
                if "no_ultimate" in stats:
                    stats.update({"no_ultimate": stats["no_ultimate"] + 1}) 
                else:
                    stats.update({"no_ultimate": 1})

        else: # update stats for no-etym failure
            if "no_etym" in stats:
                stats.update({"no_etym": stats["no_etym"] + 1}) 
            else:
                stats.update({"no_etym": 1}) 
            save_no_etym_log(sample_words[i], sample_filename)
                               
       
        # increment i
        i += 1

        # save progress and stats
        duration = prev_session_time + time() - start_time
        save_stats(sample_filename, stats, i, duration)    

    # end of analysis
    os.system("clear")

    print("Analysis complete. Stats:")
    for lang in stats:
        print(f"{lang}: {stats[lang]/i*100 :.2f}%")

    elapsed_time(duration)

    print(f"Speed: {i/duration*3600 :.2f} words/h")
    
    
def save_stats(filename, stats, i, duration):
    filename = re.search(r"[^\.]+", filename).group(0)
    try:
        with open(f"{filename}_stats.csv", "w") as file:
            for lang in stats:
                file.write(f"{lang},{stats[lang]}\n")
            
            file.write(f"total,{i}\n")
            file.write(f"elapsed_time,{duration}")
    except:
        sys.exit("Failed to save stats. exiting...")


def save_no_etym_log(word, filename):
    filename = re.search(r"[^\.]+", filename).group(0)

    with open(f"{filename}_no_etym_log.txt", "a") as file:
        file.write(word + "\n")
    

def clear_file(filename):
    with open(filename, "w") as file:
        file.truncate(0)
        file.seek(0)


def restore_session(filename):
    filename = re.search(r"[^\.]+", filename).group(0)
    try:
        with open(f"{filename}_stats.csv", "r") as file:
            stats = {}
            for line in file:
                values = line.strip().split(",")
                if values[0] not in ["total", "elapsed_time"]:
                    stats.update({values[0]: float(values[1])})
                elif values[0] == "total":
                    i = int(values[1])
                else:
                    duration = float(values[1])

        return [stats, i, duration]
        
    except FileNotFoundError:
        pass
    
    


def convert_file_to_words(filename):
    words = []
    
    try:
        with open(filename, "r") as file:
            for line in file:
                line_words = line.split()
                for word in line_words:
                    words.append(word)
    except FileNotFoundError:
        sys.exit("Sample file not found!")
    
    return words


def elapsed_time(duration):
    if duration < 60:
        print(f"Elapsed time: {duration :.2f} seconds")
    elif 60 <= duration < 3600:
        print(f"Elapsed time: {duration/60 :.2f} minutes")
    else:
        print(f"Elapsed time: {duration/3600 :.2f} hours")


def display_stats(stats, num_words):
    for lang in stats:
        print(f"{lang}: {stats[lang]/num_words*100 :.2f}%")


if __name__ == "__main__":
    main()