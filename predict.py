import requests
import json
import lxml
from io import StringIO
import time

import lxml.html as html
s = requests.Session()
from pprint import pformat

def get_profile(name):
  r = s.get('https://www.tennisexplorer.com/res/ajax/search.php?s='+name+'&t=p&c=&_=1594398240340')
  return json.loads(r.text)["links"][0]

def get_profile_data(profile):
  r = s.get("https://www.tennisexplorer.com/player/"+profile["url"])
  return r.tex

def kelly_crit(win_p, odds):
  return (win_p - (1-p/ odds))


def played_matches(profile, year, data=None):
  r = s.get("http://www.tennisexplorer.com/player/"+profile["url"]+"/?annual="+str(year))
  h = html.fromstring(r.text)

  #print(h)

  parse = True
  card = profile
  if not "courts" in profile.keys():
    card["matches"] = []
    card["courts"] = {
        "Clay":{
        "Wins":0,
        "Loss":0
      },
      "Hard":{
        "Wins":0,
        "Loss":0
      },
      "Indoors":{
        "Wins":0,
        "Loss":0
      },
      "Grass":{
        "Wins":0,
        "Loss":0
      },
      "Total":{
        "Wins":0,
        "Loss":0
      }
    }

    details = h.cssselect(".plDetail td")[-1]
    attr = details.cssselect(".date")
    for a in attr:
       x = a.text.split(":")
       card[x[0]] = x[1]

    if card.get("Current/Highest rank - singles", None):
      card["Highest Rank"] = int(card.get("Current/Highest rank - singles").split("/")[-1].replace(".", ""))
      card["Current Rank"] = int(card.get("Current/Highest rank - singles").split("/")[0].replace(".", ""))


    courts = h.cssselect("#balMenu-1-data .balance tbody tr")
    indices = [
      ("Grass", -2),
      ("Indoors", -3),
      ("Hard", -4),
      ("Clay", -5),
      ("Total", -6)
      ]
    for row in courts:
      cells = row.cssselect("td")
      #print(row.cssselect("td")[-6])

      for i in indices:
        if len(cells) == 7 and len(list(cells[i[1]])) != 0 or i[1] == -6:
          if i[1] == -6:
            wl = cells[i[1]].text.split("/")
          else:
            wl = list(cells[i[1]])[0].text.split("/")
          wins = int(wl[0])
          loss = int(wl[1])
          card["courts"][i[0]]["Wins"] += wins
          card["courts"][i[0]]["Loss"] += loss

    for i in indices:
      divzero = (card["courts"][i[0]]["Wins"] + card["courts"][i[0]]["Loss"])
      if divzero > 0:
        card["courts"][i[0]]["W/L"] = 100*(card["courts"][i[0]]["Wins"] / (card["courts"][i[0]]["Wins"] + card["courts"][i[0]]["Loss"]))  
  #print(attributes)
  tables = h.cssselect("#matches-"+ str(year)+"-1-data .result.balance")

  if len(tables):
    locations = tables[-1].cssselect("tr.head")
    row = locations[0]
    while row:
      #print(list(row.classes))
      if "head" in row.classes:
        a = row.cssselect("a")
        if len(a) > 0:
          location =  a[0].get('href')
        else:
          location = row.text

        #print("Found Location"+ location)
        row = row.getnext()
        continue
      else:
        players = row.cssselect("tr .t-name a")
        for i, p in enumerate(players):
          ##rint("notU" in list(p.classes))

          if "notU" in list(p.classes):
            continue
          else:
            opponent = p
            break
        date = row.cssselect("tr .time")[0].text
        rnd = row.cssselect("tr .round")[0].text

        score_summary = row.cssselect("tr .tl a")[0].text
        stats = {
            "scores":[],
            "win":0,
        }
        if score_summary:

          sets = score_summary.split(',')
   
          for x in sets:
            points = x.split("-")
            #print(points)
            if len(points) > 1:
              loss = int(points.pop(i))
              wins = int(points[0])
              stats["scores"].append((wins, loss))

          dpoints = [int(win) - int(loss) for win,loss in stats["scores"]]
          win = sum(int(win) for win,loss in stats["scores"])
          loss = sum(int(loss) for win,loss in stats["scores"])
          stats["win_points"] = win
          stats["loss_points"] = loss
          stats["dpoints"] = dpoints

          if len(stats["dpoints"]) > 0:
            stats["avg_dpoints"] = sum(int(x) for x in stats["dpoints"])
          else:
            stats["avg_dpoints"] = 0

          if win > loss:
            stats["win"] = 1
          if loss > win:
            stats["win"] = -1

        match_url = row.cssselect("tr .tl a")[0].get("href")

        card["matches"].append({
          "location:":location,
          "date":date,
          "name":opponent.text,
          "link":opponent.get('href'),
          "match":match_url,
          "score":score_summary,
          "stats":stats,
          "score_index":i,
          "round":rnd
        })
      row = row.getnext()
  #print(pformat(card))
  return card



