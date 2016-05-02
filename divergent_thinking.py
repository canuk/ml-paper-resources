explanation = """
Guilford's Divergent Thinking test (DT)
Creativity in the DT test is assessed as follows:

 ORIGINALITY 
 * Unusual questions across all questions score 1, unique questions score 2.

 FLUENCY 
 * The number of questions.

 FLEXIBILITY 
 * The number of different categories of questions.

 ELABORATION
 * The amount of detail.
 * * For example, "break door" = 0 and "break door with a crowbar" = 1.

Originality - each response it compared to the total amount of responses from all of the people you gave the test to. Reponses that were given by only 5% of your group are unusual (1 point), responses that were given by only 1% of your group are unique - 2 points). Total all the point. Higher scores indicate creativity*
Fluency - total. Just add up all the responses. In this example it is 6.
Flexibility - or different categories. In this case there are five different categories (weapon and hit sister are from the same general idea of weapon)
Elaboration - amount of detail (for Example "a doorstop" = 0 whereas "a door stop to prevent a door slamming shut in a strong wind" = 2 (one for explanation of door slamming, two for further detail about the wind).
*You might have noticed that the higher fluency the higher the originality (if you did "good for you!") This is a contamination problem and can be corrected by using a corrective calculation for originality (originality = originality/fluency).


NOTE: This is a modified version of a script found in the following paper:
De Smedt, T. (2013). Modeling Creativity. University Press Antwerp.
"""
import csv
from pattern.en import parsetree 
from pattern.vector import Vector, count, words
from pattern.vector import hierarchical, distance, centroid 
from pattern.metrics import avg
import requests
from requests.auth import HTTPBasicAuth
import json

fine_categorize_classifier_id = ""

classifier_uri = 'https://gateway.watsonplatform.net/natural-language-classifier/api/v1/classifiers/'
classifier_uri += fine_categorize_classifier_id
classifier_uri += "/classify?text="

watson_user = ''
watson_pass = ''

with open('dt_score-ask2.csv', 'wb') as csvfile:
    dt_writer = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    dt_writer.writerow(['name', 'originality', 'fluency', 'flexibility', 'flex2', 'elaboration'])
                            
    with open('questions-ask2.csv', 'rb') as csvfile:
        questions = csv.reader(csvfile, delimiter=',', quotechar='"')
        next(questions, None)  # skip the headers
        all_questions = list(questions)

        # remove nulls
        all_q = []
        for row in all_questions:
            row = filter(None, row)
            all_q.append(row)

        for row in all_q:
            row = filter(None, row)  #remove nulls
    
            def fluency(questions):
                return len(questions)
            
            def elaboration(questions):
                return sum(min(len(parsetree(a)[0].pnp), 2) for a in questions)
                
            def variance(cluster):
                return avg([distance(centroid(cluster), v) for v in cluster])
    
            vectors = []
                
            for q in all_q:
                v = count(words(q), stemmer='lemma') 
                v = Vector(v)
                vectors.append(v)
                
            clusters = hierarchical(vectors, k=250, distance='cosine')
            clusters = [isinstance(v, Vector) and [v] or v.flatten() for v in clusters] 
            clusters = sorted(clusters, key=variance)
            
            categories = {}
            
            for i, cluster in enumerate(clusters):
                for v in cluster: 
                    categories[row[vectors.index(v)]] = i

            def flex(questions):
                ml_categories = []
                for q in questions:
                    q_uri = classifier_uri + q
                    j = requests.get(q_uri, auth=(watson_user, watson_pass))
                    ml_categories.append(j.json()['top_class'])
                print ml_categories
                return len(set(ml_categories))
                    
            def flexibility(questions):
                return len(set(categories.get(a, a) for a in questions))
                
            p = {}
            for c in categories.values():	
                p.setdefault(c, 0.0)
                p[c] += 1
            s = sum(p.values()) 
            for c in p:
                p[c] /= s
                
            def originality(questions): 
                originality = 0
                for a in questions:
                    if p.get(categories.get(a, a), 0) < 0.01: 
                        originality += 1
                    if p.get(categories.get(a, a), 0) < 0.05: 
                        originality += 1
                return originality / (float(fluency(questions)) or 1)
               
            ori = originality(row)
            flu = fluency(row)
            fle = flexibility(row)
            flex = flex(row)
            # flex = -1
            ela = elaboration(row)
            dt_writer.writerow([row[1], ori, flu, fle, flex, ela])
            print row[1]
            print "Originality: %f" % ori
            print "Fluency: %i" % flu
            print "Flexibility: %i" % fle
            print "Flex: %i" % flex
            print "Elaboration: %i" % ela