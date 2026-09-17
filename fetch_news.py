#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin
import hashlib,json,re,sys
import requests,feedparser
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent
CFG=json.loads((ROOT/"sources.json").read_text(encoding="utf-8"))
OUT=ROOT/"frontend/data/articles.json"
LOG=ROOT/"feed_report.json"
HEAD={"User-Agent":"DailyNewsDashboard/1.0 (personal RSS reader)"}
PAYWALL=["subscribe to continue","subscribe to read","sign in to continue","already a subscriber",
         "premium article","subscription required","unlock this article","you've reached your limit",
         "you have reached your limit","become a subscriber"]
LONG=["investigation","investigative","in-depth","long read","longform","special report","deep dive","explainer"]

def txt(s): return BeautifulSoup(s or "","html.parser").get_text(" ",strip=True)
def dateof(e):
    for k in ("published_parsed","updated_parsed","created_parsed"):
        v=getattr(e,k,None)
        if v: return datetime(*v[:6],tzinfo=timezone.utc)
    return datetime.now(timezone.utc)
def sha(u): return hashlib.sha1(u.encode()).hexdigest()[:18]

def discover(site):
    try:
        r=requests.get(site,headers=HEAD,timeout=12); r.raise_for_status()
        soup=BeautifulSoup(r.text,"html.parser")
        for link in soup.find_all("link"):
            typ=(link.get("type") or "").lower()
            href=link.get("href")
            if href and ("rss" in typ or "atom" in typ):
                return urljoin(site,href)
    except Exception: pass
    return ""

def classify(title,desc,rules):
    text=(title+" "+desc).lower()
    return [topic for topic,words in rules.items()
            if any(re.search(r"\b"+re.escape(w.lower())+r"\b",text) for w in words)]

def main():
    articles=[]; report=[]
    cutoff=datetime.now(timezone.utc)-timedelta(days=8)
    for src in CFG["sources"]:
        if not src.get("enabled"): continue
        rss=src.get("rss") or discover(src["website"])
        if not rss:
            report.append({"source":src["name"],"status":"no RSS found"}); continue
        try:
            f=feedparser.parse(rss)
            if getattr(f,"bozo",False) and not f.entries:
                raise RuntimeError("invalid/empty feed")
            count=0
            for e in f.entries[:src.get("max_items",25)]:
                url=e.get("link","").strip(); title=txt(e.get("title",""))
                desc=txt(e.get("summary",e.get("description","")))
                if not url or not title: continue
                published=dateof(e)
                if published < cutoff: continue
                hay=(title+" "+desc+" "+url).lower()
                if any(x in hay for x in PAYWALL): continue
                topics=classify(title,desc,CFG["topic_keywords"])
                deep=any(x in hay for x in LONG) or len(desc)>500
                articles.append({"id":sha(url),"title":title,"description":desc[:600],
                  "url":url,"published":published.isoformat(),"source":src["name"],
                  "topics":topics,"deep_dive":deep})
                count+=1
            report.append({"source":src["name"],"status":"ok","rss":rss,"items":count})
        except Exception as ex:
            report.append({"source":src["name"],"status":"error","rss":rss,"error":str(ex)})
    unique={a["id"]:a for a in articles}
    data=sorted(unique.values(),key=lambda a:a["published"],reverse=True)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf8")
    LOG.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
    print(f"{len(data)} articles written; {len(report)} sources checked.")
if __name__=="__main__": main()