years = [
2020,
2019,
2018,
2017,
2016,
2015,
2014
]

def versus(p1, p2, p1c=False, return_obj=False):
  players = [p1, p2]
  names = []
  import grequests
  urls = []
  for i, year in enumerate(years): 
    if not p1c:
      time.sleep(1)
      p1 = played_matches(p1, year)
    time.sleep(1)
    p2 = played_matches(p2, year)

  for p in [p1, p2]:
    nms = []
    #print(p)
    for match in p["matches"]:
      nms.append(match["name"])
    names.append(nms)
  

  vs = {}
  similar = list(set(names[0]) & set(names[1]))
  sname1 = p1["name"].split(" ")[1] =  p1["name"].split(" ")[0].replace(",", "") +" "+ p1["name"].split(" ")[1][0]+'.'
  sname2 = p2["name"].split(" ")[1] = p2["name"].split(" ")[0].replace(",", "") +" "+p2["name"].split(" ")[1][0]+'.'

  similar +=[sname1,sname2]

  #print(similar)
  blacklist = []
  for card in [p1, p2]:
    for s in similar:
      for match in card["matches"]:
        if match["name"] == s:
          if not vs.get(s, None):
            vs[s] = {}

          if not vs[s].get(card["name"], None):
            vs[s][card["name"]] = []

          if match["score"] == None:
            continue
          data = (match["stats"]["win"], match["score"], match["stats"].get("dpoints", [0]), match["stats"].get("avg_dpoints", 0))
          print(data)
          if len(match["stats"]["dpoints"]) > 2:
            blacklist.append(data)

          if not data in blacklist and not data in vs[s][card["name"]]:
            vs[s][card["name"]].append(data)
          else:
            vs[s][card["name"]].append((0, 0, 0, 0))
  #print(pformat(vs))
  p1_scores = []
  p2_scores = []
  p1_result = 0
  p2_result = 0
  p1_total = 1
  p2_total = 1
  p3_result = 0
  p1_max = 0
  p2_max = 0
  p1_sum = 0
  p2_sum = 0
  p1_count = 0
  p2_count = 0
  p1_win = 0
  p1_lose = 0
  p2_win = 0
  p2_lose = 0

  for k, v in vs.items():
    #print(print(x[-1] for x in v[p1["name"]]))
    #p1_scores += [x[-1] for x in v[p1["name"]]]
    p1_count += sum(x[0] for x in v.get(p1["name"], [[0]]))
    p1_max += max(x[-1] for x in v.get(p1["name"],  [[0]]))
    p1_result += min(x[-1] for x in v.get(p1["name"], [[0]]))
    p1_total += len(v.get(p1["name"], []))
    p1_sum += sum(x[-1] for x in v.get(p1["name"],  [[0]])) / len(v.get(p1["name"],  [[0]]))
    p1_win += sum(x[-1] for x in v.get(p1["name"],  [[0]]) if x[-1] > 0) 
    p1_lose += sum(x[-1] for x in v.get(p1["name"],  [[0]]) if x[-1] < 0) 

    p2_win += sum(x[-1] for x in v.get(p2["name"],  [[0]]) if x[-1] > 0) 
    p2_lose += sum(x[-1] for x in v.get(p2["name"],  [[0]]) if x[-1] < 0) 

    #p2_scores += [x[-1] for x in v[p2["name"]]]
    #p2_max += max(x[-1] for x in v.get(p2["name"], [[0]]))
    p2_count += sum(x[0] for x in v.get(p2["name"], [[0]]))

    #p2_result += min(x[-1] for x in v.get(p2["name"],  [[0]]))
    p2_total += len(v.get(p2["name"], [0]))
    #p2_sum += sum(x[-1] for x in v.get(p2["name"],  [[0]])) / len(v.get(p2["name"],  [[0]]))

    v["diffrence"] = min(x[-1] for x in v.get(p1["name"],  [[0]])) - min(x[-1] for x in v.get(p2["name"], [[0]]))
    p3_result += v["diffrence"]

  #p1_result = min(p1_scores)
  #p2_result = min(p2_scores)

  #r1 = ((p1_result, p1_total, p1_result/p1_total), (p2_result, p2_total, p2_result/p2_total))
  #r1 = (((p1_result/ p1_total) /(p2_result / p2_total)))

  from tabulate import tabulate
  print(tabulate([
      [" Name ", p1["name"],   p2["name"]], 
      [" Wins ",str(p1_count), str(p2_count)],
      #[" Avg Min Score ",str((p1_result/ p1_total)), str((p2_result/ p2_total))],
      #[" Avg Max Score ",str((p1_max/ p1_total)), str((p2_max/ p2_total))],
      [" Avg Sum Score ",str((p1_win / abs(p1_lose))), str((p2_win / abs(p2_lose)))],

      [" Total Games ", str(p1_total),  str(p2_total)],

    ], headers=['', '', '']))
  if return_obj:
    return [
      [" Name ", p1["name"],   p2["name"]], 
      [" Wins ",str(p1_count), str(p2_count)],
      [" Avg Min Score ",str((p1_result/ p1_total)), str((p2_result/ p2_total))],
      [" Avg Max Score ",str((p1_max/ p1_total)), str((p2_max/ p2_total))],
      [" Avg Sum Score ",str((p1_win / abs(p1_lose))), str((p2_win / abs(p2_lose)))],
      [" Total Games ", str(p1_total),  str(p2_total)],
      ]

  #print("Avg Score Ratio:"+ str((100*abs(p2_result/ p2_total)) / abs(p1_result/ p1_total)))
  #print("Average Delta: "+ str(p3_result / p1_total))
  #print("% of Total Points:"+ p1_total / (p1_total + p2_total)))
  #print(p1["name"] + " has "+ str(r1[0][-1] / r1[1][-2]) +"\% score")


