from bs4 import BeautifulSoup
import requests
import json
import feedparser
import datetime as dt
import time
import os, sys, re
import dateutil.parser

#말그대로 rss를 파싱해주는 것
"""def RSS_PARSE() -> list:
  #속보 러시아
  parsed_rss = feedparser.parse('https://news.google.com/rss/search?q=%EB%9F%AC%EC%8B%9C%EC%95%84%20%EC%9A%B0%ED%81%AC%EB%9D%BC%EC%9D%B4%EB%82%98%20%22%EC%86%8D%EB%B3%B4%22%20when%3A1h&hl=ko&gl=KR&ceid=KR%3Ako')
  rss = parsed_rss.entries
  return rss"""

#말그대로 rss를 파싱해주는 것
#네이버 뉴스
def RSS_PARSE() -> list:
  res = requests.get("https://search.naver.com/search.naver?where=news&query=%EC%9A%B0%ED%81%AC%EB%9D%BC%EC%9D%B4%EB%82%98%20%EB%9F%AC%EC%8B%9C%EC%95%84%20%EC%86%8D%EB%B3%B4&sm=tab_opt&sort=0&photo=0&field=0&pd=7&ds=&de=&docid=&related=0&mynews=0&office_type=0&office_section_code=0&news_office_checked=&nso=so%3Ar%2Cp%3Aall&is_sug_officeid=0")
  soup = BeautifulSoup(res.content)
  news_cores = soup.find_all(lambda x: x.name == "a" and x.attrs.get("title", False))
  news_cores_list = []
  for news in news_cores:
      pubtime = news.parent.find("span", attrs={'class':'info'}).get_text().strip('분 전').strip()
      news_cores_list.append(
          {
          'title': news.attrs['title'],
          'summary': news.parent.find("div", attrs={'class':'news_dsc'}).get_text().strip(),
          'link': news.attrs['href'],
          'published': dt.datetime.strftime(dt.datetime.now()-dt.timedelta(minutes=int(pubtime)), "%Y/%m/%d, %H:%M:%S")
          }
      )
  return news_cores_list

#content를 받고 정리해서 돌려줌
def RSS_CONTENT(rss): 
  title = rss['title']
  description = rss['summary']
  link = rss['link']
  published = rss['published']#str(dt.datetime.strptime(rss['published'], '%a, %d %b %Y %H:%M:%S %Z')) #+ dt.timedelta(hours=9))
  print(published)
  #date = ':'.join(published.split(":")[:-1])
  #kor_date=dt.datetime.strptime(date,"%Y-%m-%d %H:%M")-dt.timedelta(hours=9)#디스코드가 GMT를 사용해서 그만큼 빼줘야 함.
  #kor_date = time.time()
  #kor_date=str(kor_date)`~

  return title, description, link, published


#공지형식의 임베드 구조 만들고 포스트 하기
def POST_rss(rss, webhook_url):
  title, description, link, date = RSS_CONTENT(rss)
  data = {
    "content":"",
    "embeds" : [
      {
        "title" : title,
        #"description" : description,
        "url" : link, 
        "color" : "598634",
        "description": description,
        "footer": {
          "text": date
          }
      }
    ]
  }

  #post request
  print(data)
  requests.post(
    webhook_url,
    data=json.dumps(data),
    headers={'Content-Type' : 'application/json'})

#rsss는 rss들(복수 s)라는 뜻이다.

#언론사가 다르고 시간이 가장 짧은 뉴스 하나를 내보낸다는 룰을 고려해보자

#시간을 입력하면 현재와의 차를 구하는 함수
def now_minus_strtime(strtime) -> float:
  try:
    dt_time = dateutil.parser.parse(strtime)
  except:
    print('error occured: 시간 유틸 예외 잡기 오류 in 86 lines')
    return 100000 #시간 넘겨버려서 출력 못하게 하기
    pass
  #구글 뉴스일때의 코드임
    #dt_time = dt.datetime.strptime(strtime, '%a, %d %b %Y %H:%M:%S %Z') #%H: 24hours 
  dt_now = dt.datetime.utcnow() + dt.timedelta(hours=9) #gmt랑 소숫점 초 차이밖에 나지 않기 때문에 굳이 GMT로 변환하여 사용하지 않는다. +9시간 차
  return time.mktime(dt_now.timetuple()) - time.mktime(dt_time.timetuple()) #unix time의 차로 돌려준다.

#언론사 published date 리턴
def get_site_pubDate(url=str(), headers={})-> str:
    res = requests.get(
        url= url,
        headers=headers)
    soup = BeautifulSoup(res.content, "html.parser")
    pubDate = soup.find(lambda x: x.name=="meta" and "published_time" in x.attrs.get('property',''))
    if bool(pubDate):
      return pubDate.attrs.get('content', 0)
    else:
      return "False"


def main():
  recent_path = "./recent.json"
  
  rsss = RSS_PARSE()
  beforelen = len(rsss)
  print("before rsss length:", beforelen) 
  
  if os.path.isfile(recent_path):
    recent = open(recent_path, "r", encoding="utf-8").readlines()
    try: recent = json.loads("\n".join(recent))
    except Exception as e: return print(f"JSON Loading Error:\n{e}")
    print("recent title:", recent["title"])
    #링크가 같으면 rsss 업데이트 후 break
    for i, rss in enumerate(rsss): 
      #직접 사이트 들어가서 메타데이터에서 작성시간 긁어오기
      rss_timegap = get_site_pubDate(rss["link"])
      if rss_timegap == "False":
        rss_timegap = now_minus_strtime(rss["published"])
      else:
        rss_timegap = now_minus_strtime(rss_timegap)
      
      #print("datetime(+9h):",str(dt.datetime.strptime(rss.published, '%a, %d %b %Y %H:%M:%S %Z') + dt.timedelta(hours=9)))
      #source: 신문방송사를 의미
      #and recent["source"] != rss["source"]
      if recent["link"] != rss["link"] \
          and rss_timegap <= 2400: #unix시간은 초를 단위로 1식 올라가기 때문에 3600은 1시간을 의미한다. 2400은 40분.
        print("now_minus_strtime:",now_minus_strtime(rss['published']))
        print("rss_timegap:",rss_timegap)
        rsss = (rsss[i],)
        break
  else:
    rsss = (rsss[0],)
  
  
  #확인용 출력
  print("after rsss length:", len(rsss))
  #정상적으로 필터링이 된 경우
  if len(rsss) > 0 and len(rsss) < beforelen:
    #확인용 출력
    print("rsss[0]['title']:", rsss[0]['title'])
    print("rsss[0]['link']:", rsss[0]['link'])
    print("rsss[0]['summary']:", rsss[0]['summary'])
    
    #웹후크 주소로 보내기  
    for webhook_url in sys.argv[1:]:
      #print("toto")
      for rss in rsss:
        print("gogo")
        POST_rss(rss, webhook_url)

  elif len(rsss) == 0:
    print("There is nothing to send.")
  
  #정상적으로 필터링이 안된경우
  elif beforelen <= len(rsss): 
    print("Error but pass over: recent.json과 동일한 내용의 rss가 포착되지 않았습니다. ")
    rsss = tuple()
    #rsss = (beforersss[0],)
  
  else:
    print("Unknown Error")
    return #프로그램 종료

  #rsss가 비어있지 않아야만 파일을 새로 씀.
  if len(rsss) > 0:
    with open(recent_path, "w", encoding="utf-8") as w:
      w.write(json.dumps(rsss[-1]))
      w.close()
  else:
    print("Nothing was written.")
    

if __name__ == '__main__':
    main()