#p = versus(get_profile("Shatoo Mohamad"), get_profile("Mary Closs"))

def test(profile):
  for year in years: 
    profile = played_matches(profile, year)
    time.sleep(0.2)
  
  nms = []
  matches = profile["matches"]
  for match in matches:
    nms.append((match["name"], match["stats"]["win"]))

  correct = 0
  incorrect = 0
  for name in nms:
    obj = versus(profile, get_profile(name[0]), p1c=True, return_obj=True)
    if obj[4][1] > obj[4][2]:
      if name[1] == 1:
        correct += 1
      else:
        incorrect += 1
    else:
      if name[1] == -1:
        correct += 1
      else:
        incorrect += 1
    print(correct, incorrect)
test(get_profile("Barrere Gregoire"))
#print(versus(get_profile("Barrere Gregoire"), get_profile("Tiafoe F.lo")))
#card["matches"] = (n for n in card["matches"])
#for match in card["matches"]:

'''if match["stats"]["win"] == 1:
    match["card"] = played_matches(get_profile(match["name"]), 2020)
    
    probability = 100*((match["stats"]["win_points"]-match["stats"]["loss_points"]) / (match['stats']["win_points"]))

    divzero = (match["card"]["courts"]["Total"]["Wins"] + match["card"]["courts"]["Total"]["Loss"])
    # print(divzero)
    #print(match["card"]["courts"])
    if divzero > 0: 
      #rank_v_match_count = int(100 * (match["card"]["Current Rank"] / (match["card"]["courts"]["Total"]["Wins"] + match["card"]["courts"]["Total"]["Loss"])))
      experience_diffrence = (card["courts"]["Total"]["Wins"]) - (match["card"]["courts"]["Total"]["Wins"])
      rank_diffrence = (match["card"]["Current Rank"] - card["Current Rank"])
      #rank_diffrence = card["courts"]["Total"]["Wins"] / rank_diffrence
      #pvr = probability * rank_diffrence
      #print(match["card"]["name"], match["score"])
      print(card["Current Rank"], match["card"]["name"], match["card"]["Current Rank"], experience_diffrence, rank_diffrence, probability)
  '''
def ranked_wins(card):
  opp_cards = []
  for match in card["matches"]:
    opp_cards.append(played_matches(get_profile(match["name"]), 2020))

  for ocard in opp_cards:
    pass

#print(pformat(card))